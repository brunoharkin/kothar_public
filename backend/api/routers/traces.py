"""Traces router."""

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.metrics import record_trace
from backend.trace.trace_recorder import trace_recorder
from backend.trace.models import Trace
from backend.core.privacy import REDACTED, safe_metadata

log = get_logger("api.traces")
router = APIRouter()


class TraceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID
    sequence: int = Field(default=0, ge=0, le=10_000_000)
    event_type: str = Field(default="unknown", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    agent_name: str = Field(default="unknown", min_length=1, max_length=100)
    content: object | None = None
    tool_name: str | None = Field(default=None, max_length=100)
    tool_input: object | None = None
    tool_output: object | None = None
    duration_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    tokens_used: int = Field(default=0, ge=0, le=100_000_000)
    input_tokens: int | None = Field(default=None, ge=0, le=100_000_000)
    output_tokens: int | None = Field(default=None, ge=0, le=100_000_000)
    tokens_input: int | None = Field(default=None, ge=0, le=100_000_000)
    tokens_output: int | None = Field(default=None, ge=0, le=100_000_000)
    is_error: bool = False
    error_message: object | None = None
    metadata: dict = Field(default_factory=dict)


class ThinkingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID
    agent_name: str = Field(default="unknown", min_length=1, max_length=100)
    thinking_content: str = Field(default="", max_length=1_000_000)
    tokens: int = Field(default=0, ge=0, le=100_000_000)
    metadata: dict = Field(default_factory=dict)


@router.get("/")
async def list_traces(
    session_id: uuid.UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    is_error: bool | None = Query(default=None),
    limit: int = Query(default=500, le=5000),
    offset: int = Query(default=0),
):
    """Lista traces com filtros."""
    async with get_db_session() as db:
        q = select(Trace).order_by(desc(Trace.created_at))
        if session_id:
            q = q.where(Trace.session_id == session_id)
        if event_type:
            q = q.where(Trace.event_type == event_type)
        if is_error is not None:
            q = q.where(Trace.is_error == is_error)
        q = q.limit(limit).offset(offset)
        result = await db.execute(q)
        return [_trace_to_dict(t) for t in result.scalars().all()]


@router.post("/")
async def record_trace(body: TraceInput):
    """Grava um evento de trace."""
    # Aceitar tokens_input/output do hook para granularidade
    tokens_used = body.tokens_used
    tokens_in = body.input_tokens or body.tokens_input or 0
    tokens_out = body.output_tokens or body.tokens_output or 0

    # Se não vier separados, estimar do total
    if tokens_in == 0 and tokens_out == 0 and tokens_used > 0:
        tokens_in = int(tokens_used * 0.3)
        tokens_out = tokens_used - tokens_in

    event_type = body.event_type
    metadata = safe_metadata(body.metadata)

    async with get_db_session() as db:
        trace = Trace(
            session_id=body.session_id,
            sequence=body.sequence,
            event_type=event_type,
            agent_name=body.agent_name,
            content=REDACTED if body.content is not None else None,
            tool_name=body.tool_name,
            tool_input=REDACTED if body.tool_input is not None else None,
            tool_output=REDACTED if body.tool_output is not None else None,
            duration_ms=body.duration_ms,
            tokens_used=tokens_used,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            is_error=body.is_error,
            error_message=REDACTED if body.error_message is not None else None,
            metadata_=metadata,
        )
        db.add(trace)
        await db.flush()

        return _trace_to_dict(trace)


@router.post("/thinking")
async def record_thinking_trace(body: ThinkingInput):
    """Endpoint dedicado para captura de thinking via record_thinking().

    Salva o thinking completo sem truncamento e emite thinking_captured.
    """
    thinking_length = len(body.thinking_content)
    redacted = TraceInput(
        session_id=body.session_id, event_type="thinking_captured",
        agent_name=body.agent_name, content=REDACTED, tokens_used=body.tokens,
        metadata={"thinking_length_chars": thinking_length,
                  "thinking_length_tokens_est": max(1, int(thinking_length / 3.5))},
    )
    trace = await record_trace(redacted)
    return {
        "thinking_trace_id": trace["id"],
        "thinking_length_chars": thinking_length,
        "thinking_length_tokens_est": max(1, int(thinking_length / 3.5)),
    }


@router.get("/{trace_id}")
async def get_trace(trace_id: uuid.UUID):
    """Retorna um trace específico."""
    async with get_db_session() as db:
        result = await db.execute(select(Trace).where(Trace.id == trace_id))
        trace = result.scalar_one_or_none()
        if not trace:
            return JSONResponse(status_code=404, content={"error": "Trace não encontrado"})
        return _trace_to_dict(trace)


from sqlalchemy import delete

@router.delete("/")
async def delete_traces(session_id: uuid.UUID = Query(..., description="ID da sessão para deletar traces")):
    """Deleta todos os traces de uma sessão."""
    async with get_db_session() as db:
        await db.execute(delete(Trace).where(Trace.session_id == session_id))
        await db.flush()
        return {"success": True}



def _trace_to_dict(t: Trace) -> dict:
    return {
        "id": str(t.id),
        "session_id": str(t.session_id),
        "sequence": t.sequence,
        "event_type": t.event_type,
        "agent_name": t.agent_name,
        "content": t.content,
        "tool_name": t.tool_name,
        "tool_input": t.tool_input,
        "tool_output": t.tool_output,
        "duration_ms": t.duration_ms,
        "tokens_used": t.tokens_used,
        "tokens_input": t.tokens_input,
        "tokens_output": t.tokens_output,
        "is_error": t.is_error,
        "error_message": t.error_message,
        "metadata": t.metadata_,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
