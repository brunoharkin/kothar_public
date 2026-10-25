"""
=============================================================
 KOTHAR v4.0 — Entry Point da API (FastAPI)
 Engenheiro Kothar | Ugarit Digital
=============================================================
"""

from contextlib import asynccontextmanager
import os
from backend.api.security import APISecurityMiddleware

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.database import close_databases, init_databases
from backend.core.exceptions import KotharError
from backend.core.logger import get_logger, setup_logging

# Importa routers
from backend.api.routers import health, sessions, traces, skills, orchestrate, cbm, cofre, rag_tracker, vault_inspector, heatmaps, locks, workspace_state
from backend.api.routers.ollama_proxy import router as ollama_proxy_router
from backend.api.routers.model_preview import router as model_preview_router
from backend.api.routers.dashboard import router as dashboard_router
from backend.api.routers.cascade_metrics import router as cascade_metrics_router
from backend.api.routers.flow import router as flow_router
from backend.api.routers.evolucao import router as evolution_router
from backend.trace.metrics import router as metrics_router
from backend.trace.rag_metrics import router as rag_metrics_router

# Hack de compat: backend/token_counter/ foi portado do Codenotch (módulo standalone)
# e usa imports absolutos `from token_counter.models` sem o prefixo `backend.`.
# Para o Python tratar `backend/token_counter/` como package `token_counter`,
# precisamos que o PAI (backend/) esteja no sys.path — não o próprio diretório.
# Sem isso, Python acha como namespace package e os imports absolutos quebram.
import sys as _sys
from pathlib import Path as _Path
_backend_dir = str((_Path(__file__).parent.parent).resolve())
if _backend_dir not in _sys.path:
    _sys.path.insert(0, _backend_dir)
from backend.token_counter.api import router as usage_router, setup_token_counter  # noqa: E402

from backend.trace.metrics import MetricsStore, record_trace, record_session, record_agent

setup_logging()
log = get_logger("api.main")


# =============================================================
# Lifecycle — startup / shutdown
# =============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "🎵 Engenheiro Kothar v4.0 — API iniciando...",
        version=settings.kothar_version,
        environment=settings.environment,
    )
    # Token counter: inicia polling adaptativo + registra ClaudeCLIProvider
    setup_token_counter()
    await init_databases()
    yield
    log.info("Encerrando API...")
    await close_databases()
    log.info("✅ API encerrada com segurança.")


# =============================================================
# Aplicação FastAPI
# =============================================================

app = FastAPI(
    title="Engenheiro Kothar API",
    description="API de Observabilidade e Orquestração do Kothar v4.0",
    version=settings.kothar_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get('CORS_ORIGIN', '').split(',') if origin.strip().startswith('https://')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(APISecurityMiddleware)

# --- Routers ---
app.include_router(health.router,      prefix="/health",          tags=["Health"])
app.include_router(metrics_router,    prefix="/metrics",        tags=["Metrics"])
app.include_router(rag_metrics_router, prefix="/api/rag-metrics",   tags=["RAG Metrics"])
app.include_router(sessions.router,    prefix="/api/sessions",    tags=["Sessions"])
app.include_router(traces.router,      prefix="/api/traces",      tags=["Traces"])
app.include_router(skills.router,      prefix="/api/skills",      tags=["Skills"])
app.include_router(orchestrate.router, prefix="/api/orchestrate", tags=["Orchestrate"])
app.include_router(model_preview_router, prefix="/api", tags=["Model-Preview"])
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(cascade_metrics_router, prefix="/api/metrics", tags=["Cascade-Metrics"])
app.include_router(locks.router, prefix="/api/locks", tags=["Locks"])
app.include_router(cbm.router,        prefix="/api",             tags=["Codebase-Memory"])
app.include_router(ollama_proxy_router, prefix="/api/ollama",    tags=["Ollama-Proxy"])
app.include_router(cofre.router,       prefix="/api/cofre",      tags=["Cofre"])
app.include_router(rag_tracker.router, prefix="/api/rag-tracker", tags=["RAG-Tracker"])
app.include_router(vault_inspector.router, prefix="/api/inspector", tags=["Vault-Inspector"])
app.include_router(heatmaps.router,    prefix="/api/heatmaps",    tags=["Heatmaps"])
app.include_router(flow_router,       prefix="/api/flow",         tags=["Flow"])
app.include_router(workspace_state.router, prefix="/api/workspace-state", tags=["Workspace-State"])
app.include_router(evolution_router, prefix="/api/evolucao", tags=["Evolução"])
app.include_router(usage_router,      tags=["Token-Usage"])

# --- Métricas endpoint ---
_metrics_store = MetricsStore()
_rag_metrics_store = None  # lazy load

def get_rag_metrics_store():
    global _rag_metrics_store
    if _rag_metrics_store is None:
        try:
            from backend.trace.rag_metrics import MetricsStore as RAGMetricsStore
            _rag_metrics_store = RAGMetricsStore()
        except ImportError:
            # Se não existir, retorna store vazio
            class EmptyStore:
                def get_metrics(self):
                    return {"total_hits": 0, "total_misses": 0, "hit_rate": 0.0, "by_type": {}}
            _rag_metrics_store = EmptyStore()
    return _rag_metrics_store

@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Endpoint de métricas no formato Prometheus."""
    data = _metrics_store.get_metrics()
    lines = [
        "# HELP kothar_uptime_seconds Tempo de atividade do serviço",
        "# TYPE kothar_uptime_seconds gauge",
        f"kothar_uptime_seconds {data['uptime_seconds']:.2f}",
        "",
        "# HELP kothar_sessions_started Total de sessões iniciadas",
        "# TYPE kothar_sessions_started counter",
        f"kothar_sessions_started {data['sessions']['started']}",
        "",
        "# HELP kothar_sessions_completed Total de sessões concluídas",
        "# TYPE kothar_sessions_completed counter",
        f"kothar_sessions_completed {data['sessions']['completed']}",
        "",
        "# HELP kothar_trace_events_total Total de eventos de trace",
        "# TYPE kothar_trace_events_total counter",
    ]
    for key, count in data["trace_events"].items():
        event_type, agent = key.split(":", 1)
        lines.append(f'kothar_trace_events_total{{event_type="{event_type}",agent_name="{agent}"}} {count}')
    content = "\n".join(lines)
    return Response(content=content, media_type="text/plain")

@app.get("/metrics/json", tags=["Metrics"])
async def metrics_json():
    """Endpoint de métricas em JSON."""
    return _metrics_store.get_metrics()

@app.get("/metrics/rag", tags=["Metrics"])
async def metrics_rag():
    """Endpoint de métricas RAG (hit/miss) - lê do tracker que está populado."""
    try:
        from backend.api.routers.rag_tracker import tracker
        queries = tracker.get_recent(limit=1000)
        total_hits = sum(1 for q in queries if q.get("is_hit"))
        total_misses = sum(1 for q in queries if not q.get("is_hit"))
        total_chunks = sum(q.get("chunks_count", 0) for q in queries)
        total = total_hits + total_misses
        hit_rate = round(total_hits / total * 100, 1) / 100 if total > 0 else 0.0
        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_chunks_retrieved": total_chunks,
            "hit_rate": hit_rate,
            "by_type": {"tracker": total_hits} if total_hits > 0 else {},
            "source": "rag_tracker"
        }
    except Exception as e:
        return {"error": str(e), "total_hits": 0, "total_misses": 0, "hit_rate": 0.0}

@app.get("/metrics/rag/prometheus", tags=["Metrics"])
async def metrics_rag_prometheus():
    """Endpoint de métricas RAG em formato Prometheus."""
    store = get_rag_metrics_store()
    data = store.get_metrics()
    lines = [
        "# HELP kothar_rag_hits_total Total de hits do RAG",
        "# TYPE kothar_rag_hits_total counter",
        f"kothar_rag_hits_total {data['total_hits']}",
        "",
        "# HELP kothar_rag_misses_total Total de misses do RAG",
        "# TYPE kothar_rag_misses_total counter",
        f"kothar_rag_misses_total {data['total_misses']}",
        "",
        "# HELP kothar_rag_hit_rate Taxa de acerto do RAG",
        "# TYPE kothar_rag_hit_rate gauge",
        f"kothar_rag_hit_rate {data['hit_rate']:.2f}",
    ]
    return Response(content="\n".join(lines), media_type="text/plain")

# --- Health Check endpoint ---
_health_checker = None  # lazy load

def get_health_checker():
    global _health_checker
    if _health_checker is None:
        from backend.core.health_check import health_checker as hc
        _health_checker = hc
    return _health_checker

@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """Health check detalhado de todos os componentes."""
    checker = get_health_checker()
    return await checker.check_all()


# --- Handler global de erros ---
@app.exception_handler(KotharError)
async def kothar_error_handler(request: Request, exc: KotharError):
    log.error("Erro Kothar", error=str(exc), context=exc.context, path=request.url.path)
    status_code = getattr(exc, "http_status", 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": "Não foi possível concluir a operação."},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    log.exception("Erro inesperado", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Erro interno do servidor. Verifique os logs."},
    )


# =============================================================
# Dev runner
# =============================================================

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
