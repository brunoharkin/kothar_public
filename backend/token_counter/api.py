"""
API de Token Counter - Endpoints REST
======================================

Provides REST endpoints for token usage data.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional
import os
import json

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from token_counter.models import (
    Fidelity,
    LimitWindow,
    ProviderSnapshot,
    ProviderStatus,
    WindowType,
)
from token_counter.providers.claude_cli import ClaudeCLIProvider
from token_counter.store import UsageStore, get_store, init_store, StoreConfig
from token_counter.ledger import LocalTokenLedger, LocalPrediction, Totals


logger = logging.getLogger(__name__)

# Router principal
router = APIRouter(prefix="/api/usage", tags=["usage"])


# =============================================================================
# Pydantic Models
# =============================================================================

class TotalsResponse(BaseModel):
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    reasoning_share: float = 0.0


class WindowResponse(BaseModel):
    type: str
    used_fraction: float
    used: int
    limit: int
    remaining: int
    resets_at: Optional[str] = None
    label: Optional[str] = None


class ContextResponse(BaseModel):
    timestamp: Optional[str] = None
    instance: Optional[str] = None
    model: Optional[str] = None


class SnapshotResponse(BaseModel):
    id: str
    name: str
    fidelity: str
    status: str
    windows: list[WindowResponse]
    headline: Optional[str] = None
    context: Optional[ContextResponse] = None
    ledger_today: Optional[TotalsResponse] = None
    error_message: Optional[str] = None


class SummaryResponse(BaseModel):
    instance: str
    today: TotalsResponse
    last_7_days: TotalsResponse
    all_time: TotalsResponse
    dates_tracked: int


class RefreshRequest(BaseModel):
    provider_id: Optional[str] = None


class StatusResponse(BaseModel):
    is_running: bool
    providers: dict


# =============================================================================
# Ledger singleton
# =============================================================================

_ledger: Optional[LocalTokenLedger] = None


def get_ledger() -> LocalTokenLedger:
    """Retorna instância global do ledger."""
    global _ledger
    if _ledger is None:
        storage_path = os.environ.get(
            "KOTHAR_TOKEN_USAGE_PATH",
            "~/.kothar/token-usage",
        )
        _ledger = LocalTokenLedger(storage_path=storage_path)
    return _ledger


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/snapshots", response_model=dict[str, SnapshotResponse])
async def list_snapshots():
    """
    Lista todos os snapshots disponíveis.

    Returns:
        Dicionário de snapshots por provider ID
    """
    store = get_store()
    snapshots = store.get_all_snapshots()

    return {
        provider_id: SnapshotResponse(
            id=s.id,
            name=s.name,
            fidelity=s.fidelity.value,
            status=s.status.value,
            windows=[
                WindowResponse(
                    type=w.type.value,
                    used_fraction=w.used_fraction,
                    used=w.used,
                    limit=w.limit,
                    remaining=w.remaining,
                    resets_at=w.resets_at.isoformat() if w.resets_at else None,
                    label=w.label,
                )
                for w in s.windows
            ],
            headline=s.headline.format_for_display(s.fidelity) if s.headline else None,
            context=ContextResponse(
                timestamp=s.context.timestamp.isoformat() if s.context else None,
                instance=s.context.instance if s.context else None,
                model=s.context.model if s.context else None,
            ) if s.context else None,
            ledger_today=TotalsResponse(
                **s.ledger.totals_today().to_dict()
            ) if s.ledger else None,
            error_message=s.error_message,
        )
        for provider_id, s in snapshots.items()
    }


@router.get("/snapshot/{provider_id}", response_model=SnapshotResponse)
async def get_snapshot(provider_id: str):
    """
    Retorna snapshot de um provedor específico.

    Args:
        provider_id: ID do provedor

    Returns:
        Snapshot do provedor

    Raises:
        404: Provedor não encontrado
    """
    store = get_store()
    snapshot = store.get_snapshot(provider_id)

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    return SnapshotResponse(
        id=snapshot.id,
        name=snapshot.name,
        fidelity=snapshot.fidelity.value,
        status=snapshot.status.value,
        windows=[
            WindowResponse(
                type=w.type.value,
                used_fraction=w.used_fraction,
                used=w.used,
                limit=w.limit,
                remaining=w.remaining,
                resets_at=w.resets_at.isoformat() if w.resets_at else None,
                label=w.label,
            )
            for w in snapshot.windows
        ],
        headline=snapshot.headline.format_for_display(snapshot.fidelity) if snapshot.headline else None,
        context=ContextResponse(
            timestamp=snapshot.context.timestamp.isoformat() if snapshot.context else None,
            instance=snapshot.context.instance if snapshot.context else None,
            model=snapshot.context.model if snapshot.context else None,
        ) if snapshot.context else None,
        ledger_today=TotalsResponse(
            **snapshot.ledger.totals_today().to_dict()
        ) if snapshot.ledger else None,
        error_message=snapshot.error_message,
    )


@router.get("/ledger", response_model=SummaryResponse)
async def get_ledger_summary(instance: str = "default"):
    """
    Retorna resumo do ledger local.

    Args:
        instance: ID da instância (default: "default")

    Returns:
        Resumo com totais hoje, últimos 7 dias, e todos os tempos
    """
    ledger = get_ledger()
    summary = ledger.summary(instance)

    return SummaryResponse(
        instance=summary["instance"],
        today=TotalsResponse(**summary["today"]),
        last_7_days=TotalsResponse(**summary["last_7_days"]),
        all_time=TotalsResponse(**summary["all_time"]),
        dates_tracked=summary["dates_tracked"],
    )


@router.post("/record")
async def record_prediction(
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    reasoning_tokens: int = 0,
    instance: str = "default",
):
    """
    Registra uma predição de tokens.

    Args:
        input_tokens: Número de tokens de entrada
        output_tokens: Número de tokens de saída
        reasoning_tokens: Número de tokens de raciocínio
        instance: ID da instância

    Returns:
        Totais atualizados do dia
    """
    ledger = get_ledger()

    prediction = LocalPrediction(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
    )

    ledger.record(prediction, instance=instance)

    today = ledger.totals_today(instance)

    return {
        "recorded": True,
        "today": today.to_dict(),
    }


@router.get("/limits")
async def get_limits():
    """
    Retorna limites configurados dos providers.

    Returns:
        Dicionário de limites por provider
    """
    store = get_store()
    return store.get_status_summary()


@router.post("/refresh")
async def refresh_provider(request: RefreshRequest = RefreshRequest()):
    """
    Força refresh de um ou todos os providers.

    Args:
        request: provider_id opcional (se None, refresh all)

    Returns:
        Resultado do refresh
    """
    store = get_store()

    if request.provider_id:
        snapshot = await store.fetch(request.provider_id)
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {request.provider_id} not found",
            )
        return {"refreshed": request.provider_id, "snapshot": snapshot.to_dict()}
    else:
        # Refresh all
        await asyncio.gather(
            *[store.fetch(pid) for pid in store._providers.keys()],
            return_exceptions=True,
        )
        return {"refreshed": list(store._providers.keys())}


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Retorna status do UsageStore.

    Returns:
        Status do store e providers
    """
    store = get_store()
    return StatusResponse(
        is_running=store._is_running,
        providers=store.get_status_summary(),
    )


@router.post("/cleanup")
async def cleanup_old_days(keep_days: int = 60):
    """
    Limpa dias antigos do ledger.

    Args:
        keep_days: Número de dias para manter

    Returns:
        Número de dias removidos
    """
    ledger = get_ledger()
    removed = ledger.cleanup_old_days(keep_days)
    return {"removed_days": removed}


# =============================================================================
# Initialization
# =============================================================================

def setup_token_counter():
    """
    Inicializa o sistema de token counter.

    Deve ser chamado na inicialização da aplicação.
    """
    # Inicializa store
    store = init_store()

    # Registra providers padrão
    claude_provider = ClaudeCLIProvider()
    store.register(claude_provider)

    logger.info("Token counter initialized")

    return store
