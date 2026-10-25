"""
=============================================================
 KOTHAR v5.0 — Timeouts Configuráveis
 Configuração centralizada de timeouts do sistema
=============================================================
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class TimeoutConfig:
    """Configuração de timeout para um componente."""

    default: float = 30.0  # segundos
    min: float = 1.0
    max: float = 300.0

    @property
    def value(self) -> float:
        return self.default

    def __post_init__(self):
        self.default = max(self.min, min(self.default, self.max))


@dataclass
class Timeouts:
    """
    Configuração centralizada de todos os timeouts do Kothar.
    Carrega de variáveis de ambiente com fallback para valores padrão.
    """

    # API timeouts
    api_request: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_API_REQUEST", "60"))
        )
    )
    api_shutdown: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_API_SHUTDOWN", "10"))
        )
    )

    # Database timeouts
    postgres_query: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_POSTGRES_QUERY", "30"))
        )
    )
    postgres_connection: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_POSTGRES_CONN", "10"))
        )
    )

    # Cache timeouts
    redis_operation: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_REDIS_OP", "5"))
        )
    )

    # External service timeouts
    chromadb_query: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_CHROMADB", "30"))
        )
    )
    neo4j_query: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_NEO4J", "30"))
        )
    )

    # Agent timeouts
    agent_execution: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_AGENT_EXEC", "300"))
        )
    )
    agent_idle: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_AGENT_IDLE", "60"))
        )
    )

    # MCP timeouts
    mcp_request: TimeoutConfig = field(
        default_factory=lambda: TimeoutConfig(
            default=float(os.getenv("KOTHAR_TIMEOUT_MCP_REQUEST", "30"))
        )
    )

    # Retry delays
    retry_base_delay: float = field(
        default=float(os.getenv("KOTHAR_RETRY_BASE_DELAY", "1.0"))
    )
    retry_max_delay: float = field(
        default=float(os.getenv("KOTHAR_RETRY_MAX_DELAY", "30.0"))
    )

    def to_dict(self) -> dict:
        """Converte para dicionário para serialização."""
        result = {}
        for name, config in self.__dataclass_fields__.items():
            value = getattr(self, name)
            if isinstance(value, TimeoutConfig):
                result[name] = {
                    "default": value.default,
                    "min": value.min,
                    "max": value.max,
                }
            else:
                result[name] = value
        return result

    def get(self, name: str) -> Optional[float]:
        """Obtém timeout por nome."""
        config = getattr(self, name, None)
        if isinstance(config, TimeoutConfig):
            return config.value
        return None

    def set(self, name: str, value: float) -> bool:
        """Define timeout por nome (runtime)."""
        config = getattr(self, name, None)
        if isinstance(config, TimeoutConfig):
            config.default = value
            return True
        return False


# Instância global com configuração
timeouts = Timeouts()


# ============================================================
# Decorators de timeout
# ============================================================

def with_timeout(timeout_name: str):
    """
    Decorator para aplicar timeout a uma função assíncrona.
    Uso:
        @with_timeout("postgres_query")
        async def my_query():
            ...
    """
    import asyncio
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            timeout_seconds = timeouts.get(timeout_name) or 30.0
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                from backend.core.exceptions import KotharTimeoutError

                raise KotharTimeoutError(
                    operation=func.__name__,
                    timeout_seconds=timeout_seconds,
                    component=timeout_name,
                )

        return wrapper

    return decorator


def retry_with_backoff(
    timeout_name: Optional[str] = None,
    max_retries: int = 3,
    exponential: bool = True,
):
    """
    Decorator para retry com backoff exponencial.
    Uso:
        @retry_with_backoff("redis_operation", max_retries=3)
        async def my_operation():
            ...
    """
    import asyncio
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    if timeout_name:
                        timeout = timeouts.get(timeout_name)
                        if timeout:
                            return await asyncio.wait_for(
                                func(*args, **kwargs), timeout=timeout
                            )
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = timeouts.retry_base_delay * (
                            2**attempt if exponential else 1
                        )
                        delay = min(delay, timeouts.retry_max_delay)
                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
