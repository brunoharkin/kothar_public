"""
Kothar Token Counter — Contabilização de Uso de Tokens
=====================================================

Inspirado em: https://github.com/vinzdg/codenotch

Este módulo implementa um sistema de contabilização de tokens
integrado ao Kothar para monitorar o uso em sessões do Claude Code.
"""

from token_counter.models import (
    Fidelity,
    ProviderStatus,
    WindowType,
    Money,
    LimitWindow,
    UsageContext,
    LocalPrediction,
    Totals,
    ProviderSnapshot,
)

from token_counter.providers.base import UsageProvider
from token_counter.providers.claude_cli import ClaudeCLIProvider
from token_counter.store import UsageStore
from token_counter.ledger import LocalTokenLedger

__all__ = [
    # Models
    "Fidelity",
    "ProviderStatus",
    "WindowType",
    "Money",
    "LimitWindow",
    "UsageContext",
    "LocalPrediction",
    "Totals",
    "ProviderSnapshot",
    # Providers
    "UsageProvider",
    "ClaudeCLIProvider",
    # Store
    "UsageStore",
    # Ledger
    "LocalTokenLedger",
]
