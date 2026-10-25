"""
=============================================================
 KOTHAR v4.0 — Dashboard Metrics Router
 Endpoint unificado para alimentar o painel de métricas.
 Retorna TODAS as métricas em uma única chamada.
=============================================================
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, func, desc, and_

from backend.core.logger import get_logger
from backend.core.database import get_db_session
from backend.trace.models import Session, Trace, Skill, Lock, Blueprint
from backend.trace.metrics import get_metrics as get_general_metrics
from backend.trace.rag_metrics import get_rag_metrics
from backend.harness.circuit_breaker import CircuitBreakerRegistry

log = get_logger("api.dashboard")
router = APIRouter()


# =====================================================
# ENDPOINT PRINCIPAL - Tudo em um
# =====================================================

@router.get("/dashboard")
async def get_dashboard_metrics(
    hours: int = Query(default=24, description="Janela de tempo em horas"),
):
    """
    Endpoint unificado para o painel Observability Hub.

    Retorna TUDO que o painel precisa em uma única chamada:
    - Métricas gerais (uptime, sessões, agentes)
    - Métricas RAG (hits, misses, cache)
    - Sessions detail (lista recente)
    - Trace events (breakdown)
    - Token usage (com multi-modelo)
    - Cascade escalations
    - Health checks
    """
    try:
        result = {}

        # 1. Métricas gerais (in-memory)
        general = get_general_metrics()
        result["uptime_seconds"] = general.get("uptime_seconds", 0)
        result["sessions"] = general.get("sessions", {})
        result["trace_events"] = general.get("trace_events", {})
        result["agents_executed"] = general.get("agents_executed", {})

        # 2. Métricas RAG (in-memory)
        rag = get_rag_metrics()
        result["rag"] = {
            "total_hits": rag.get("total_hits", 0),
            "total_misses": rag.get("total_misses", 0),
            "total_requests": rag.get("total_requests", 0),
            "hit_rate_percent": rag.get("hit_rate_percent", 0.0),
            "cache_hits": rag.get("cache_hits", 0),
            "hits_by_type": rag.get("hits_by_type", {}),
            "misses_by_type": rag.get("misses_by_type", {}),
        }

        # 3. Métricas do banco (PostgreSQL)
        async with get_db_session() as db:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Sessions ativas
            active_q = select(func.count(Session.id)).where(Session.status == "active")
            result["active_sessions"] = (await db.execute(active_q)).scalar() or 0

            # Sessions recentes (limitadas)
            sessions_q = (
                select(Session)
                .where(Session.started_at >= since)
                .order_by(desc(Session.started_at))
                .limit(50)
            )
            sessions = (await db.execute(sessions_q)).scalars().all()
            result["recent_sessions"] = [_sess_to_dict(s) for s in sessions]

            # Total de sessions no período
            total_sessions_q = select(func.count(Session.id)).where(Session.started_at >= since)
            result["total_sessions_period"] = (await db.execute(total_sessions_q)).scalar() or 0

            # Sessions por status no período
            status_q = (
                select(Session.status, func.count(Session.id))
                .where(Session.started_at >= since)
                .group_by(Session.status)
            )
            result["sessions_by_status"] = dict((await db.execute(status_q)).all())

            # Sessions por agente no período
            agent_q = (
                select(Session.agent_name, func.count(Session.id))
                .where(Session.started_at >= since)
                .group_by(Session.agent_name)
                .order_by(desc(func.count(Session.id)))
                .limit(10)
            )
            result["sessions_by_agent"] = dict((await db.execute(agent_q)).all())

            # Tokens totais no período
            tokens_q = (
                select(
                    func.coalesce(func.sum(Session.tokens_input), 0).label("input"),
                    func.coalesce(func.sum(Session.tokens_output), 0).label("output"),
                    func.coalesce(func.sum(Session.total_cost_usd), 0).label("cost"),
                )
                .where(Session.started_at >= since)
            )
            tokens_row = (await db.execute(tokens_q)).one()
            result["token_usage"] = {
                "input": int(tokens_row.input or 0),
                "output": int(tokens_row.output or 0),
                "total": int((tokens_row.input or 0) + (tokens_row.output or 0)),
                "total_cost_usd": float(tokens_row.cost or 0.0),
            }

            # Trace events - distribuição por tipo
            trace_events_q = (
                select(Trace.event_type, func.count(Trace.id))
                .where(Trace.created_at >= since)
                .group_by(Trace.event_type)
                .order_by(desc(func.count(Trace.id)))
                .limit(20)
            )
            result["trace_events_breakdown"] = dict((await db.execute(trace_events_q)).all())

            # Trace events - distribuição por agente
            trace_agents_q = (
                select(Trace.agent_name, func.count(Trace.id))
                .where(and_(Trace.created_at >= since, Trace.agent_name.isnot(None)))
                .group_by(Trace.agent_name)
                .order_by(desc(func.count(Trace.id)))
                .limit(10)
            )
            result["trace_events_by_agent"] = dict((await db.execute(trace_agents_q)).all())

            # Errors no período
            errors_q = (
                select(func.count(Trace.id))
                .where(and_(Trace.created_at >= since, Trace.is_error == True))
            )
            result["errors_count"] = (await db.execute(errors_q)).scalar() or 0

            # Success rate
            total_traces_q = select(func.count(Trace.id)).where(Trace.created_at >= since)
            total_traces = (await db.execute(total_traces_q)).scalar() or 0
            if total_traces > 0:
                result["success_rate_percent"] = round(
                    (1 - result["errors_count"] / total_traces) * 100, 2
                )
            else:
                result["success_rate_percent"] = 100.0

            # Skills cristalizadas
            skills_total = await db.execute(select(func.count(Skill.id)))
            result["skills_total"] = skills_total.scalar() or 0

            # Locks ativos
            locks_total = await db.execute(
                select(func.count(Lock.id)).where(Lock.is_active == True)
            )
            result["locks_active"] = locks_total.scalar() or 0

            # Blueprints recentes
            blueprints_q = (
                select(Blueprint)
                .order_by(desc(Blueprint.created_at))
                .limit(10)
            )
            blueprints = (await db.execute(blueprints_q)).scalars().all()
            result["recent_blueprints"] = [_bp_to_dict(bp) for bp in blueprints]

            # RAG metrics do tracker (mais detalhado)
            try:
                from backend.api.routers.rag_tracker import tracker
                recent_queries = tracker.get_recent(limit=100)
                if recent_queries:
                    total_q = len(recent_queries)
                    hits_q = sum(1 for q in recent_queries if q.get("is_hit"))
                    result["rag_tracker"] = {
                        "total_queries": total_q,
                        "hits": hits_q,
                        "hit_rate": round(hits_q / total_q * 100, 2) if total_q > 0 else 0,
                        "avg_chunks": round(sum(q.get("chunks_count", 0) for q in recent_queries) / total_q, 1) if total_q > 0 else 0,
                    }
            except Exception as e:
                log.debug(f"RAG tracker indisponível: {e}")
                result["rag_tracker"] = {}

            # Cascade metrics (multi-modelo)
            try:
                from backend.trace.cascade_metrics import get_cascade_metrics
                result["cascade"] = get_cascade_metrics()
            except Exception:
                # Fallback: extrai do trace recorder
                model_q = (
                    select(Trace.tool_name, func.count(Trace.id))
                    .where(and_(
                        Trace.created_at >= since,
                        Trace.tool_name.in_(["haiku", "sonnet", "opus"])
                    ))
                    .group_by(Trace.tool_name)
                )
                model_rows = dict((await db.execute(model_q)).all())
                result["cascade"] = {
                    "models_used": model_rows,
                    "total_executions": sum(model_rows.values()),
                }

            # Latência média
            latency_q = (
                select(func.avg(Trace.duration_ms))
                .where(and_(
                    Trace.created_at >= since,
                    Trace.duration_ms.isnot(None)
                ))
            )
            avg_latency = (await db.execute(latency_q)).scalar()
            result["avg_latency_ms"] = round(float(avg_latency or 0), 2)

            # Throughput (traces/min)
            result["throughput_per_min"] = round(
                total_traces / (hours * 60), 2
            ) if total_traces > 0 else 0

        # 4. Harness metrics (circuit breakers, checkpoints)
        result["harness"] = {
            "circuit_breakers": CircuitBreakerRegistry.get_all_status(),
        }

        # 5. Health checks
        result["health"] = await _get_health_status()

        # 6. Metadata
        result["period_hours"] = hours
        result["generated_at"] = datetime.now(timezone.utc).isoformat()

        return result

    except Exception as e:
        log.error(f"Erro ao buscar métricas do dashboard: {e}", exc_info=True)
        return {
            "error": str(e),
            "uptime_seconds": 0,
            "sessions": {"started": 0, "completed": 0, "failed": 0},
            "rag": {"total_hits": 0, "total_misses": 0, "hit_rate_percent": 0},
            "active_sessions": 0,
            "errors_count": 0,
        }


# =====================================================
# ENDPOINTS ESPECÍFICOS
# =====================================================

@router.get("/dashboard/sessions/recent")
async def get_recent_sessions(limit: int = Query(default=20, le=100)):
    """Retorna apenas as sessões recentes."""
    async with get_db_session() as db:
        q = select(Session).order_by(desc(Session.started_at)).limit(limit)
        sessions = (await db.execute(q)).scalars().all()
        return [_sess_to_dict(s) for s in sessions]


@router.get("/dashboard/traces/timeline")
async def get_traces_timeline(
    hours: int = Query(default=24),
    interval_minutes: int = Query(default=60),
):
    """
    Retorna timeline de traces agrupados por intervalo.
    Útil para gráficos de série temporal.
    """
    async with get_db_session() as db:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        q = (
            select(Trace.created_at, Trace.event_type, Trace.is_error, Trace.duration_ms)
            .where(Trace.created_at >= since)
            .order_by(Trace.created_at)
        )
        rows = (await db.execute(q)).all()

        # Agrupa por intervalo
        buckets = {}
        for created_at, event_type, is_error, duration_ms in rows:
            # Trunca para o intervalo
            bucket_key = created_at.replace(
                minute=(created_at.minute // interval_minutes) * interval_minutes,
                second=0,
                microsecond=0,
            )
            bucket_key_str = bucket_key.isoformat()

            if bucket_key_str not in buckets:
                buckets[bucket_key_str] = {
                    "timestamp": bucket_key_str,
                    "total": 0,
                    "errors": 0,
                    "avg_duration_ms": 0,
                    "durations": [],
                }

            buckets[bucket_key_str]["total"] += 1
            if is_error:
                buckets[bucket_key_str]["errors"] += 1
            if duration_ms is not None:
                buckets[bucket_key_str]["durations"].append(duration_ms)

        # Calcula médias
        for b in buckets.values():
            if b["durations"]:
                b["avg_duration_ms"] = round(sum(b["durations"]) / len(b["durations"]), 2)
            del b["durations"]

        return sorted(buckets.values(), key=lambda x: x["timestamp"])


@router.get("/dashboard/tokens/distribution")
async def get_tokens_distribution(hours: int = Query(default=24)):
    """
    Retorna distribuição de tokens por agente e modelo.
    """
    async with get_db_session() as db:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Por agente
        agent_q = (
            select(
                Session.agent_name,
                func.coalesce(func.sum(Session.tokens_input), 0),
                func.coalesce(func.sum(Session.tokens_output), 0),
                func.count(Session.id),
            )
            .where(Session.started_at >= since)
            .group_by(Session.agent_name)
        )
        agent_rows = (await db.execute(agent_q)).all()

        return {
            "by_agent": [
                {
                    "agent": row[0],
                    "tokens_input": int(row[1]),
                    "tokens_output": int(row[2]),
                    "total": int(row[1] + row[2]),
                    "sessions": row[3],
                }
                for row in agent_rows
            ],
        }


# =====================================================
# HARNESS DASHBOARD
# =====================================================

@router.get("/dashboard/harness")
async def get_harness_metrics():
    """
    Retorna métricas do Harness Kothar v4.0.
    Inclui:
    - Circuit breakers status
    - Lock counts
    - Blueprint executions
    """
    result = {
        "circuit_breakers": CircuitBreakerRegistry.get_all_status(),
        "locks_active": 0,
        "blueprints_pending": 0,
        "blueprints_running": 0,
        "blueprints_completed": 0,
    }

    # Locks ativos do banco
    async with get_db_session() as db:
        from sqlalchemy import func
        locks_q = select(func.count(Lock.id)).where(Lock.is_active == True)
        result["locks_active"] = (await db.execute(locks_q)).scalar() or 0

        # Blueprints por status
        pending_q = select(func.count(Blueprint.id)).where(Blueprint.status == "pending")
        result["blueprints_pending"] = (await db.execute(pending_q)).scalar() or 0

        running_q = select(func.count(Blueprint.id)).where(Blueprint.status == "active")
        result["blueprints_running"] = (await db.execute(running_q)).scalar() or 0

        completed_q = select(func.count(Blueprint.id)).where(Blueprint.status.in_(["completed", "done"]))
        result["blueprints_completed"] = (await db.execute(completed_q)).scalar() or 0

    return result


# =====================================================
# HELPERS
# =====================================================

def _sess_to_dict(s: Session) -> dict:
    """Converte Session para dict."""
    duration = None
    if s.ended_at and s.started_at:
        duration = (s.ended_at - s.started_at).total_seconds()

    return {
        "id": str(s.id),
        "agent_name": s.agent_name,
        "llm_model": s.llm_model,
        "task_summary": s.task_summary,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "duration_seconds": duration,
        "tokens_input": s.tokens_input or 0,
        "tokens_output": s.tokens_output or 0,
        "total_cost_usd": float(s.total_cost_usd or 0),
        "metadata": s.metadata_ or {},
    }


def _bp_to_dict(bp: Blueprint) -> dict:
    """Converte Blueprint para dict."""
    return {
        "id": str(bp.id),
        "session_id": str(bp.session_id) if bp.session_id else None,
        "title": bp.title,
        "description": bp.description,
        "steps_count": len(bp.steps or []),
        "status": bp.status,
        "assigned_agent": bp.assigned_agent,
        "started_at": bp.started_at.isoformat() if bp.started_at else None,
        "completed_at": bp.completed_at.isoformat() if bp.completed_at else None,
        "created_at": bp.created_at.isoformat() if bp.created_at else None,
    }


async def _get_health_status() -> dict:
    """Verifica status dos componentes."""
    health = {
        "overall": "healthy",
        "components": {},
    }

    try:
        # Postgres
        from sqlalchemy import text
        async with get_db_session() as db:
            await db.execute(text("SELECT 1"))
        health["components"]["postgres"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        health["components"]["postgres"] = {"status": "unhealthy", "error": str(e)[:100]}
        health["overall"] = "degraded"

    try:
        # Redis
        from backend.memory.cache.redis_client import RedisMemory
        redis = RedisMemory()
        client = await redis._client()
        await client.ping()
        health["components"]["redis"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        health["components"]["redis"] = {"status": "unhealthy", "error": str(e)[:100]}
        health["overall"] = "degraded"

    try:
        # ChromaDB
        import httpx
        from backend.core.config import settings
        chroma_url = f"http://{settings.chroma_host}:{settings.chroma_port}"
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{chroma_url}/api/v2/heartbeat",
                timeout=2
            )
            if r.status_code == 200:
                health["components"]["chromadb"] = {"status": "healthy"}
            else:
                health["components"]["chromadb"] = {"status": "degraded"}
                health["overall"] = "degraded"
    except Exception as e:
        health["components"]["chromadb"] = {"status": "unhealthy", "error": str(e)[:100]}
        health["overall"] = "degraded"

    try:
        # Neo4j
        from backend.core.database import get_neo4j_driver
        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run("RETURN 1")
        health["components"]["neo4j"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["neo4j"] = {"status": "unhealthy", "error": str(e)[:100]}
        health["overall"] = "degraded"

    return health
