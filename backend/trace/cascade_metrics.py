"""
=============================================================
 KOTHAR v4.0 — Cascade Metrics
 Tracking de uso do sistema multi-modelo.
=============================================================
"""

import threading
from collections import defaultdict
from datetime import datetime, timezone

# =====================================================
# Store de métricas de cascade
# =====================================================

class CascadeMetricsStore:
    """Thread-safe singleton para métricas de multi-modelo."""

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
        self._lock = threading.Lock()
        self.models_used: dict[str, int] = defaultdict(int)  # haiku/sonnet/opus
        self.escalations: int = 0
        self.escalations_by_path: dict[str, int] = defaultdict(int)  # haiku→sonnet, sonnet→opus
        self.tokens_by_model: dict[str, int] = defaultdict(int)
        self.cost_by_model: dict[str, float] = defaultdict(float)
        self.total_executions: int = 0
        self.started_at = datetime.now(timezone.utc)

        # Histórico para gráficos
        self.history: list[dict] = []  # {timestamp, model, tokens}

    def record_execution(
        self,
        model: str,
        tokens: int = 0,
        escalated: bool = False,
        from_model: str | None = None,
    ):
        """Registra uma execução de modelo."""
        with self._lock:
            self.models_used[model] += 1
            self.tokens_by_model[model] += tokens
            self.total_executions += 1

            # Custos estimados (relativos)
            cost_per_token = {"haiku": 0.000001, "sonnet": 0.000003, "opus": 0.000015}
            self.cost_by_model[model] += tokens * cost_per_token.get(model, 0)

            if escalated and from_model:
                path = f"{from_model}→{model}"
                self.escalations_by_path[path] += 1
                self.escalations += 1

            # Mantém histórico limitado
            self.history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "tokens": tokens,
                "escalated": escalated,
            })
            self.history = self.history[-1000:]  # Últimas 1000

    def get_metrics(self) -> dict:
        """Retorna métricas atuais."""
        with self._lock:
            total = self.total_executions
            distribution = {}
            if total > 0:
                for model, count in self.models_used.items():
                    distribution[model] = {
                        "count": count,
                        "percent": round(count / total * 100, 2),
                    }

            return {
                "total_executions": total,
                "models_used": dict(self.models_used),
                "distribution": distribution,
                "escalations": self.escalations,
                "escalations_by_path": dict(self.escalations_by_path),
                "tokens_by_model": dict(self.tokens_by_model),
                "cost_by_model": {k: round(v, 6) for k, v in self.cost_by_model.items()},
                "total_cost_usd": round(sum(self.cost_by_model.values()), 6),
                "escalation_rate_percent": round(
                    self.escalations / total * 100, 2
                ) if total > 0 else 0,
                "uptime_seconds": (
                    datetime.now(timezone.utc) - self.started_at
                ).total_seconds(),
            }

    def reset(self):
        """Reset para testes."""
        with self._lock:
            self.models_used.clear()
            self.escalations = 0
            self.escalations_by_path.clear()
            self.tokens_by_model.clear()
            self.cost_by_model.clear()
            self.total_executions = 0
            self.history.clear()
            self.started_at = datetime.now(timezone.utc)


# Singleton
_store = CascadeMetricsStore()


# =====================================================
# Public API
# =====================================================

def record_cascade_execution(
    model: str,
    tokens: int = 0,
    escalated: bool = False,
    from_model: str | None = None,
):
    """Registra uma execução."""
    _store.record_execution(model, tokens, escalated, from_model)


def get_cascade_metrics() -> dict:
    """Retorna métricas atuais."""
    return _store.get_metrics()
