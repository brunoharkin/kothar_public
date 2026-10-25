"""Authenticated durable state used by browser tools; PostgreSQL is authoritative."""
import json
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from backend.core.database import get_db_session

router = APIRouter()
StateKind = Literal["prompt_variant", "ab_test", "marked_error"]
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class StateItem(BaseModel):
    id: str
    payload: dict = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not ID_PATTERN.fullmatch(value):
            raise ValueError("identificador inválido")
        return value

    @field_validator("payload")
    @classmethod
    def bounded_payload(cls, value: dict) -> dict:
        if len(json.dumps(value, ensure_ascii=False)) > 256_000:
            raise ValueError("payload excede o limite")
        return value


def owner(request: Request) -> str:
    principal = getattr(request.state, "principal", "")
    if not principal:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return principal


@router.get("/{kind}")
async def list_state(kind: StateKind, request: Request):
    async with get_db_session() as db:
        result = await db.execute(
            text("SELECT item_id, payload, updated_at FROM workspace_state "
                 "WHERE owner = :owner AND kind = :kind ORDER BY updated_at DESC LIMIT 500"),
            {"owner": owner(request), "kind": kind},
        )
        return [{"id": row.item_id, "payload": row.payload,
                 "updated_at": row.updated_at.isoformat()} for row in result]


@router.put("/{kind}/{item_id}")
async def put_state(kind: StateKind, item_id: str, body: StateItem, request: Request):
    if body.id != item_id:
        raise HTTPException(status_code=400, detail="identificadores divergentes")
    async with get_db_session() as db:
        await db.execute(
            text("INSERT INTO workspace_state (owner, kind, item_id, payload) "
                 "VALUES (:owner, :kind, :item_id, CAST(:payload AS JSONB)) "
                 "ON CONFLICT (owner, kind, item_id) DO UPDATE "
                 "SET payload = EXCLUDED.payload, updated_at = NOW()"),
            {"owner": owner(request), "kind": kind, "item_id": item_id,
             "payload": json.dumps(body.payload, ensure_ascii=False)},
        )
    return {"saved": True, "id": item_id}


@router.delete("/{kind}/{item_id}")
async def delete_state(kind: StateKind, item_id: str, request: Request):
    if not ID_PATTERN.fullmatch(item_id):
        raise HTTPException(status_code=400, detail="identificador inválido")
    async with get_db_session() as db:
        result = await db.execute(
            text("DELETE FROM workspace_state WHERE owner = :owner AND kind = :kind "
                 "AND item_id = :item_id"),
            {"owner": owner(request), "kind": kind, "item_id": item_id},
        )
    return {"deleted": result.rowcount == 1, "id": item_id}
