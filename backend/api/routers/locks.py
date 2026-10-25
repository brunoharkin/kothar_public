"""
KOTHAR v4.0 — Locks Router
API para gerenciar locks (padrões de erro aprendidos).
Quando o usuário marca um erro no frontend, ele é salvo aqui.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.models import Lock

log = get_logger("api.locks")
router = APIRouter()


class CreateLockRequest(BaseModel):
    pattern: str
    description: str
    alternative: Optional[str] = None
    category: Optional[str] = "user_reported"
    # Campos extras para erro do usuário
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    error_type: Optional[str] = None  # falso_positivo, bug_real, falso_negativo
    where_in_code: Optional[str] = None
    which_model: Optional[str] = None
    which_agent: Optional[str] = None
    marked_by: Optional[str] = "user"
    marked_at: Optional[str] = None


@router.post("/create")
async def create_lock(req: CreateLockRequest):
    """
    Cria um novo lock (padrão de erro a evitar).
    Chamado quando o usuário marca um erro no trace.
    """
    try:
        async with get_db_session() as db:
            lock = Lock(
                pattern=req.pattern[:500],
                description=req.description,
                alternative=req.alternative,
                category=req.category or "user_reported",
                trigger_count=1,
                is_active=True,
            )
            db.add(lock)
            await db.commit()
            await db.refresh(lock)

            log.info(
                "Lock criado pelo usuário",
                lock_id=str(lock.id),
                pattern=req.pattern[:80],
                error_type=req.error_type,
                trace_id=req.trace_id,
            )

            return {
                "id": str(lock.id),
                "pattern": lock.pattern,
                "description": lock.description,
                "alternative": lock.alternative,
                "category": lock.category,
                "created_at": lock.created_at.isoformat() if lock.created_at else None,
            }
    except Exception as e:
        log.error(f"Erro ao criar lock: {e}")
        return {"error": str(e), "success": False}


@router.get("/")
async def list_locks(
    category: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, le=200),
):
    """Lista locks (padrões de erro aprendidos)."""
    async with get_db_session() as db:
        q = select(Lock).order_by(desc(Lock.created_at))
        if category:
            q = q.where(Lock.category == category)
        if active_only:
            q = q.where(Lock.is_active == True)
        q = q.limit(limit)
        result = await db.execute(q)
        return [_lock_to_dict(l) for l in result.scalars().all()]


@router.get("/{lock_id}")
async def get_lock(lock_id: uuid.UUID):
    """Busca um lock específico."""
    async with get_db_session() as db:
        result = await db.execute(select(Lock).where(Lock.id == lock_id))
        lock = result.scalar_one_or_none()
        if not lock:
            return {"error": "Lock não encontrado"}
        return _lock_to_dict(lock)


def _lock_to_dict(l: Lock) -> dict:
    return {
        "id": str(l.id),
        "pattern": l.pattern,
        "description": l.description,
        "alternative": l.alternative,
        "category": l.category,
        "trigger_count": l.trigger_count,
        "is_active": l.is_active,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }
