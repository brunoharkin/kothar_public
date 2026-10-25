"""Persistência SQLAlchemy, sem criar banco/tabelas ou fallback em produção."""

from __future__ import annotations

import copy
import time
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    case,
    insert,
    or_,
    select,
    tuple_,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .modelos import EvolutionError

metadata = MetaData()
records = Table(
    "evolution_records", metadata,
    Column("owner", String(128), primary_key=True),
    Column("project", String(128), primary_key=True),
    Column("kind", String(32), primary_key=True),
    Column("item_id", String(100), primary_key=True),
    Column("revision", Integer, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("updated_at", BigInteger, nullable=False),
)


class EvolutionRepository:
    def __init__(self, db: AsyncSession, owner: str, project: str):
        if any(not isinstance(value, str) or not value.strip() or len(value) > 128 or "\x00" in value
               for value in (owner, project)):
            raise EvolutionError("invalid_server_identity")
        self.db, self.owner, self.project = db, owner, project

    def where(self, kind: str, item_id: str | None = None):
        parts = [records.c.owner == self.owner, records.c.project == self.project, records.c.kind == kind]
        if item_id is not None:
            parts.append(records.c.item_id == item_id)
        return and_(*parts)

    @staticmethod
    def unpack(row) -> dict[str, Any]:
        return {"id": row.item_id, "revision": row.revision, **copy.deepcopy(row.payload)}

    async def get(self, kind: str, item_id: str, *, lock: bool = False) -> dict | None:
        query = select(records).where(self.where(kind, item_id))
        if lock:
            query = query.with_for_update()
        row = (await self.db.execute(query)).first()
        return self.unpack(row) if row else None

    async def list(self, kind: str, limit: int = 100) -> list[dict]:
        if not 1 <= limit <= 1000:
            raise EvolutionError("invalid_limit")
        rows = (await self.db.execute(select(records).where(self.where(kind)).order_by(records.c.updated_at.desc(), records.c.item_id).limit(limit))).all()
        return [self.unpack(row) for row in rows]

    async def task_candidates(self, now: int):
        """Scan eligible tasks with a stable cursor, including older queued work.

        Terminal history cannot hide pending tasks. The key contains immutable
        scheduling fields; a claim/removal while iterating cannot shift an OFFSET.
        Blocked work is considered first so completed dependencies can unblock it.
        """
        payload = records.c.payload
        status = payload["status"].as_string()
        blocked = case((status == "blocked", 0), else_=1)
        category = case((payload["category"].as_string() == "repair", 0),
                        (payload["category"].as_string() == "resume", 1), else_=2)
        priority = -payload["priority"].as_integer()
        created = payload["created_at"].as_integer()
        ordering = (blocked, category, priority, created, records.c.item_id)
        eligible = or_(status.in_(("queued", "blocked")),
                       and_(status == "retry_wait", payload["next_attempt_at"].as_integer() <= now),
                       and_(status == "running", payload["lease_until"].as_integer() <= now))
        cursor = None
        while True:
            query = select(records).where(self.where("task"), eligible)
            if cursor is not None:
                query = query.where(tuple_(*ordering) > tuple_(*cursor))
            rows = (await self.db.execute(query.order_by(*ordering).limit(100))).all()
            if not rows:
                return
            last = self.unpack(rows[-1])
            cursor = (0 if last["status"] == "blocked" else 1,
                      {"repair": 0, "resume": 1, "new": 2}[last["category"]],
                      -last["priority"], last["created_at"], last["id"])
            for row in rows:
                yield self.unpack(row)

    async def create(self, kind: str, item_id: str, payload: dict) -> tuple[dict, bool]:
        try:
            async with self.db.begin_nested():
                await self.db.execute(insert(records).values(owner=self.owner, project=self.project, kind=kind, item_id=item_id, revision=1, payload=payload, updated_at=int(time.time())))
        except IntegrityError:
            existing = await self.get(kind, item_id)
            if existing is None:
                raise
            return existing, False
        return {"id": item_id, "revision": 1, **copy.deepcopy(payload)}, True

    async def replace(self, kind: str, row: dict, payload: dict) -> dict:
        result = await self.db.execute(update(records).where(self.where(kind, row["id"]), records.c.revision == row["revision"]).values(payload=payload, revision=row["revision"] + 1, updated_at=int(time.time())))
        if result.rowcount != 1:
            raise EvolutionError("concurrent_change")
        return {"id": row["id"], "revision": row["revision"] + 1, **copy.deepcopy(payload)}

    @staticmethod
    def payload(row: dict) -> dict:
        return {key: copy.deepcopy(value) for key, value in row.items() if key not in {"id", "revision"}}
