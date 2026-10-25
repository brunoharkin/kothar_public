"""Sessions router."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.models import Session

log = get_logger("api.sessions")
router = APIRouter()


@router.get("/")
async def list_sessions(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    status: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
):
    """Lista sessões com filtros opcionais."""
    async with get_db_session() as db:
        q = select(Session).order_by(desc(Session.started_at))
        if status:
            q = q.where(Session.status == status)
        if agent_name:
            q = q.where(Session.agent_name == agent_name)
        q = q.limit(limit).offset(offset)
        result = await db.execute(q)
        sessions = result.scalars().all()
        return [_session_to_dict(s) for s in sessions]


@router.post("/")
async def create_session(body: dict):
    """Inicia uma nova sessão de agente."""
    async with get_db_session() as db:
        session = Session(
            agent_name=body.get("agent_name", "unknown"),
            llm_model=body.get("llm_model"),
            task_summary=body.get("task_summary"),
            metadata_=body.get("metadata", {}),
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)
        log.info("Nova sessão criada", session_id=str(session.id), agent=session.agent_name)
        return _session_to_dict(session)


@router.get("/{session_id}")
async def get_session(session_id: uuid.UUID):
    """Retorna detalhes de uma sessão."""
    async with get_db_session() as db:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            return JSONResponse(status_code=404, content={"error": "Sessão não encontrada"})
        return _session_to_dict(session)


@router.patch("/{session_id}/complete")
async def complete_session(session_id: uuid.UUID, body: dict):
    """Finaliza uma sessão."""
    async with get_db_session() as db:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            return JSONResponse(status_code=404, content={"error": "Sessão não encontrada"})
        session.ended_at = datetime.now(timezone.utc)
        session.status = body.get("status", "completed")
        session.tokens_input = body.get("tokens_input", session.tokens_input)
        session.tokens_output = body.get("tokens_output", session.tokens_output)
        session.total_cost_usd = body.get("total_cost_usd", session.total_cost_usd)
        log.info("Sessão finalizada", session_id=str(session_id), status=session.status)
        return _session_to_dict(session)


@router.delete("/{session_id}")
async def delete_session(session_id: uuid.UUID):
    """Deleta uma sessão."""
    async with get_db_session() as db:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            return JSONResponse(status_code=404, content={"error": "Sessão não encontrada"})
        await db.delete(session)
        await db.flush()
        return {"deleted": True, "id": str(session_id)}


@router.delete("/action/purge_all")
async def purge_all_sessions():
    """Expurgo total (Hard Reset) de todas as sessões."""
    from sqlalchemy import text
    async with get_db_session() as db:
        await db.execute(text("TRUNCATE TABLE sessions CASCADE"))
        await db.commit()
        log.warning("Todas as sessões foram expurgadas do banco (HARD RESET)!")
        return {"deleted": True, "message": "Todas as sessões foram removidas."}


def _session_to_dict(s: Session) -> dict:
    return {
        "id": str(s.id),
        "agent_name": s.agent_name,
        "llm_model": s.llm_model,
        "task_summary": s.task_summary,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "tokens_input": s.tokens_input,
        "tokens_output": s.tokens_output,
        "total_cost_usd": float(s.total_cost_usd),
        "metadata": s.metadata_,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
