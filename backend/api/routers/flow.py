"""Flow visualization router."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select, func, and_

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.harness.checkpoint import checkpoint_manager
from backend.harness.circuit_breaker import CircuitBreakerRegistry
from backend.memory.cache.redis_client import RedisMemory
from backend.trace.models import Trace, Session, Blueprint
from backend.trace.trace_recorder import trace_recorder

log = get_logger("api.flow")
router = APIRouter()


@router.get("/{session_id}")
async def get_flow_status(session_id: str):
    """
    Retorna status completo do fluxo em tempo real.
    Inclui:
    - Progresso do blueprint
    - Eventos recentes do trace
    - Circuit breakers
    - Timeline visual
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "session_id inválido"})

    redis = RedisMemory()

    # Busca blueprint
    blueprint = await redis.get_blueprint(session_id)

    # Busca último checkpoint
    last_checkpoint = await checkpoint_manager.get_last_checkpoint(session_id)

    # Busca traces recentes
    async with get_db_session() as db:
        traces_result = await db.execute(
            select(Trace)
            .where(Trace.session_id == session_uuid)
            .order_by(desc(Trace.sequence))
            .limit(100)
        )
        traces = traces_result.scalars().all()

    # Busca sessão
    async with get_db_session() as db:
        session_result = await db.execute(
            select(Session).where(Session.id == session_uuid)
        )
        session = session_result.scalar_one_or_none()

    # Status atual
    if not blueprint:
        return JSONResponse(status_code=404, content={"error": "Sessão não encontrada"})

    steps = blueprint.get("steps", [])
    completed = sum(1 for s in steps if s.get("status") == "done")
    in_progress = [s for s in steps if s.get("status") == "in_progress"]
    failed = sum(1 for s in steps if s.get("status") in ("failed", "timeout"))
    locked = sum(1 for s in steps if s.get("status") == "locked")

    # Circuit breakers
    circuit_status = CircuitBreakerRegistry.get_all_status()

    # Timeline de eventos
    timeline = []
    for trace in reversed(traces[:50]):
        event = {
            "sequence": trace.sequence,
            "type": trace.event_type,
            "agent": trace.agent_name,
            "content": trace.content[:100] if trace.content else None,
            "timestamp": trace.created_at.isoformat() if trace.created_at else None,
            "duration_ms": trace.duration_ms,
            "is_error": trace.is_error,
        }
        timeline.append(event)

    # Próximo passo executável
    next_executable = None
    for step in steps:
        if step.get("status") == "pending":
            # Verifica se tem deps atendidas (simplificado)
            next_executable = step
            break

    return {
        "session_id": session_id,
        "blueprint_id": blueprint.get("id"),
        "session_status": session.status if session else "unknown",
        "progress": {
            "total": len(steps),
            "completed": completed,
            "in_progress": len(in_progress),
            "failed": failed,
            "locked": locked,
            "pending": len(steps) - completed - len(in_progress) - failed - locked,
            "percentage": round((completed / len(steps) * 100) if steps else 0, 1),
        },
        "current_step": in_progress[0] if in_progress else None,
        "next_step": next_executable,
        "last_checkpoint": {
            "step_id": last_checkpoint.step_id if last_checkpoint else None,
            "step_title": last_checkpoint.step_title if last_checkpoint else None,
            "status": last_checkpoint.status if last_checkpoint else None,
            "timestamp": last_checkpoint.timestamp if last_checkpoint else None,
        } if last_checkpoint else None,
        "circuit_breakers": circuit_status,
        "timeline": timeline,
        "steps": [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "agent": s.get("agent"),
                "status": s.get("status"),
                "result": s.get("result"),
            }
            for s in steps
        ],
    }


@router.get("/{session_id}/timeline")
async def get_flow_timeline(session_id: str, limit: int = Query(default=100, le=500)):
    """
    Retorna timeline de eventos do fluxo.
    Útil para visualização gráfica.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "session_id inválido"})

    async with get_db_session() as db:
        result = await db.execute(
            select(Trace)
            .where(Trace.session_id == session_uuid)
            .order_by(Trace.sequence)
            .limit(limit)
        )
        traces = result.scalars().all()

    # Agrupa por tipo de evento
    events = []
    for trace in traces:
        events.append({
            "sequence": trace.sequence,
            "type": trace.event_type,
            "agent": trace.agent_name,
            "content": trace.content,
            "timestamp": trace.created_at.isoformat() if trace.created_at else None,
            "duration_ms": trace.duration_ms,
            "is_error": trace.is_error,
            "tool": trace.tool_name,
        })

    return {
        "session_id": session_id,
        "total_events": len(events),
        "events": events,
    }


@router.get("/{session_id}/gantt")
async def get_flow_gantt(session_id: str):
    """
    Retorna dados no formato Gantt para visualização.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "session_id inválido"})

    redis = RedisMemory()
    blueprint = await redis.get_blueprint(session_id)

    if not blueprint:
        return JSONResponse(status_code=404, content={"error": "Blueprint não encontrado"})

    # Busca traces para calcular durações
    async with get_db_session() as db:
        traces_result = await db.execute(
            select(Trace)
            .where(Trace.session_id == session_uuid)
            .where(Trace.event_type.in_(["step_start", "step_done", "step_failed"]))
            .order_by(Trace.sequence)
        )
        traces = traces_result.scalars().all()

    # Constrói timeline
    step_times = {}
    for trace in traces:
        meta = trace.metadata_ or {}
        step_id = meta.get("step_id")
        if step_id:
            if trace.event_type == "step_start":
                step_times[step_id] = {"start": trace.created_at, "end": None}
            elif trace.event_type in ("step_done", "step_failed"):
                if step_id in step_times:
                    step_times[step_id]["end"] = trace.created_at

    # Gantt
    gantt_rows = []
    for step in blueprint.get("steps", []):
        step_id = step.get("id")
        times = step_times.get(step_id, {})
        status = step.get("status")

        gantt_rows.append({
            "id": step_id,
            "title": step.get("title"),
            "agent": step.get("agent"),
            "status": status,
            "start": times.get("start").isoformat() if times.get("start") else None,
            "end": times.get("end").isoformat() if times.get("end") else None,
            "duration_ms": step.get("duration_ms"),
        })

    return {
        "session_id": session_id,
        "gantt": gantt_rows,
    }


@router.get("/{session_id}/checkpoints")
async def get_flow_checkpoints(session_id: str):
    """Retorna histórico de checkpoints da sessão."""
    checkpoints = await checkpoint_manager.get_checkpoint_history(session_id)

    return {
        "session_id": session_id,
        "checkpoints": [
            {
                "step_id": cp.step_id,
                "step_title": cp.step_title,
                "status": cp.status,
                "result": cp.result,
                "error": cp.error,
                "timestamp": cp.timestamp,
            }
            for cp in checkpoints
        ],
    }


@router.get("/circuit-breakers")
async def get_circuit_breakers():
    """Retorna status de todos os circuit breakers."""
    return {
        "circuit_breakers": CircuitBreakerRegistry.get_all_status(),
    }


@router.post("/circuit-breakers/{agent_name}/reset")
async def reset_circuit_breaker(agent_name: str):
    """Reseta o circuit breaker de um agente."""
    CircuitBreakerRegistry.reset(agent_name)

    await trace_recorder.record(
        session_id="system",
        event_type="circuit_breaker_reset",
        agent_name=agent_name,
        content=f"Circuit breaker resetado para {agent_name}",
    )

    return {"success": True, "agent": agent_name}


# =====================================================
# FLOW METRICS
# =====================================================

@router.get("/metrics/summary")
async def get_flow_metrics_summary(
    hours: int = Query(default=24, le=168),
):
    """
    Retorna resumo de métricas de fluxo no período.
    """
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with get_db_session() as db:
        # Conta TODOS os eventos de trace (não só os de fluxo específico)
        all_events_q = (
            select(Trace.event_type, func.count(Trace.id).label("count"))
            .where(Trace.created_at >= since)
            .group_by(Trace.event_type)
        )
        all_events_result = await db.execute(all_events_q)
        all_events = dict(all_events_result.all())

        # Eventos de fluxo (para compatibilidade)
        flow_events = ["flow_start", "flow_end", "step_start", "step_done", "step_failed", "step_locked"]
        flow_counts = {k: all_events.get(k, 0) for k in flow_events}

        # Eventos reais de trace (que existem no banco)
        trace_events = {
            "tool_call": all_events.get("tool_call", 0),
            "tool_result": all_events.get("tool_result", 0),
            "assistant_response": all_events.get("assistant_response", 0),
            "user_message": all_events.get("user_message", 0),
            "thinking": all_events.get("thinking", 0),
        }

        # Total de traces no período
        total_traces = sum(all_events.values())

        # Circuit breaker events
        cb_events = ["circuit_breaker", "circuit_breaker_reset"]
        cb_q = (
            select(func.count(Trace.id))
            .where(and_(
                Trace.created_at >= since,
                Trace.event_type.in_(cb_events)
            ))
        )
        cb_total = (await db.execute(cb_q)).scalar() or 0

        # Checkpoint events
        cp_q = (
            select(func.count(Trace.id))
            .where(and_(
                Trace.created_at >= since,
                Trace.event_type == "checkpoint"
            ))
        )
        cp_total = (await db.execute(cp_q)).scalar() or 0

        # Blueprints criados
        bp_created_q = (
            select(func.count(Blueprint.id))
            .where(Blueprint.created_at >= since)
        )
        bp_created = (await db.execute(bp_created_q)).scalar() or 0

        # Blueprints completados
        bp_completed_q = (
            select(func.count(Blueprint.id))
            .where(and_(
                Blueprint.completed_at >= since,
                Blueprint.status.in_(["completed", "done"])
            ))
        )
        bp_completed = (await db.execute(bp_completed_q)).scalar() or 0

        # Blueprints falhados
        bp_failed_q = (
            select(func.count(Blueprint.id))
            .where(and_(
                Blueprint.completed_at >= since,
                Blueprint.status == "failed"
            ))
        )
        bp_failed = (await db.execute(bp_failed_q)).scalar() or 0

        # Duração média dos flows
        avg_duration_q = (
            select(func.avg(Trace.duration_ms))
            .where(and_(
                Trace.created_at >= since,
                Trace.event_type == "flow_end",
                Trace.duration_ms.isnot(None)
            ))
        )
        avg_duration = (await db.execute(avg_duration_q)).scalar() or 0

        # Top agentes mais executados
        top_agents_q = (
            select(Trace.agent_name, func.count(Trace.id))
            .where(and_(
                Trace.created_at >= since,
                Trace.agent_name.isnot(None),
            ))
            .group_by(Trace.agent_name)
            .order_by(desc(func.count(Trace.id)))
            .limit(10)
        )
        top_agents = dict((await db.execute(top_agents_q)).all())

        # Sessões no período
        sessions_in_period_q = (
            select(func.count(Session.id))
            .where(Session.started_at >= since)
        )
        sessions_in_period = (await db.execute(sessions_in_period_q)).scalar() or 0

    return {
        "period_hours": hours,
        "period_since": since.isoformat(),
        "total_traces": total_traces,
        "total_sessions": sessions_in_period,
        "flow_events": {
            "flow_start": flow_counts.get("flow_start", 0),
            "flow_end": flow_counts.get("flow_end", 0),
            "step_start": flow_counts.get("step_start", 0),
            "step_done": flow_counts.get("step_done", 0),
            "step_failed": flow_counts.get("step_failed", 0),
            "step_locked": flow_counts.get("step_locked", 0),
        },
        "trace_events": trace_events,
        "all_events_by_type": all_events,
        "circuit_breaker_events": cb_total,
        "checkpoint_events": cp_total,
        "blueprints": {
            "created": bp_created,
            "completed": bp_completed,
            "failed": bp_failed,
        },
        "avg_flow_duration_ms": round(float(avg_duration), 2) if avg_duration else 0,
        "top_agents": top_agents,
        "circuit_breakers": CircuitBreakerRegistry.get_all_status(),
    }


@router.get("/{session_id}/events")
async def get_flow_events(
    session_id: str,
    event_types: str = Query(default=None, description="Vírgulas: flow_start,step_done,etc"),
):
    """
    Retorna eventos de fluxo para uma sessão.
    Útil para reconstruir o timeline completo.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "session_id inválido"})

    flow_events = ["flow_start", "flow_end", "step_start", "step_done", "step_failed", "step_locked", "circuit_breaker", "checkpoint"]

    async with get_db_session() as db:
        q = (
            select(Trace)
            .where(Trace.session_id == session_uuid)
            .where(Trace.event_type.in_(flow_events))
            .order_by(Trace.sequence)
        )

        if event_types:
            types = [t.strip() for t in event_types.split(",")]
            q = q.where(Trace.event_type.in_(types))

        result = await db.execute(q)
        traces = result.scalars().all()

    return {
        "session_id": session_id,
        "total_events": len(traces),
        "events": [
            {
                "sequence": t.sequence,
                "type": t.event_type,
                "agent": t.agent_name,
                "content": t.content,
                "timestamp": t.created_at.isoformat() if t.created_at else None,
                "duration_ms": t.duration_ms,
                "is_error": t.is_error,
                "metadata": t.metadata_,
            }
            for t in traces
        ],
    }
