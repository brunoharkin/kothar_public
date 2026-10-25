"""
=============================================================
 KOTHAR v5.0 — RAG Metrics (Hit/Miss Tracking)
=============================================================
 Thread-safe metrics store for RAG hit/miss tracking.
 Supports Prometheus format export.
"""

import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Response

# ============================================================
# TYPES
# ============================================================

QueryType = Literal["skill", "lock", "hyde", "cache"]


# ============================================================
# RAG METRICS STORE (thread-safe singleton)
# ============================================================

class RAGMetricsStore:
    """Thread-safe singleton store for RAG metrics."""

    _lock = threading.Lock()
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        """Initialize counters and state."""
        self._lock = threading.Lock()
        self.rag_hits = 0
        self.rag_misses = 0
        self.rag_cache_hits = 0
        self._hits_by_type: dict[QueryType, int] = defaultdict(int)
        self._misses_by_type: dict[QueryType, int] = defaultdict(int)
        self.started_at = datetime.now(timezone.utc)

    def record_hit(self, query_type: QueryType = "skill"):
        """Record a RAG hit."""
        with self._lock:
            self.rag_hits += 1
            self._hits_by_type[query_type] += 1

    def record_miss(self, query_type: QueryType = "skill"):
        """Record a RAG miss."""
        with self._lock:
            self.rag_misses += 1
            self._misses_by_type[query_type] += 1

    def record_cache_hit(self):
        """Record a cache hit."""
        with self._lock:
            self.rag_cache_hits += 1

    def get_metrics(self) -> dict:
        """Return all RAG metrics."""
        with self._lock:
            total = self.rag_hits + self.rag_misses
            hit_rate = (self.rag_hits / total * 100) if total > 0 else 0.0

            return {
                "total_hits": self.rag_hits,
                "total_misses": self.rag_misses,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_hits": self.rag_cache_hits,
                "hits_by_type": dict(self._hits_by_type),
                "misses_by_type": dict(self._misses_by_type),
                "uptime_seconds": (datetime.now(timezone.utc) - self.started_at).total_seconds(),
            }

    def reset(self):
        """Reset all counters (for testing)."""
        with self._lock:
            self.rag_hits = 0
            self.rag_misses = 0
            self.rag_cache_hits = 0
            self._hits_by_type.clear()
            self._misses_by_type.clear()


# Global singleton instance
_rag_store = RAGMetricsStore()


# ============================================================
# PUBLIC API
# ============================================================

def record_rag_hit(query_type: QueryType = "skill"):
    """Record a successful RAG lookup."""
    _rag_store.record_hit(query_type)


def record_rag_miss(query_type: QueryType = "skill"):
    """Record a failed RAG lookup."""
    _rag_store.record_miss(query_type)


def record_rag_cache_hit():
    """Record a cache hit."""
    _rag_store.record_cache_hit()


def get_rag_metrics() -> dict:
    """Get current RAG metrics."""
    return _rag_store.get_metrics()


# ============================================================
# FASTAPI ROUTER
# ============================================================

router = APIRouter()


@router.get("/rag")
async def rag_metrics():
    """
    Endpoint de métricas RAG no formato Prometheus.

    Métricas exportadas:
    - kothar_rag_hits_total: Total de hits de RAG
    - kothar_rag_misses_total: Total de misses de RAG
    - kothar_rag_hit_rate_percent: Taxa de acerto (%)
    - kothar_rag_cache_hits_total: Total de cache hits
    - kothar_rag_hits_by_type: Hits por tipo de query
    - kothar_rag_misses_by_type: Misses por tipo de query
    """
    data = get_rag_metrics()

    lines = [
        "# HELP kothar_rag_hits_total Total de RAG hits (resultados encontrados)",
        "# TYPE kothar_rag_hits_total counter",
        f"kothar_rag_hits_total {data['total_hits']}",
        "",
        "# HELP kothar_rag_misses_total Total de RAG misses (resultados não encontrados)",
        "# TYPE kothar_rag_misses_total counter",
        f"kothar_rag_misses_total {data['total_misses']}",
        "",
        "# HELP kothar_rag_hit_rate_percent Taxa de acerto RAG em percentual",
        "# TYPE kothar_rag_hit_rate_percent gauge",
        f"kothar_rag_hit_rate_percent {data['hit_rate_percent']}",
        "",
        "# HELP kothar_rag_cache_hits_total Total de cache hits",
        "# TYPE kothar_rag_cache_hits_total counter",
        f"kothar_rag_cache_hits_total {data['cache_hits']}",
        "",
        "# HELP kothar_rag_hits_by_type_total Hits por tipo de query",
        "# TYPE kothar_rag_hits_by_type_total counter",
    ]

    for qtype, count in data["hits_by_type"].items():
        lines.append(f'kothar_rag_hits_by_type_total{{query_type="{qtype}"}} {count}')

    lines.extend([
        "",
        "# HELP kothar_rag_misses_by_type_total Misses por tipo de query",
        "# TYPE kothar_rag_misses_by_type_total counter",
    ])

    for qtype, count in data["misses_by_type"].items():
        lines.append(f'kothar_rag_misses_by_type_total{{query_type="{qtype}"}} {count}')

    lines.extend([
        "",
        "# HELP kothar_rag_uptime_seconds Tempo de atividade do tracking",
        "# TYPE kothar_rag_uptime_seconds gauge",
        f"kothar_rag_uptime_seconds {data['uptime_seconds']:.2f}",
    ])

    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4")


@router.get("/rag/json")
async def rag_metrics_json():
    """Endpoint JSON para debugging e dashboards."""
    return get_rag_metrics()
