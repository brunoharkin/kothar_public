"""
=============================================================
 KOTHAR v4.0 — Circuit Breaker
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Protege o fluxo contra falhas em cascata.
 Se um agente falha N vezes, ele é bloqueado temporariamente.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from backend.core.logger import get_logger

log = get_logger("harness.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Bloqueado - falhando muito
    HALF_OPEN = "half_open"  # Testando recuperação


@dataclass
class CircuitBreakerConfig:
    """Configuração por agente."""
    failures_threshold: int = 3      # Falhas antes de abrir
    success_threshold: int = 2        # Sucessos para fechar
    open_duration_seconds: float = 60  # Tempo bloqueado
    half_open_max_calls: int = 3      # Chamadas permitidas no teste


@dataclass
class CircuitBreakerState:
    """Estado interno do circuit breaker."""
    failures: int = 0
    successes: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: float = 0.0
    half_open_calls: int = 0


# Configuração global de circuit breakers por agente
AGENT_CONFIGS: dict[str, CircuitBreakerConfig] = {
    "qa": CircuitBreakerConfig(failures_threshold=2, open_duration_seconds=120),
    "security": CircuitBreakerConfig(failures_threshold=2, open_duration_seconds=90),
    "frontend_engineer": CircuitBreakerConfig(failures_threshold=3),
    "backend_engineer": CircuitBreakerConfig(failures_threshold=3),
    "supervisor_agent": CircuitBreakerConfig(failures_threshold=3),
    "code_reviewer": CircuitBreakerConfig(failures_threshold=2),
    # Agentes de escrita/agência são mais tolerantes
    "copywriter": CircuitBreakerConfig(failures_threshold=5),
    "architect": CircuitBreakerConfig(failures_threshold=4),
}


class CircuitBreaker:
    """
    Circuit Breaker para agentes do Kothar.

    Fluxo de estados:

        CLOSED ──► OPEN ──► HALF_OPEN ──► CLOSED
           ▲                      │
           │                      │
           └──────────────────────┘
           (sucesso no half_open)

    CLOSED: Funciona normalmente
    OPEN: Bloqueado por N segundos
    HALF_OPEN: Permite teste de recuperação
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.config = AGENT_CONFIGS.get(agent_name, CircuitBreakerConfig())
        self._state = CircuitBreakerState()

    @property
    def state(self) -> CircuitState:
        """Retorna estado atual, verificando se deve transicionar."""
        self._check_transition()
        return self._state.state

    def _check_transition(self) -> None:
        """Verifica se deve transitar de estado."""
        if self._state.state == CircuitState.OPEN:
            elapsed = time.time() - self._state.last_failure_time
            if elapsed >= self.config.open_duration_seconds:
                log.info(f"Circuit Breaker '{self.agent_name}': OPEN -> HALF_OPEN")
                self._state.state = CircuitState.HALF_OPEN
                self._state.half_open_calls = 0
                self._state.failures = 0

    def is_available(self) -> bool:
        """Verifica se o agente pode executar."""
        state = self.state

        if state == CircuitState.CLOSED:
            return True

        if state == CircuitState.OPEN:
            return False

        if state == CircuitState.HALF_OPEN:
            return self._state.half_open_calls < self.config.half_open_max_calls

        return False

    async def execute(self, func, *args, **kwargs):
        """
        Executa uma função com circuit breaker.
        Raises CircuitBreakerOpen if blocked.
        """
        if not self.is_available():
            raise CircuitBreakerOpen(
                f"Circuit Breaker '{self.agent_name}' está OPEN. "
                f"Última falha há {time.time() - self._state.last_failure_time:.0f}s. "
                f"Tente novamente em {self.config.open_duration_seconds}s."
            )

        try:
            # Incrementa chamadas no half_open
            if self._state.state == CircuitState.HALF_OPEN:
                self._state.half_open_calls += 1

            # Executa
            result = await func(*args, **kwargs)

            # Sucesso
            self._on_success()
            return result

        except Exception as e:
            # Falha
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Callback de sucesso."""
        if self._state.state == CircuitState.HALF_OPEN:
            self._state.successes += 1
            if self._state.successes >= self.config.success_threshold:
                log.info(f"Circuit Breaker '{self.agent_name}': HALF_OPEN -> CLOSED")
                self._state.state = CircuitState.CLOSED
                self._state.successes = 0
                self._state.failures = 0
        elif self._state.state == CircuitState.CLOSED:
            # Reset contador no CLOSED após sucessos
            if self._state.failures > 0:
                self._state.failures = max(0, self._state.failures - 1)

    def _on_failure(self) -> None:
        """Callback de falha."""
        self._state.failures += 1
        self._state.last_failure_time = time.time()

        if self._state.state == CircuitState.HALF_OPEN:
            # Falhou no teste - volta pro OPEN
            log.warn(f"Circuit Breaker '{self.agent_name}': HALF_OPEN -> OPEN (falhou)")
            self._state.state = CircuitState.OPEN
            self._state.successes = 0
            self._state.half_open_calls = 0

        elif self._state.state == CircuitState.CLOSED:
            if self._state.failures >= self.config.failures_threshold:
                log.warn(
                    f"Circuit Breaker '{self.agent_name}': CLOSED -> OPEN "
                    f"(falhas: {self._state.failures})"
                )
                self._state.state = CircuitState.OPEN

    def get_status(self) -> dict:
        """Retorna status do circuit breaker."""
        return {
            "agent": self.agent_name,
            "state": self.state.value,
            "failures": self._state.failures,
            "successes": self._state.successes,
            "config": {
                "failures_threshold": self.config.failures_threshold,
                "open_duration_seconds": self.config.open_duration_seconds,
            },
            "last_failure_ago_seconds": time.time() - self._state.last_failure_time if self._state.last_failure_time else None,
        }


class CircuitBreakerOpen(Exception):
    """Exceção lançada quando circuit breaker está aberto."""
    pass


class CircuitBreakerRegistry:
    """
    Registro global de circuit breakers.
    Garante que cada agente tenha apenas um circuit breaker.
    """

    _breakers: dict[str, CircuitBreaker] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls, agent_name: str) -> CircuitBreaker:
        """Obtém ou cria circuit breaker para o agente."""
        async with cls._lock:
            if agent_name not in cls._breakers:
                cls._breakers[agent_name] = CircuitBreaker(agent_name)
            return cls._breakers[agent_name]

    @classmethod
    def get_all_status(cls) -> list[dict]:
        """Retorna status de todos os circuit breakers."""
        return [cb.get_status() for cb in cls._breakers.values()]

    @classmethod
    def reset(cls, agent_name: str = None) -> None:
        """Reseta circuit breaker(s)."""
        if agent_name:
            if agent_name in cls._breakers:
                cls._breakers[agent_name] = CircuitBreaker(agent_name)
        else:
            cls._breakers.clear()
