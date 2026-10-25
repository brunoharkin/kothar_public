"""
=============================================================
 KOTHAR v4.0 — Circuit Breaker (Resiliência)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Protege contra falhas em cascata de serviços externos.
 Estados: CLOSED (normal) -> OPEN (bloqueando) -> HALF_OPEN (testando)
"""

import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

from backend.core.logger import get_logger

log = get_logger("core.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"       # Normal, aceitando chamadas
    OPEN = "open"          # Bloqueando, falha recente
    HALF_OPEN = "half_open"  # Testando recuperação


F = TypeVar("F", bound=Callable[..., Any])


class CircuitBreakerOpen(Exception):
    """Exceção levantada quando o circuit breaker está aberto."""

    def __init__(self, name: str, remaining_time: float):
        self.name = name
        self.remaining_time = remaining_time
        super().__init__(
            f"Circuit breaker '{name}' está aberto. "
            f"Tente novamente em {remaining_time:.1f}s"
        )


class CircuitBreaker:
    """
    Circuit Breaker pattern para resiliência de serviços externos.

    Estados:
        CLOSED: Operation normal, falhas incrementam contador
        OPEN: Serviço falhou, bloqueando novas chamadas
        HALF_OPEN: Testando se o serviço recuperou

    Métricas expostas via atributos:
        - state: CircuitState atual
        - failure_count: Total de falhas desde último reset
        - circuit_state: Para compatibilidade com métricas
        - circuit_failure_count: Para compatibilidade com métricas
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 1,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED

        self._lock = asyncio.Lock()
        self._metrics_lock = asyncio.Lock()

    # Métricas para exposição (thread-safe para leitura)
    @property
    def circuit_state(self) -> str:
        """Estado atual do circuito (para métricas)."""
        return self.state.value

    @property
    def circuit_failure_count(self) -> int:
        """Contagem de falhas (para métricas)."""
        return self.failure_count

    @property
    def circuit_last_failure(self) -> float | None:
        """Timestamp da última falha."""
        return self.last_failure_time

    async def _should_allow_request(self) -> tuple[bool, float]:
        """
        Verifica se a requisição deve ser permitida.
        Retorna (permitida, tempo_restante_para_retry).
        """
        async with self._lock:
            now = time.monotonic()

            if self.state == CircuitState.CLOSED:
                return True, 0.0

            if self.state == CircuitState.OPEN:
                if self.last_failure_time is None:
                    return True, 0.0

                elapsed = now - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    log.info(
                        "Circuit breaker entrando em HALF_OPEN",
                        name=self.name,
                        elapsed=elapsed,
                    )
                    return True, 0.0
                return False, self.recovery_timeout - elapsed

            if self.state == CircuitState.HALF_OPEN:
                # Um estado HALF_OPEN sem falha registrada é inconsistente
                # (por exemplo, restauração manual); normalize o contador.
                if self.last_failure_time is None:
                    self.half_open_calls = 0
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True, 0.0
                return False, 0.0

            return True, 0.0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função com proteção do circuit breaker.

        Args:
            func: Função assíncrona a ser executada
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado da função

        Raises:
            CircuitBreakerOpen: Se o circuito está aberto
            Exception: Erro original se a função falhar
        """
        allowed, remaining = await self._should_allow_request()

        if not allowed:
            log.warning(
                "Circuit breaker bloqueando chamada",
                name=self.name,
                state=self.state.value,
                retry_after=remaining,
            )
            raise CircuitBreakerOpen(self.name, remaining)

        try:
            # Executa a função (pode ser sync ou async)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self.record_success()
            return result

        except self.expected_exception as e:
            self.record_failure()
            raise

    def record_success(self) -> None:
        """Registra sucesso e reseta o circuito se em HALF_OPEN."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # Em half_open, um sucesso fecha o circuito
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0
            log.info(
                "Circuit breaker fechou após sucesso em HALF_OPEN",
                name=self.name,
            )
        elif self.state == CircuitState.CLOSED:
            # Reset suave: apenas limpa contador
            pass

    def record_failure(self) -> None:
        """Registra falha e abre o circuito se limite atingido."""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()

        if self.state == CircuitState.HALF_OPEN:
            # Falha em half_open abre imediatamente
            self.state = CircuitState.OPEN
            log.warning(
                "Circuit breaker abriu após falha em HALF_OPEN",
                name=self.name,
            )

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                log.warning(
                    "Circuit breaker abriu",
                    name=self.name,
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold,
                )

    def reset(self) -> None:
        """Reseta manualmente o circuit breaker."""
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        log.info("Circuit breaker resetado manualmente", name=self.name)

    def get_status(self) -> dict[str, Any]:
        """Retorna status completo para debugging/métricas."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "half_open_calls": self.half_open_calls,
        }

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, "
            f"state={self.state.value}, "
            f"failures={self.failure_count}/{self.failure_threshold})"
        )


def circuit_breaker(
    name: str | None = None,
    failure_threshold: int = 3,
    recovery_timeout: int = 30,
    expected_exception: type = Exception,
) -> Callable[[F], F]:
    """
    Decorator para aplicar circuit breaker em funções assíncronas.

    Uso:
        @circuit_breaker("chroma", failure_threshold=3)
        async def busca_chroma(query):
            ...

        @circuit_breaker(name="neo4j")
        async def query_neo4j(cypher):
            ...

    Args:
        name: Nome do circuito (default: nome da função)
        failure_threshold: Número de falhas para abrir (default: 3)
        recovery_timeout: Segundos antes de testar recuperação (default: 30)
        expected_exception: Tipo de exceção que conta como falha (default: Exception)
    """
    def decorator(func: F) -> F:
        cb_name = name or func.__name__
        cb = CircuitBreaker(
            name=cb_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)

        # Expoe o circuit breaker para acesso externo
        wrapper.circuit_breaker = cb
        wrapper.__circuit_breaker__ = cb

        return wrapper  # type: ignore

    return decorator


# Instâncias globais para serviços do Kothar
_chroma_circuit: CircuitBreaker | None = None
_neo4j_circuit: CircuitBreaker | None = None


def get_chroma_circuit() -> CircuitBreaker:
    """Retorna (e cria se necessário) o circuit breaker do ChromaDB."""
    global _chroma_circuit
    if _chroma_circuit is None:
        _chroma_circuit = CircuitBreaker(
            name="chroma_db",
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception,
        )
    return _chroma_circuit


def get_neo4j_circuit() -> CircuitBreaker:
    """Retorna (e cria se necessário) o circuit breaker do Neo4j."""
    global _neo4j_circuit
    if _neo4j_circuit is None:
        _neo4j_circuit = CircuitBreaker(
            name="neo4j_db",
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception,
        )
    return _neo4j_circuit


def get_all_circuits() -> list[CircuitBreaker]:
    """Retorna todos os circuit breakers ativos."""
    circuits = []
    if _chroma_circuit is not None:
        circuits.append(_chroma_circuit)
    if _neo4j_circuit is not None:
        circuits.append(_neo4j_circuit)
    return circuits
