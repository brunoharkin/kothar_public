"""
=============================================================
 KOTHAR v5.0 — Métricas (Sem dependência Prometheus)
 Alternativa simples que não requer prometheus_client
=============================================================
"""

import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Response

# ============================================================
# STORE DE MÉTRICAS (thread-safe)
# ============================================================

class MetricsStore:
    _lock = threading.Lock()
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.trace_events = defaultdict(int)
        self.sessions_started = 0
        self.sessions_completed = 0
        self.sessions_failed = 0
        self.agents_executed = defaultdict(int)
        self.started_at = datetime.now(timezone.utc)

    def inc_trace(self, event_type: str, agent_name: str):
        with self._lock:
            key = f"{event_type}:{agent_name}"
            self.trace_events[key] += 1

    def inc_session(self, status: str):
        with self._lock:
            if status == "completed":
                self.sessions_completed += 1
            elif status == "failed":
                self.sessions_failed += 1
            else:
                self.sessions_started += 1

    def inc_agent(self, agent_name: str, status: str):
        with self._lock:
            key = f"{agent_name}:{status}"
            self.agents_executed[key] += 1

    def get_metrics(self) -> dict:
        with self._lock:
            uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()
            return {
                "uptime_seconds": uptime,
                "sessions": {
                    "started": self.sessions_started,
                    "completed": self.sessions_completed,
                    "failed": self.sessions_failed,
                },
                "trace_events": dict(self.trace_events),
                "agents_executed": dict(self.agents_executed),
            }

# Instância global
_store = MetricsStore()

# ============================================================
# HELPERS
# ============================================================

def record_trace(event_type: str, agent_name: str, duration_ms: float = None):
    """Registra um evento de trace."""
    _store.inc_trace(event_type, agent_name)

def record_session(status: str):
    """Registra uma sessão."""
    _store.inc_session(status)

def record_agent(agent_name: str, status: str, duration_ms: float = None):
    """Registra execução de agente."""
    _store.inc_agent(agent_name, status)

def get_metrics() -> dict:
    """Retorna métricas atuais."""
    return _store.get_metrics()

def set_active_sessions(count: int):
    """Define número de sessões ativas (placeholder)."""
    pass

# ============================================================
# ROUTER
# ============================================================

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """
    Endpoint de métricas no formato Prometheus-like.
    Compatível com Prometheus e outros scrapers.
    """
    data = _store.get_metrics()

    # Formato Prometheus text
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
        "# HELP kothar_sessions_failed Total de sessões com falha",
        "# TYPE kothar_sessions_failed counter",
        f"kothar_sessions_failed {data['sessions']['failed']}",
        "",
        "# HELP kothar_trace_events_total Total de eventos de trace",
        "# TYPE kothar_trace_events_total counter",
    ]

    for key, count in data["trace_events"].items():
        event_type, agent = key.split(":", 1)
        lines.append(f'kothar_trace_events_total{{event_type="{event_type}",agent_name="{agent}"}} {count}')

    lines.extend([
        "",
        "# HELP kothar_agents_executed_total Total de agentes executados",
        "# TYPE kothar_agents_executed_total counter",
    ])

    for key, count in data["agents_executed"].items():
        agent_name, status = key.split(":", 1)
        lines.append(f'kothar_agents_executed_total{{agent_name="{agent_name}",status="{status}"}} {count}')

    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4")


@router.get("/metrics/json")
async def metrics_json():
    """Endpoint de métricas em JSON para debugging."""
    return _store.get_metrics()
