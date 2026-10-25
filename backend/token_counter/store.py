"""
UsageStore - Gerenciador Central de Dados de Uso
=================================================

Inspirado em UsageStore.swift do Codenotch.

Este módulo implementa o store central que:
1. Mantém snapshots de cada provedor
2. Faz polling adaptativo (ativo/idle)
3. Implementa decadência gradual em falhas
4. Protege contra condições de corrida (generation counters)
5. Persiste última leitura válida
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
import json
import os
from pathlib import Path

from token_counter.models import (
    Fidelity,
    ProviderSnapshot,
    ProviderStatus,
)
from token_counter.providers.base import (
    BaseUsageProvider,
    UsageProviderError,
)


logger = logging.getLogger(__name__)


@dataclass
class StoreConfig:
    """Configuração do UsageStore."""
    # Intervalo quando ativo (segundos)
    refresh_interval: int = 60

    # Intervalo quando idle (segundos)
    idle_refresh_interval: int = 300  # 5 minutos

    # Timeout para cada fetch individual (segundos)
    deadline: int = 60

    # Minutos após os quais dados são considerados stale
    stale_threshold_minutes: int = 15

    # Arquivo para persistência
    persistence_path: str = "~/.kothar/token-usage/last-good.json"


@dataclass
class ProviderState:
    """Estado interno de um provedor no store."""
    provider: BaseUsageProvider
    snapshot: Optional[ProviderSnapshot] = None
    last_good: Optional[ProviderSnapshot] = None
    last_attempt: Optional[datetime] = None
    generation: int = 0  # Contador de geração para condições de corrida
    is_refreshing: bool = False
    error_count: int = 0


class UsageStore:
    """
    Store central para dados de uso de múltiplos provedores.

    Inspirado em UsageStore.swift do Codenotch.

    Padrão Publisher/Store:
    - Mantém snapshots em @Published properties
    - Implementa polling adaptativo
    - Faz decadência gradual em falhas
    - Protege contra condições de corrida

    Uso:
        store = UsageStore()

        # Registrar providers
        store.register(ClaudeCLIProvider())

        # Iniciar polling
        await store.start()

        # Obter snapshot
        snapshot = store.get_snapshot("claude-cli")
    """

    def __init__(self, config: Optional[StoreConfig] = None):
        self.config = config or StoreConfig()
        self._providers: dict[str, ProviderState] = {}
        self._is_running = False
        self._refresh_task: Optional[asyncio.Task] = None
        self._listeners: list[Callable[[str, ProviderSnapshot], None]] = []

        # Persistência
        self._persistence_path = Path(
            os.path.expanduser(self.config.persistence_path)
        )
        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)

        # Carrega último bom estado
        self._load_last_good()

    def register(self, provider: BaseUsageProvider) -> None:
        """
        Registra um provedor no store.

        Args:
            provider: Implementação de UsageProvider
        """
        state = ProviderState(provider=provider)
        self._providers[provider.id] = state
        logger.info(f"Registered provider: {provider.id}")

    def unregister(self, provider_id: str) -> None:
        """
        Remove um provedor do store.

        Args:
            provider_id: ID do provedor
        """
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info(f"Unregistered provider: {provider_id}")

    def get_provider(self, provider_id: str) -> Optional[BaseUsageProvider]:
        """Retorna o provider por ID."""
        state = self._providers.get(provider_id)
        return state.provider if state else None

    def get_snapshot(self, provider_id: str) -> Optional[ProviderSnapshot]:
        """
        Retorna o snapshot atual de um provedor.

        Se a última leitura foi bem-sucedida, retorna ela (potencialmente stale).
        Caso contrário, retorna None.
        """
        state = self._providers.get(provider_id)
        if not state:
            return None

        # Se está em refresh, retorna último bom ou None
        if state.is_refreshing:
            return state.last_good

        # Se tem snapshot atual, retorna ele
        if state.snapshot:
            return state.snapshot

        # Fallback para último bom
        return state.last_good

    def get_all_snapshots(self) -> dict[str, ProviderSnapshot]:
        """Retorna todos os snapshots disponíveis."""
        result = {}
        for provider_id, state in self._providers.items():
            snapshot = self.get_snapshot(provider_id)
            if snapshot:
                result[provider_id] = snapshot
        return result

    async def fetch(self, provider_id: str) -> Optional[ProviderSnapshot]:
        """
        Força um fetch imediato para um provedor.

        Args:
            provider_id: ID do provedor

        Returns:
            Snapshot atualizado ou None em caso de falha
        """
        state = self._providers.get(provider_id)
        if not state:
            return None

        # Incrementa geração para descartar respostas antigas
        state.generation += 1
        current_generation = state.generation
        state.last_attempt = datetime.now()

        try:
            snapshot = await asyncio.wait_for(
                state.provider.fetch_snapshot(),
                timeout=self.config.deadline,
            )

            # Descarta resposta se geração mudou
            if state.generation != current_generation:
                logger.debug(
                    f"Discarded stale response for {provider_id} "
                    f"(generation {current_generation} -> {state.generation})"
                )
                return None

            # Atualiza estado
            state.snapshot = snapshot
            state.last_good = snapshot
            state.error_count = 0
            state.is_refreshing = False

            # Salva último bom
            self._save_last_good(provider_id, snapshot)

            # Notifica listeners
            self._notify_listeners(provider_id, snapshot)

            logger.debug(f"Fetched snapshot for {provider_id}: {snapshot.status}")
            return snapshot

        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {provider_id}")
            state.is_refreshing = False
            await self._handle_fetch_error(state, UsageProviderError.timeout())

        except UsageProviderError as e:
            logger.warning(f"Provider error for {provider_id}: {e.code}")
            state.is_refreshing = False
            await self._handle_fetch_error(state, e)

        except Exception as e:
            logger.error(f"Unexpected error fetching {provider_id}: {e}")
            state.is_refreshing = False
            await self._handle_fetch_error(
                state,
                UsageProviderError.unknown(str(e)),
            )

        return None

    async def _handle_fetch_error(
        self,
        state: ProviderState,
        error: UsageProviderError,
    ) -> None:
        """
        Trata erro de fetch com decadência gradual.

        Estratégia:
        - needsAuth/unsupported: descarta cache
        - rateLimited/accessDenied: mantém cache
        - outros: mantém cache mas marca stale
        """
        state.error_count += 1

        error_code = error.code

        if error_code in [
            UsageProviderError.NEEDS_AUTH,
            UsageProviderError.UNSUPPORTED,
        ]:
            # Descarta cache para erros que tornam dados obsoletos
            if state.last_good:
                state.last_good.status = ProviderStatus.ERROR
                state.last_good.error_message = error.message

        elif error_code in [
            UsageProviderError.ACCESS_DENIED,
            UsageProviderError.RATE_LIMITED,
            UsageProviderError.CREDENTIAL_EXPIRED,
        ]:
            # Mantém cache para erros temporários/benignos
            pass

        else:
            # Para outros erros, marca como stale se tem dados
            if state.last_good:
                time_since = datetime.now() - (state.last_attempt or datetime.now())
                if time_since > timedelta(minutes=self.config.stale_threshold_minutes):
                    state.last_good.status = ProviderStatus.STALE

    async def start(self) -> None:
        """Inicia o polling de todos os providers."""
        if self._is_running:
            return

        self._is_running = True
        self._refresh_task = asyncio.create_task(self._poll_loop())
        logger.info("UsageStore started")

    async def stop(self) -> None:
        """Para o polling."""
        self._is_running = False

        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        logger.info("UsageStore stopped")

    async def _poll_loop(self) -> None:
        """
        Loop principal de polling.

        Intervalos adaptativos:
        - Ativo (algum fetch recente): 60s
        - Idle (sem fetches recentes): 5min
        """
        idle_threshold = timedelta(minutes=5)
        last_activity = datetime.now()
        interval = self.config.refresh_interval

        while self._is_running:
            # Verifica se está idle
            if datetime.now() - last_activity > idle_threshold:
                interval = self.config.idle_refresh_interval
            else:
                interval = self.config.refresh_interval

            try:
                # Fetch paralelo de todos os providers
                await asyncio.gather(
                    *[self.fetch(provider_id) for provider_id in self._providers],
                    return_exceptions=True,
                )

                last_activity = datetime.now()

            except Exception as e:
                logger.error(f"Error in poll loop: {e}")

            await asyncio.sleep(interval)

    def add_listener(
        self,
        callback: Callable[[str, ProviderSnapshot], None],
    ) -> None:
        """Adiciona listener para mudanças de snapshot."""
        self._listeners.append(callback)

    def remove_listener(
        self,
        callback: Callable[[str, ProviderSnapshot], None],
    ) -> None:
        """Remove listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, provider_id: str, snapshot: ProviderSnapshot) -> None:
        """Notifica todos os listeners de uma mudança."""
        for listener in self._listeners:
            try:
                listener(provider_id, snapshot)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    def _save_last_good(
        self,
        provider_id: str,
        snapshot: ProviderSnapshot,
    ) -> None:
        """Salva último snapshot válido em disco."""
        try:
            data = self._load_all_last_good()
            data[provider_id] = {
                "snapshot": snapshot.to_dict(),
                "saved_at": datetime.now().isoformat(),
            }
            with open(self._persistence_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save last good: {e}")

    def _load_all_last_good(self) -> dict:
        """Carrega todos os últimos bons do disco."""
        if not self._persistence_path.exists():
            return {}

        try:
            with open(self._persistence_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _load_last_good(self) -> None:
        """Carrega último bom para cada provider registrado."""
        data = self._load_all_last_good()

        for provider_id, entry in data.items():
            if provider_id in self._providers:
                try:
                    snapshot_dict = entry.get("snapshot", {})
                    # Reconstrói snapshot (simplificado)
                    self._providers[provider_id].last_good = ProviderSnapshot(
                        id=provider_id,
                        name=snapshot_dict.get("name", provider_id),
                        fidelity=Fidelity(snapshot_dict.get("fidelity", "official")),
                        status=ProviderStatus(snapshot_dict.get("status", "ok")),
                        error_message=snapshot_dict.get("error_message"),
                    )
                    logger.debug(f"Loaded last good for {provider_id}")
                except Exception:
                    pass

    def get_status_summary(self) -> dict:
        """Retorna resumo do status de todos os providers."""
        return {
            provider_id: {
                "status": state.snapshot.status.value if state.snapshot else "unknown",
                "last_attempt": (
                    state.last_attempt.isoformat()
                    if state.last_attempt else None
                ),
                "error_count": state.error_count,
                "is_refreshing": state.is_refreshing,
                "available": state.provider.is_available(),
            }
            for provider_id, state in self._providers.items()
        }


# =============================================================================
# Instância global singleton
# =============================================================================

_global_store: Optional[UsageStore] = None


def get_store() -> UsageStore:
    """Retorna a instância global do store."""
    global _global_store
    if _global_store is None:
        _global_store = UsageStore()
    return _global_store


def init_store(config: Optional[StoreConfig] = None) -> UsageStore:
    """Inicializa a instância global do store."""
    global _global_store
    _global_store = UsageStore(config)
    return _global_store
