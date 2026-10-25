"""Traces router."""

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.metrics import record_trace
from backend.trace.trace_recorder import trace_recorder
from backend.trace.models import Trace

log = get_logger("api.traces")
router = APIRouter()


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
async def record_trace(body: dict):
    """Grava um evento de trace."""
    # Aceitar tokens_input/output do hook para granularidade
    tokens_used = body.get("tokens_used", 0)
    tokens_in = body.get("input_tokens") or body.get("tokens_input") or 0
    tokens_out = body.get("output_tokens") or body.get("tokens_output") or 0

    # Se não vier separados, estimar do total
    if tokens_in == 0 and tokens_out == 0 and tokens_used > 0:
        tokens_in = int(tokens_used * 0.3)
        tokens_out = tokens_used - tokens_in

    event_type = body.get("event_type", "unknown")

    # Para eventos de thinking, salvar conteúdo completo (sem limite de truncamento)
    tool_input = body.get("tool_input")
    content = body.get("content")

    # Se for thinking e tiver tool_input com thinking, extrair conteúdo completo
    if event_type == "thinking" and tool_input:
        if isinstance(tool_input, dict) and "thinking" in tool_input:
            content = tool_input["thinking"]
        elif isinstance(tool_input, str):
            content = tool_input

    async with get_db_session() as db:
        trace = Trace(
            session_id=uuid.UUID(body["session_id"]),
            sequence=body.get("sequence", 0),
            event_type=event_type,
            agent_name=body.get("agent_name", "unknown"),
            content=content,
            tool_name=body.get("tool_name"),
            tool_input=tool_input,
            tool_output=body.get("tool_output"),
            duration_ms=body.get("duration_ms"),
            tokens_used=tokens_used,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            is_error=body.get("is_error", False),
            error_message=body.get("error_message"),
            metadata_=body.get("metadata", {}),
        )
        db.add(trace)
        await db.flush()

        # Emitir evento thinking_captured quando thinking é salvo
        if event_type == "thinking":
            thinking_content = content or ""
            thinking_meta = body.get("metadata", {})
            thinking_meta["thinking_captured"] = True
            thinking_meta["thinking_length_chars"] = len(thinking_content)
            thinking_meta["thinking_length_tokens_est"] = max(1, int(len(thinking_content) / 3.5))
            thinking_meta["original_event_id"] = str(trace.id)

            captured_trace = Trace(
                session_id=trace.session_id,
                sequence=trace.sequence + 1,  # Logo após o thinking
                event_type="thinking_captured",
                agent_name=trace.agent_name,
                content=f"Thinking completo salvo: {len(thinking_content)} chars",
                tool_name="Claude:thinking",
                tool_input={"thinking": thinking_content},
                tokens_used=tokens_used,
                metadata_=thinking_meta,
            )
            db.add(captured_trace)
            await db.flush()

        return _trace_to_dict(trace)


@router.post("/thinking")
async def record_thinking_trace(body: dict):
    """Endpoint dedicado para captura de thinking via record_thinking().

    Salva o thinking completo sem truncamento e emite thinking_captured.
    """
    session_id = body.get("session_id")
    agent_name = body.get("agent_name", "unknown")
    thinking_content = body.get("thinking_content", "")
    tokens = body.get("tokens", 0)
    metadata = body.get("metadata", {})

    if not session_id:
        return JSONResponse(status_code=400, content={"error": "session_id é obrigatório"})

    # Usar record_thinking() do TraceRecorder - salva SEM truncamento
    thinking_trace_id = await trace_recorder.record_thinking(
        session_id=session_id,
        agent_name=agent_name,
        thinking_content=thinking_content,
        tokens=tokens,
        metadata=metadata,
    )

    # Emitir evento thinking_captured via API
    try:
        await trace_recorder.record(
            session_id=session_id,
            event_type="thinking_captured",
            agent_name=agent_name,
            content=f"Thinking completo salvo: {len(thinking_content)} chars",
            tool_name="Claude:thinking",
            tool_input={"thinking": thinking_content},
            tokens_used=tokens,
            metadata={
                **metadata,
                "thinking_captured": True,
                "thinking_length_chars": len(thinking_content),
                "thinking_length_tokens_est": max(1, int(len(thinking_content) / 3.5)),
                "original_thinking_id": thinking_trace_id,
            },
        )
    except Exception as e:
        log.warning(f"Erro ao gravar thinking_captured: {e}")

    return {
        "thinking_trace_id": thinking_trace_id,
        "thinking_length_chars": len(thinking_content),
        "thinking_length_tokens_est": max(1, int(len(thinking_content) / 3.5)),
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
