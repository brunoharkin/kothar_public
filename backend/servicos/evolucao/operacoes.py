"""Harness durável e isolada. O chamador confirma a transação da sessão.

Claims de ações devem ser COMMITADOS antes de chamar um provedor externo. O helper
execute_action faz isso e grava resultados incertos sem repetir o efeito.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import time
import uuid
from collections.abc import Callable, Mapping
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .modelos import (
    ActionInput,
    ApprovalInput,
    BudgetLimitInput,
    BudgetUsageInput,
    EvolutionError,
    FactInput,
    FeedbackInput,
    ProspectInput,
    StrictInput,
    TaskInput,
)
from .repositorio import EvolutionRepository

METRICS = ("tokens", "calls", "cost_microunits")
GENERIC_KINDS = frozenset({"feedback", "prospect", "profile", "feedback_proposal", "evaluation", "selection", "skill_receipt", "business"})


def _now() -> int:
    return int(time.time())


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _validated(model: type[StrictInput], value: Any) -> StrictInput:
    return model.model_validate(value.model_dump() if isinstance(value, model) else value)


def _key(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 160:
        raise EvolutionError("invalid_key")
    return hashlib.sha256(value.encode()).hexdigest()


class EvolutionService:
    def __init__(self, db: AsyncSession, owner: str, project: str):
        # SQLite is an explicit isolated test fixture, never a runtime fallback.
        dialect = db.get_bind().dialect.name
        if dialect != "postgresql" and not (dialect == "sqlite" and db.info.get("evolution_test_database") is True):
            raise EvolutionError("postgresql_required")
        self.db = db
        self.repo = EvolutionRepository(db, owner, project)
        self.owner, self.project = owner, project

    async def _required(self, kind: str, item_id: str, *, lock: bool = False) -> dict:
        row = await self.repo.get(kind, item_id, lock=lock)
        if row is None:
            raise EvolutionError("not_found")
        return row

    async def add_fact(self, value: FactInput | dict) -> dict:
        item = _validated(FactInput, value).model_dump()
        if item["observed_at"] > _now() + 300 or (item["expires_at"] is not None and item["expires_at"] <= item["observed_at"]):
            raise EvolutionError("invalid_fact_dates")
        item.update(status="active", created_at=_now(), supersedes=None)
        return (await self.repo.create("fact", str(uuid.uuid4()), item))[0]

    async def list_facts(self, limit: int = 100, include_inactive: bool = False) -> list[dict]:
        rows = await self.repo.list("fact", limit)
        if include_inactive:
            return rows
        return [row for row in rows if row["status"] == "active" and (row["expires_at"] is None or row["expires_at"] > _now())]

    async def correct_fact(self, fact_id: str, value: FactInput | dict, expected_revision: int) -> dict:
        async with self.db.begin_nested():
            original = await self._required("fact", fact_id, lock=True)
            if original["revision"] != expected_revision or original["status"] != "active":
                raise EvolutionError("stale_revision")
            corrected = await self.add_fact(value)
            payload = self.repo.payload(corrected)
            payload["supersedes"] = fact_id
            corrected = await self.repo.replace("fact", corrected, payload)
            payload = self.repo.payload(original)
            payload.update(status="superseded", superseded_by=corrected["id"])
            await self.repo.replace("fact", original, payload)
            return corrected

    async def revoke_fact(self, fact_id: str, expected_revision: int) -> dict:
        row = await self._required("fact", fact_id, lock=True)
        if row["revision"] != expected_revision:
            raise EvolutionError("stale_revision")
        payload = self.repo.payload(row)
        # Retain provenance and a tombstone, remove content on revocation.
        payload.update(content="", status="revoked", revoked_at=_now())
        return await self.repo.replace("fact", row, payload)

    async def create_task(self, value: TaskInput | dict) -> dict:
        data = _validated(TaskInput, value).model_dump()
        request_hash = _hash(data)
        async with self.db.begin_nested():
            for dependency in data["dependencies"]:
                await self._required("task", dependency)
            data.update(status="blocked" if data["dependencies"] else "queued", request_hash=request_hash,
                        created_at=_now(), attempts=0, fence=0, lease_until=0, checkpoint={}, next_attempt_at=0)
            row, created = await self.repo.create("task", _key(data["dedupe_key"]), data)
            if not created and row["request_hash"] != request_hash:
                raise EvolutionError("dedupe_conflict")
            return row

    async def get_task(self, task_id: str) -> dict:
        return await self._required("task", task_id)

    async def list_tasks(self, limit: int = 100) -> list[dict]:
        rows = await self.repo.list("task", limit)
        categories = {"repair": 0, "resume": 1, "new": 2}
        return sorted(rows, key=lambda r: (r["status"] != "blocked", categories[r["category"]], -r["priority"], r["created_at"], r["id"]))

    async def claim_task(self, task_id: str | None = None, lease_seconds: int = 120) -> dict | None:
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
            raise EvolutionError("invalid_lease")

        async def candidates():
            if task_id is not None:
                yield await self._required("task", task_id)
            else:
                async for candidate in self.repo.task_candidates(_now()):
                    yield candidate

        async for row in candidates():
            payload = self.repo.payload(row)
            status = payload["status"]
            if status == "running" and payload["lease_until"] <= _now():
                # A task must explicitly declare its effects safe to retry.
                if not payload["retry_safe"]:
                    payload.update(status="uncertain", lease_until=0)
                    await self.repo.replace("task", row, payload)
                    continue
                status = "retry_wait"
            if status == "blocked":
                dependencies = [await self._required("task", item) for item in payload["dependencies"]]
                if not all(item["status"] == "completed" for item in dependencies):
                    continue
                status = "queued"
            if status not in {"queued", "retry_wait"} or payload["next_attempt_at"] > _now():
                continue
            if payload["attempts"] >= payload["max_attempts"]:
                payload.update(status="failed", lease_until=0)
                await self.repo.replace("task", row, payload)
                continue
            payload.update(status="running", attempts=payload["attempts"] + 1,
                           fence=payload["fence"] + 1, lease_until=_now() + lease_seconds)
            try:
                async with self.db.begin_nested():
                    return await self.repo.replace("task", row, payload)
            except EvolutionError as exc:
                if exc.code != "concurrent_change":
                    raise
        return None

    @staticmethod
    def _lease(row: dict, fence: int):
        if type(fence) is not int or row["status"] not in {"running", "executing"} or row["fence"] != fence or row["lease_until"] <= _now():
            raise EvolutionError("stale_lease")

    async def checkpoint_task(self, task_id: str, fence: int, checkpoint: dict) -> dict:
        validated = TaskInput(title="checkpoint", dedupe_key="checkpoint", payload=checkpoint)
        row = await self._required("task", task_id, lock=True)
        self._lease(row, fence)
        payload = self.repo.payload(row)
        payload["checkpoint"] = validated.payload
        return await self.repo.replace("task", row, payload)

    async def finish_task(self, task_id: str, fence: int, *, success: bool, transient: bool = False, result: dict | None = None) -> dict:
        result = TaskInput(title="result", dedupe_key="result", payload=result or {}).payload
        row = await self._required("task", task_id, lock=True)
        self._lease(row, fence)
        payload = self.repo.payload(row)
        retry = not success and transient and row["retry_safe"] and row["attempts"] < row["max_attempts"]
        payload.update(status="completed" if success else ("retry_wait" if retry else "failed"), lease_until=0, result=result)
        if retry:
            # Deterministic bounded jitter avoids synchronized retries and is replayable.
            jitter = int(row["id"][:4], 16) % 4
            payload["next_attempt_at"] = _now() + min(300, 2 ** row["attempts"] + jitter)
        return await self.repo.replace("task", row, payload)

    async def set_budget(self, budget_id: str, value: BudgetLimitInput | dict) -> dict:
        limits = _validated(BudgetLimitInput, value).model_dump()
        async with self.db.begin_nested():
            row = await self.repo.get("budget", _key(budget_id), lock=True)
            if row is None:
                row, created = await self.repo.create("budget", _key(budget_id), {"name": budget_id, "limits": limits, "spent": dict.fromkeys(METRICS, 0), "reserved": dict.fromkeys(METRICS, 0)})
                if created:
                    return row
                row = await self._required("budget", row["id"], lock=True)
            if any(limits[key] < row["spent"][key] + row["reserved"][key] for key in METRICS):
                raise EvolutionError("budget_below_committed_usage")
            payload = self.repo.payload(row)
            payload["limits"] = limits
            return await self.repo.replace("budget", row, payload)

    async def get_budget(self, budget_id: str = "default") -> dict:
        return await self._required("budget", _key(budget_id))

    async def reserve_budget(self, reservation_key: str, estimated: BudgetUsageInput | dict, budget_id: str = "default") -> dict:
        usage = _validated(BudgetUsageInput, estimated).model_dump()
        item_id = _key(reservation_key)
        async with self.db.begin_nested():
            budget = await self._required("budget", _key(budget_id), lock=True)
            existing = await self.repo.get("reservation", item_id, lock=True)
            if existing:
                if existing["budget_id"] != budget["id"] or existing["estimated"] != usage:
                    raise EvolutionError("dedupe_conflict")
                return existing
            if any(budget["spent"][key] + budget["reserved"][key] + usage[key] > budget["limits"][key] for key in METRICS):
                raise EvolutionError("budget_exceeded")
            reservation, created = await self.repo.create("reservation", item_id, {"budget_id": budget["id"], "estimated": usage, "state": "reserved", "actual": None, "created_at": _now()})
            if not created:
                raise EvolutionError("concurrent_change")
            payload = self.repo.payload(budget)
            for key in METRICS:
                payload["reserved"][key] += usage[key]
            await self.repo.replace("budget", budget, payload)
            return reservation

    async def settle_budget(self, reservation_key: str, actual: BudgetUsageInput | dict) -> dict:
        usage = _validated(BudgetUsageInput, actual).model_dump()
        return await self._close_reservation(reservation_key, usage)

    async def release_budget(self, reservation_key: str) -> dict:
        return await self._close_reservation(reservation_key, None)

    async def _close_reservation(self, reservation_key: str, usage: dict | None) -> dict:
        async with self.db.begin_nested():
            reservation = await self._required("reservation", _key(reservation_key))
            # Consistent lock order: budget first, then reservation (same as reserve).
            budget = await self._required("budget", reservation["budget_id"], lock=True)
            reservation = await self._required("reservation", reservation["id"], lock=True)
            target_state = "released" if usage is None else "settled"
            if reservation["state"] != "reserved":
                if reservation["state"] == target_state and reservation["actual"] == usage:
                    return reservation
                raise EvolutionError("reservation_closed")
            payload = self.repo.payload(budget)
            for key in METRICS:
                payload["reserved"][key] -= reservation["estimated"][key]
                payload["spent"][key] += usage[key] if usage else 0
            payload["overrun"] = any(payload["spent"][key] + payload["reserved"][key] > payload["limits"][key] for key in METRICS)
            await self.repo.replace("budget", budget, payload)
            payload = self.repo.payload(reservation)
            payload.update(state=target_state, actual=usage, closed_at=_now(), overrun=usage is not None and any(usage[key] > reservation["estimated"][key] for key in METRICS))
            return await self.repo.replace("reservation", reservation, payload)

    async def prepare_action(self, value: ActionInput | dict) -> dict:
        data = _validated(ActionInput, value).model_dump()
        if not _now() < data["expires_at"] <= _now() + 30 * 86400:
            raise EvolutionError("invalid_action_expiry")
        payload_hash = _hash({"tool": data["tool"], "scope": data["scope"], "payload": data["payload"], "review": data["review"]})
        data.update(payload_hash=payload_hash, status="prepared", created_at=_now(), fence=0, lease_until=0, approval=None)
        row, created = await self.repo.create("action", _key(data["dedupe_key"]), data)
        if not created and (row["payload_hash"] != payload_hash or row["expires_at"] != data["expires_at"]):
            raise EvolutionError("dedupe_conflict")
        return row

    async def get_action(self, action_id: str) -> dict:
        return await self._required("action", action_id)

    async def list_actions(self, limit: int = 100) -> list[dict]:
        return await self.repo.list("action", limit)

    async def approve_action(self, action_id: str, value: ApprovalInput | dict) -> dict:
        approval = _validated(ApprovalInput, value).model_dump()
        if approval["decision"] == "reject":
            return await self.reject_action(action_id, approval)
        row = await self._required("action", action_id, lock=True)
        if row["status"] not in {"prepared", "approved"}:
            raise EvolutionError("invalid_action_state")
        if approval["payload_hash"] != row["payload_hash"] or approval["scope"] != row["scope"]:
            raise EvolutionError("approval_scope_mismatch")
        if not _now() < approval["expires_at"] <= row["expires_at"]:
            raise EvolutionError("invalid_approval_expiry")
        if row["status"] == "approved" and row["approval"] and row["approval"]["expires_at"] > _now():
            return row
        payload = self.repo.payload(row)
        approval.update(approved_by=self.owner, approved_at=_now())
        payload.update(status="approved", approval=approval)
        return await self.repo.replace("action", row, payload)

    async def reject_action(self, action_id: str, value: ApprovalInput | dict | None = None) -> dict:
        row = await self._required("action", action_id, lock=True)
        if row["status"] not in {"prepared", "approved"}:
            raise EvolutionError("invalid_action_state")
        if value is not None:
            approval = _validated(ApprovalInput, value).model_dump()
            if approval["payload_hash"] != row["payload_hash"] or approval["scope"] != row["scope"]:
                raise EvolutionError("approval_scope_mismatch")
        payload = self.repo.payload(row)
        payload.update(status="rejected", approval=None, rejected_by=self.owner, rejected_at=_now())
        return await self.repo.replace("action", row, payload)

    async def claim_action(self, action_id: str, allowed_tools: set[str] | frozenset[str], lease_seconds: int = 120) -> dict:
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
            raise EvolutionError("invalid_lease")
        row = await self._required("action", action_id, lock=True)
        payload = self.repo.payload(row)
        if row["status"] == "executing" and row["lease_until"] <= _now():
            payload.update(status="uncertain", lease_until=0)
            return await self.repo.replace("action", row, payload)
        if row["status"] != "approved":
            raise EvolutionError("invalid_action_state")
        approval = row["approval"]
        if row["tool"] not in allowed_tools:
            raise EvolutionError("tool_not_allowed")
        if not approval or approval["expires_at"] <= _now() or row["expires_at"] <= _now():
            raise EvolutionError("approval_expired")
        if approval["payload_hash"] != row["payload_hash"] or approval["scope"] != row["scope"]:
            raise EvolutionError("approval_scope_mismatch")
        expected = _hash({"tool": row["tool"], "scope": row["scope"], "payload": row["payload"], "review": row["review"]})
        if expected != row["payload_hash"]:
            raise EvolutionError("action_integrity_failure")
        payload.update(status="executing", fence=row["fence"] + 1, lease_until=_now() + lease_seconds)
        return await self.repo.replace("action", row, payload)

    async def finish_action(self, action_id: str, fence: int, *, outcome: str, receipt: str | None = None) -> dict:
        if outcome not in {"succeeded", "failed", "uncertain"} or (receipt is not None and len(receipt) > 300):
            raise EvolutionError("invalid_action_result")
        row = await self._required("action", action_id, lock=True)
        self._lease(row, fence)
        payload = self.repo.payload(row)
        payload.update(status=outcome, lease_until=0, receipt=receipt, finished_at=_now())
        return await self.repo.replace("action", row, payload)

    async def execute_action(self, action_id: str, callbacks: Mapping[str, Callable], lease_seconds: int = 120) -> dict:
        """Use dedicated session. Callback must implement its own provider timeout.

        Callbacks receive immutable snapshot + stable idempotency key. They return
        a receipt string, never credentials. Any exception is an uncertain effect.
        """
        claimed = await self.claim_action(action_id, frozenset(callbacks), lease_seconds)
        await self.db.commit()  # Durable before effect; crash cannot reset to approved.
        if claimed["status"] == "uncertain":
            return claimed
        try:
            provider_key = _hash({"owner": self.owner, "project": self.project, "action_id": claimed["id"]})
            result = callbacks[claimed["tool"]](claimed["payload"], idempotency_key=provider_key)
            if inspect.isawaitable(result):
                result = await result
            if result is not None and (not isinstance(result, str) or len(result) > 300):
                raise EvolutionError("invalid_callback_receipt")
            outcome, receipt = "succeeded", result
        except Exception:
            outcome, receipt = "uncertain", None
        # An expired lease is also uncertain; never replay to recover the result.
        row = await self._required("action", action_id, lock=True)
        if row["status"] == "uncertain" and row["fence"] == claimed["fence"]:
            finished = row
        elif row["status"] == "executing" and row["fence"] == claimed["fence"] and row["lease_until"] <= _now():
            payload = self.repo.payload(row)
            payload.update(status="uncertain", lease_until=0, finished_at=_now())
            finished = await self.repo.replace("action", row, payload)
        else:
            finished = await self.finish_action(action_id, claimed["fence"], outcome=outcome, receipt=receipt)
        await self.db.commit()
        return finished

    async def add_feedback(self, value: FeedbackInput | dict) -> dict:
        data = _validated(FeedbackInput, value).model_dump()
        if data["task_id"]:
            await self._required("task", data["task_id"])
        data.update(status="proposed", created_at=_now(), approved_by=None, applied=False)
        return (await self.repo.create("feedback", str(uuid.uuid4()), data))[0]

    async def list_feedback(self, limit: int = 100) -> list[dict]:
        return await self.repo.list("feedback", limit)

    async def add_prospect(self, value: ProspectInput | dict) -> dict:
        data = _validated(ProspectInput, value).model_dump()
        if data["contact_verified"] and not data["contact"]:
            raise EvolutionError("contact_required")
        if data["observed_at"] > _now() + 300:
            raise EvolutionError("invalid_observation_date")
        data.update(status="research", created_at=_now())
        return (await self.repo.create("prospect", _key(data["domain"].lower()), data))[0]

    async def get_prospect(self, prospect_id: str) -> dict:
        return await self._required("prospect", prospect_id)

    async def list_prospects(self, limit: int = 100) -> list[dict]:
        return await self.repo.list("prospect", limit)

    @staticmethod
    def _generic_kind(kind: str):
        if kind not in GENERIC_KINDS:
            raise EvolutionError("record_kind_not_allowed")

    async def get_record(self, kind: str, item_id: str) -> dict:
        self._generic_kind(kind)
        return await self._required(kind, item_id)

    async def list_records(self, kind: str, limit: int = 100) -> list[dict]:
        self._generic_kind(kind)
        return await self.repo.list(kind, limit)

    async def put_record(self, kind: str, item_id: str, payload: dict, expected_revision: int | None = None) -> dict:
        """Internal adapter for versioned derived results. Never expose as raw API."""
        self._generic_kind(kind)
        data = TaskInput(title="record", dedupe_key="record", payload=payload).payload
        if any(key in data for key in {"id", "revision", "owner", "project"}):
            raise EvolutionError("reserved_record_fields")
        if not isinstance(item_id, str) or not 1 <= len(item_id) <= 100:
            raise EvolutionError("invalid_key")
        row = await self.repo.get(kind, item_id, lock=True)
        if row:
            if expected_revision is None or expected_revision != row["revision"]:
                raise EvolutionError("stale_revision")
            return await self.repo.replace(kind, row, data)
        if expected_revision is not None:
            raise EvolutionError("stale_revision")
        created, is_new = await self.repo.create(kind, item_id, data)
        if not is_new:
            raise EvolutionError("concurrent_change")
        return created

    async def consume_rate_limit(self, bucket: str, limit: int, window_seconds: int) -> bool:
        """Fixed window in the authoritative DB, safe across processes.

        A conflicting CAS denies rather than allowing an unaccounted request.
        Identity must come from the caller's authenticated server context.
        """
        if type(limit) is not int or not 1 <= limit <= 100000 or type(window_seconds) is not int or not 1 <= window_seconds <= 86400:
            raise EvolutionError("invalid_rate_limit")
        window = _now() // window_seconds
        item_id = _key(bucket)
        try:
            async with self.db.begin_nested():
                row = await self.repo.get("rate_limit", item_id, lock=True)
                if row is None:
                    row, created = await self.repo.create("rate_limit", item_id, {"window": window, "count": 1, "limit": limit, "window_seconds": window_seconds})
                    if created:
                        return True
                    row = await self._required("rate_limit", item_id, lock=True)
                if row["limit"] != limit or row["window_seconds"] != window_seconds:
                    raise EvolutionError("rate_limit_configuration_changed")
                count = row["count"] if row["window"] == window else 0
                if count >= limit:
                    return False
                payload = self.repo.payload(row)
                payload.update(window=window, count=count + 1)
                await self.repo.replace("rate_limit", row, payload)
                return True
        except EvolutionError as exc:
            if exc.code == "concurrent_change":
                return False
            raise
