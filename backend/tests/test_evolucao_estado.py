"""Verificação comportamental do estado durável em banco isolado real."""

import asyncio
import time

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.servicos.evolucao.modelos import ActionInput, EvolutionError, TaskInput
from backend.servicos.evolucao.operacoes import EvolutionService
from backend.servicos.evolucao.repositorio import metadata


@pytest_asyncio.fixture
async def evolution_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'durable.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, info={"evolution_test_database": True})
    try:
        yield factory
    finally:
        await engine.dispose()


def fact(**changes):
    return {"content": "Decisão de arquitetura", "source": "cofre://projeto/adr-1", "observed_at": int(time.time()) - 1, "confidence": 0.9, **changes}


def action(**changes):
    return {"tool": "test.deliver", "scope": "reviewed-scope", "payload": {"document_id": "demo"}, "dedupe_key": "deliver-once", "expires_at": int(time.time()) + 600, "review": "Documento demo aprovado para publicação", **changes}


async def approved(service, **changes):
    prepared = await service.prepare_action(action(**changes))
    return await service.approve_action(prepared["id"], {"payload_hash": prepared["payload_hash"], "scope": prepared["scope"], "expires_at": prepared["expires_at"]})


async def test_reconstruct_session_and_isolate_owner_and_project(evolution_db):
    async with evolution_db() as db:
        saved = await EvolutionService(db, "owner-a", "project-a").add_fact(fact())
        await db.commit()
    async with evolution_db() as db:
        service = EvolutionService(db, "owner-a", "project-a")
        assert (await service.list_facts())[0]["id"] == saved["id"]
        assert await EvolutionService(db, "owner-b", "project-a").list_facts() == []
        assert await EvolutionService(db, "owner-a", "project-b").list_facts() == []
        with pytest.raises(EvolutionError, match="not_found"):
            await EvolutionService(db, "owner-b", "project-a").revoke_fact(saved["id"], 1)


async def test_memory_correction_expiration_revocation_and_cas(evolution_db, monkeypatch):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        first = await service.add_fact(fact())
        second = await service.correct_fact(first["id"], fact(content="Decisão corrigida"), first["revision"])
        assert [row["id"] for row in await service.list_facts()] == [second["id"]]
        assert second["supersedes"] == first["id"]
        with pytest.raises(EvolutionError, match="stale_revision"):
            await service.correct_fact(first["id"], fact(), first["revision"])
        revoked = await service.revoke_fact(second["id"], second["revision"])
        assert revoked["content"] == ""
        assert await service.list_facts() == []
        expiring = await service.add_fact(fact(expires_at=int(time.time()) + 3))
        monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: expiring["expires_at"])
        assert await service.list_facts() == []


async def test_task_dedupe_claim_checkpoint_resume_fencing_and_retry_cap(evolution_db, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: clock[0])
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        value = TaskInput(title="replay safe", dedupe_key="job-1", retry_safe=True, max_attempts=2)
        task = await service.create_task(value)
        assert (await service.create_task(value))["id"] == task["id"]
        with pytest.raises(EvolutionError, match="dedupe_conflict"):
            await service.create_task(TaskInput(title="different", dedupe_key="job-1"))
        claimed = await service.claim_task(task["id"], 2)
        assert claimed["fence"] == 1
        assert await service.claim_task(task["id"]) is None
        await service.checkpoint_task(task["id"], claimed["fence"], {"completed_stage": "research"})
        await db.commit()
    clock[0] += 3
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        resumed = await service.claim_task(task["id"], 2)
        assert resumed["fence"] == 2
        assert resumed["checkpoint"] == {"completed_stage": "research"}
        with pytest.raises(EvolutionError, match="stale_lease"):
            await service.finish_task(task["id"], 1, success=True)
        finished = await service.finish_task(task["id"], 2, success=False, transient=True)
        assert finished["status"] == "failed"
        assert await service.claim_task(task["id"]) is None


async def test_blocked_precedes_new_in_review_but_not_execution(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        first = await service.create_task(TaskInput(title="dependency", dedupe_key="dependency"))
        blocked = await service.create_task(TaskInput(title="blocked", dedupe_key="blocked", dependencies=[first["id"]], priority=100))
        repair = await service.create_task(TaskInput(title="repair", dedupe_key="repair", category="repair", priority=1))
        assert (await service.list_tasks())[0]["id"] == blocked["id"]
        claimed = await service.claim_task()
        assert claimed["id"] == repair["id"]
        assert await service.claim_task(blocked["id"]) is None
        dependency = await service.claim_task(first["id"])
        await service.finish_task(dependency["id"], dependency["fence"], success=True)
        assert (await service.claim_task(blocked["id"]))["status"] == "running"


async def test_unsafe_task_crash_is_uncertain_never_retried(evolution_db, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: clock[0])
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        task = await service.create_task(TaskInput(title="potential effect", dedupe_key="unsafe"))
        await service.claim_task(task["id"], 1)
        clock[0] += 2
        assert await service.claim_task(task["id"]) is None
        assert (await service.get_task(task["id"]))["status"] == "uncertain"


async def test_cas_two_sessions_prevents_stale_write(evolution_db):
    async with evolution_db() as db:
        row = await EvolutionService(db, "owner", "project").put_record("profile", "profile-a", {"content": "initial"})
        await db.commit()
    async with evolution_db() as first, evolution_db() as second:
        one = EvolutionService(first, "owner", "project")
        two = EvolutionService(second, "owner", "project")
        stale = await two.get_record("profile", row["id"])
        await second.commit()
        await one.put_record("profile", row["id"], {"content": "updated"}, row["revision"])
        await first.commit()
        with pytest.raises(EvolutionError, match="concurrent_change"):
            await two.repo.replace("profile", stale, {"content": "stale"})
        await second.rollback()
        assert (await two.get_record("profile", row["id"]))["content"] == "updated"


async def test_action_hash_scoped_approval_reuse_and_allowlist(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        prepared = await service.prepare_action(action())
        with pytest.raises(EvolutionError, match="approval_scope_mismatch"):
            await service.approve_action(prepared["id"], {"payload_hash": prepared["payload_hash"], "scope": "other", "expires_at": prepared["expires_at"]})
        approval = {"payload_hash": prepared["payload_hash"], "scope": prepared["scope"], "expires_at": prepared["expires_at"]}
        accepted = await service.approve_action(prepared["id"], approval)
        assert (await service.approve_action(prepared["id"], approval))["revision"] == accepted["revision"]
        with pytest.raises(EvolutionError, match="tool_not_allowed"):
            await service.claim_action(prepared["id"], {"other.tool"})
        with pytest.raises(EvolutionError, match="dedupe_conflict"):
            await service.prepare_action(action(payload={"document_id": "changed"}))
        claimed = await service.claim_action(prepared["id"], {"test.deliver"})
        assert claimed["status"] == "executing"
        with pytest.raises(EvolutionError, match="invalid_action_state"):
            await service.claim_action(prepared["id"], {"test.deliver"})


async def test_external_callback_claim_committed_and_timeout_not_repeated(evolution_db):
    effects = []
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        item = await approved(service)
        await db.commit()

        async def effect(payload, idempotency_key):
            async with evolution_db() as other:
                observed = await EvolutionService(other, "owner", "project").get_action(item["id"])
                assert observed["status"] == "executing"
            effects.append(idempotency_key)
            raise TimeoutError("provider may have sent")

        result = await service.execute_action(item["id"], {"test.deliver": effect})
        assert result["status"] == "uncertain"
        with pytest.raises(EvolutionError, match="invalid_action_state"):
            await service.execute_action(item["id"], {"test.deliver": effect})
        assert len(effects) == 1 and len(effects[0]) == 64


async def test_external_effect_finishes_successfully_with_receipt(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        item = await approved(service)
        result = await service.execute_action(item["id"], {"test.deliver": lambda payload, idempotency_key: "provider-receipt"})
        assert result["status"] == "succeeded"
        assert result["receipt"] == "provider-receipt"


async def test_invalid_provider_receipt_persists_uncertain_without_replay(evolution_db):
    effects = []
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        item = await approved(service)

        def effect(payload, idempotency_key):
            effects.append(idempotency_key)
            return "x" * 301

        result = await service.execute_action(item["id"], {"test.deliver": effect})
        assert result["status"] == "uncertain" and result["receipt"] is None
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        assert (await service.get_action(item["id"]))["status"] == "uncertain"
        with pytest.raises(EvolutionError, match="invalid_action_state"):
            await service.execute_action(item["id"], {"test.deliver": effect})
    assert len(effects) == 1 and len(effects[0]) == 64


async def test_provider_idempotency_key_is_stable_and_scoped_to_owner_project(evolution_db):
    received = []
    ids = []

    def effect(payload, idempotency_key):
        received.append(idempotency_key)
        return "provider-receipt"

    for owner, project in (("owner-a", "project-a"), ("owner-a", "project-b"), ("owner-b", "project-a")):
        async with evolution_db() as db:
            service = EvolutionService(db, owner, project)
            item = await approved(service)
            ids.append(item["id"])
            await service.execute_action(item["id"], {"test.deliver": effect})
    assert len(set(ids)) == 1  # Same local dedupe key; DB identity includes owner/project.
    assert len(set(received)) == 3


async def test_callback_preserves_expired_lease_reconciled_by_other_worker(evolution_db, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: clock[0])
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        item = await approved(service)

        async def effect(payload, idempotency_key):
            clock[0] += 2
            async with evolution_db() as other:
                recovered = await EvolutionService(other, "owner", "project").claim_action(item["id"], {"test.deliver"})
                assert recovered["status"] == "uncertain"
                await other.commit()
            return "provider-receipt"

        result = await service.execute_action(item["id"], {"test.deliver": effect}, lease_seconds=1)
        assert result["status"] == "uncertain"


async def test_old_queued_task_is_not_hidden_by_terminal_history(evolution_db):
    from sqlalchemy import insert

    from backend.servicos.evolucao.repositorio import records

    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        task = await service.create_task(TaskInput(title="old pending work", dedupe_key="old-pending"))
        payload = service.repo.payload(task)
        payload["status"] = "completed"
        await db.execute(insert(records), [
            {"owner": "owner", "project": "project", "kind": "task", "item_id": f"terminal-{i}",
             "revision": 1, "payload": payload, "updated_at": int(time.time()) + 10}
            for i in range(1001)
        ])
        assert (await service.claim_task())["id"] == task["id"]


async def test_claim_paginates_blocked_candidates_without_losing_ready_work(evolution_db):
    from sqlalchemy import insert

    from backend.servicos.evolucao.repositorio import records

    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        dependency = await service.create_task(TaskInput(title="dependency", dedupe_key="dependency"))
        waiting = await service.create_task(TaskInput(title="waiting", dedupe_key="waiting", dependencies=[dependency["id"]]))
        payload = service.repo.payload(waiting)
        await db.execute(insert(records), [
            {"owner": "owner", "project": "project", "kind": "task", "item_id": f"blocked-{i}",
             "revision": 1, "payload": payload, "updated_at": int(time.time())}
            for i in range(102)
        ])
        ready = await service.create_task(TaskInput(title="repair", dedupe_key="repair", category="repair"))
        assert (await service.claim_task())["id"] == ready["id"]


async def test_leases_and_server_identity_reject_coerced_or_empty_values(evolution_db):
    async with evolution_db() as db:
        for identity in ((" ", "project"), ("owner", "\x00project"), (1, "project")):
            with pytest.raises(EvolutionError, match="invalid_server_identity"):
                EvolutionService(db, *identity)
        service = EvolutionService(db, "owner", "project")
        task = await service.create_task(TaskInput(title="job", dedupe_key="job"))
        for lease in (True, 1.5, "120"):
            with pytest.raises(EvolutionError, match="invalid_lease"):
                await service.claim_task(task["id"], lease)
        claimed = await service.claim_task(task["id"])
        assert claimed["fence"] == 1
        with pytest.raises(EvolutionError, match="stale_lease"):
            await service.finish_task(task["id"], True, success=True)


async def test_expired_effect_lease_is_uncertain(evolution_db, monkeypatch):
    clock = [int(time.time())]
    monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: clock[0])
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        item = await approved(service)
        claimed = await service.claim_action(item["id"], {"test.deliver"}, lease_seconds=1)
        clock[0] += 2
        recovered = await service.claim_action(item["id"], {"test.deliver"})
        assert recovered["status"] == "uncertain"
        with pytest.raises(EvolutionError, match="stale_lease"):
            await service.finish_action(item["id"], claimed["fence"], outcome="succeeded")


async def test_schema_shadowing_sql_payload_and_production_fail_closed(evolution_db):
    with pytest.raises(ValidationError):
        TaskInput(title="job", dedupe_key="key", owner="forged")
    with pytest.raises(ValidationError):
        ActionInput(**action(payload={"bad": float("nan")}))
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        with pytest.raises(EvolutionError, match="reserved_record_fields"):
            await service.put_record("profile", "bad", {"owner": "forged"})
        saved = await service.add_fact(fact(content="'); DROP TABLE evolution_records; --"))
        assert (await service.list_facts())[0]["content"] == saved["content"]
        db.info["evolution_test_database"] = False
        with pytest.raises(EvolutionError, match="postgresql_required"):
            EvolutionService(db, "owner", "project")


async def test_rate_limit_persists_between_sessions_and_resets(evolution_db, monkeypatch):
    clock = [12000]
    monkeypatch.setattr("backend.servicos.evolucao.operacoes._now", lambda: clock[0])
    for _ in range(2):
        async with evolution_db() as db:
            assert await EvolutionService(db, "owner", "project").consume_rate_limit("provider", 2, 60)
            await db.commit()
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        assert not await service.consume_rate_limit("provider", 2, 60)
        clock[0] += 60
        assert await service.consume_rate_limit("provider", 2, 60)


async def test_concurrent_claim_never_exposes_two_leases(evolution_db):
    async with evolution_db() as db:
        task = await EvolutionService(db, "owner", "project").create_task(TaskInput(title="one worker", dedupe_key="one-worker"))
        await db.commit()

    async def claim():
        async with evolution_db() as db:
            row = await EvolutionService(db, "owner", "project").claim_task(task["id"])
            await db.commit()
            return row

    outcomes = await asyncio.gather(claim(), claim(), return_exceptions=True)
    successes = [row for row in outcomes if isinstance(row, dict)]
    assert len(successes) == 1
    # A DB conflict may fail closed on SQLite rather than emulate PostgreSQL locks.
    assert all(row is None or isinstance(row, (dict, Exception)) for row in outcomes)
