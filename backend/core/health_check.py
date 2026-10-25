"""
=============================================================
 KOTHAR v5.0 — Health Checks Avançados
 Verifica saúde de todos os componentes do sistema
=============================================================
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from backend.core.logger import get_logger

log = get_logger("health.checks")


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Resultado do health check de um componente."""

    def __init__(
        self,
        component: str,
        status: HealthStatus,
        latency_ms: float,
        message: str = "",
        details: dict = None,
    ):
        self.component = component
        self.status = status
        self.latency_ms = latency_ms
        self.message = message
        self.details = details or {}
        self.checked_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }


class HealthChecker:
    """
    Verificador de saúde do sistema.
    Checka todos os componentes e retorna status geral.
    """

    def __init__(self):
        self._cache: dict[str, ComponentHealth] = {}
        self._cache_ttl: int = 5  # segundos
        self._last_check: dict[str, float] = {}

    async def check_postgres(self) -> ComponentHealth:
        """Verifica PostgreSQL."""
        start = time.time()
        try:
            from backend.core.database import get_db_session
            from sqlalchemy import text

            async with get_db_session() as db:
                result = await db.execute(text("SELECT 1"))
                result.scalar()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                component="postgres",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="PostgreSQL respondendo",
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            log.error(f"PostgreSQL unhealthy: {e}")
            return ComponentHealth(
                component="postgres",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e)[:100],
            )

    async def check_redis(self) -> ComponentHealth:
        """Verifica Redis."""
        start = time.time()
        try:
            from backend.memory.cache.redis_client import RedisMemory

            redis = RedisMemory()
            client = await redis._client()
            await client.ping()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                component="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Redis respondendo",
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            log.error(f"Redis unhealthy: {e}")
            return ComponentHealth(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e)[:100],
            )

    async def check_chromadb(self) -> ComponentHealth:
        """Verifica ChromaDB."""
        start = time.time()
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # ChromaDB v2 API (v1 está deprecated e retorna 410)
                response = await client.get(
                    "http://kothar_chromadb:8000/api/v2/heartbeat", timeout=5
                )
                if response.status_code == 200:
                    latency = (time.time() - start) * 1000
                    return ComponentHealth(
                        component="chromadb",
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        message="ChromaDB respondendo",
                    )
                else:
                    raise Exception(f"Status {response.status_code}")

        except Exception as e:
            latency = (time.time() - start) * 1000
            log.error(f"ChromaDB unhealthy: {e}")
            return ComponentHealth(
                component="chromadb",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e)[:100],
            )

    async def check_neo4j(self) -> ComponentHealth:
        """Verifica Neo4j."""
        start = time.time()
        try:
            from backend.core.database import get_neo4j_driver

            driver = get_neo4j_driver()
            async with driver.session() as session:
                result = await session.run("RETURN 1 as n")
                await result.single()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                component="neo4j",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Neo4j respondendo",
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            log.error(f"Neo4j unhealthy: {e}")
            return ComponentHealth(
                component="neo4j",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e)[:100],
            )

    async def check_api(self) -> ComponentHealth:
        """Verifica própria API."""
        start = time.time()
        # Simula auto-check
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            component="api",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            message="API operacional",
            details={"version": "5.0.0"},
        )

    async def check_all(self, use_cache: bool = True) -> dict:
        """
        Executa health check de todos os componentes.
        Retorna status geral e detalhes.
        """
        # Verifica cache
        if use_cache:
            now = time.time()
            cached_results = {}
            all_cached = True
            for component in ["postgres", "redis", "chromadb", "neo4j", "api"]:
                if (
                    component in self._cache
                    and component in self._last_check
                    and now - self._last_check[component] < self._cache_ttl
                ):
                    cached_results[component] = self._cache[component]
                else:
                    all_cached = False

            if all_cached and cached_results:
                return self._compute_overall_status(cached_results)

        # Executa checks
        checks = {
            "postgres": self.check_postgres(),
            "redis": self.check_redis(),
            "chromadb": self.check_chromadb(),
            "neo4j": self.check_neo4j(),
            "api": self.check_api(),
        }

        results = {}
        for component, check_coro in checks.items():
            result = await check_coro
            results[component] = result
            self._cache[component] = result
            self._last_check[component] = time.time()

        return self._compute_overall_status(results)

    def _compute_overall_status(self, results: dict) -> dict:
        """Calcula status geral baseado nos componentes."""
        statuses = [r.status for r in results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        return {
            "status": overall.value,
            "components": {k: v.to_dict() for k, v in results.items()},
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


# Instância global
health_checker = HealthChecker()
