"""
Modelos de Dados para o Sistema de Contabilização de Tokens
============================================================

Inspirado em UsageModel.swift do Codenotch.

Define as estruturas principais:
- Fidelity: Nível de confiança dos dados
- ProviderStatus: Estado do provedor
- LimitWindow: Janela de uso (sessão, semanal, etc.)
- TokenLedger: Contador local de tokens
- ProviderSnapshot: Agregação de todos os dados de uso
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional
import json
import os
from pathlib import Path


class Fidelity(Enum):
    """
    Nível de confiança dos dados de uso.

    - OFFICIAL: Dados diretos do fornecedor (API real)
    - DERIVED: Calculado pelo sistema
    - MANUAL: Inserido pelo usuário
    """
    OFFICIAL = "official"
    DERIVED = "derived"
    MANUAL = "manual"

    def __str__(self) -> str:
        return self.value

    def prefix_for_display(self) -> str:
        """Retorna prefixo para exibição (~ quando não é official)."""
        return "~" if self != Fidelity.OFFICIAL else ""


class ProviderStatus(Enum):
    """
    Estados possíveis de um provedor de uso.
    """
    OK = "ok"                          # Dados válidos e atualizados
    STALE = "stale"                     # Dados antigos (>15min sem atualização)
    NEEDS_AUTH = "needsAuth"           # Requer autenticação
    ACCESS_DENIED = "accessDenied"     # Sem permissão de acesso
    RATE_LIMITED = "rateLimited"        # Rate limit atingido
    UNSUPPORTED = "unsupported"        # Provedor não suportado
    ERROR = "error"                    # Erro genérico

    def is_stale(self, last_update: datetime, threshold_minutes: int = 15) -> bool:
        """Verifica se os dados estão stales."""
        if self != ProviderStatus.OK:
            return False
        return datetime.now() - last_update > timedelta(minutes=threshold_minutes)


class WindowType(Enum):
    """Tipos de janela de uso."""
    SESSION = "session"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class Money:
    """Dados monetários de uso."""
    currency: str = "USD"
    spent: float = 0.0
    remaining: float = 0.0

    @property
    def spent_fraction(self) -> float:
        """Fração do limite já gasto (0.0 - 1.0)."""
        total = self.spent + self.remaining
        if total == 0:
            return 0.0
        return min(1.0, self.spent / total)


@dataclass
class LimitWindow:
    """
    Uma janela de uso (sessão, semanal, mensal).

    Suporta três modos de display:
    - usedFraction: porcentagem do limite gasto
    - remaining: unidades restantes (conta regressiva)
    - used: unidades gastas (conta progressiva)
    """
    type: WindowType
    used_fraction: float = 0.0      # 0.0 - 1.0
    used: int = 0                    # Tokens/unidades gastas
    limit: int = 0                   # Limite total
    remaining: int = 0               # Restante
    resets_at: Optional[datetime] = None
    money: Optional[Money] = None
    label: Optional[str] = None        # Label customizado para display

    @property
    def percent_used(self) -> float:
        """Porcentagem usada (0-100)."""
        return self.used_fraction * 100

    @property
    def compact_used(self) -> str:
        """Formato compacto para display: 651061 -> 651.1k."""
        if self.used >= 1_000_000:
            return f"{self.used / 1_000_000:.1f}M"
        elif self.used >= 1_000:
            return f"{self.used / 1_000:.1f}k"
        return str(self.used)

    @property
    def compact_remaining(self) -> str:
        """Formato compacto para restante."""
        if self.remaining >= 1_000_000:
            return f"{self.remaining / 1_000_000:.1f}M"
        elif self.remaining >= 1_000:
            return f"{self.remaining / 1_000:.1f}k"
        return str(self.remaining)

    def format_for_display(self, fidelity: Fidelity = Fidelity.OFFICIAL) -> str:
        """Formata para exibição: '38% Used · 62% left'."""
        prefix = fidelity.prefix_for_display()
        pct = self.percent_used

        if pct < 1:
            return f"{prefix}~{pct:.1f}% Used"

        remaining_pct = 100 - pct
        if remaining_pct < 1:
            return f"{prefix}{pct:.0f}% Used"

        return f"{prefix}{pct:.0f}% Used · {remaining_pct:.0f}% left"

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "used_fraction": self.used_fraction,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "resets_at": self.resets_at.isoformat() if self.resets_at else None,
            "label": self.label,
        }


@dataclass
class UsageContext:
    """Contexto metadata de uma leitura de uso."""
    timestamp: datetime
    instance: str = ""                    # Identificador da instância
    model: str = ""                       # Modelo usado
    session_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Totals:
    """Totais agregados de tokens."""
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    draft_tokens: int = 0
    accepted_draft_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total de tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def reasoning_share(self) -> float:
        """Fração do output gasta em raciocínio."""
        if self.output_tokens == 0:
            return 0.0
        return self.reasoning_tokens / self.output_tokens

    def add(self, prediction: LocalPrediction) -> None:
        """Acumula uma predição aos totais."""
        self.requests += 1
        self.input_tokens += prediction.input_tokens or 0
        self.output_tokens += prediction.output_tokens or 0
        self.reasoning_tokens += prediction.reasoning_tokens or 0
        self.draft_tokens += prediction.draft_tokens or 0
        self.accepted_draft_tokens += prediction.accepted_draft_tokens or 0

    def __add__(self, other: Totals) -> Totals:
        return Totals(
            requests=self.requests + other.requests,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            draft_tokens=self.draft_tokens + other.draft_tokens,
            accepted_draft_tokens=self.accepted_draft_tokens + other.accepted_draft_tokens,
        )

    def to_dict(self) -> dict:
        return {
            "requests": self.requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "draft_tokens": self.draft_tokens,
            "accepted_draft_tokens": self.accepted_draft_tokens,
            "reasoning_share": round(self.reasoning_share, 4),
        }


@dataclass
class LocalPrediction:
    """
    Registro de uma única resposta com contagem de tokens.
    """
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_tokens: int = 0
    draft_tokens: int = 0
    accepted_draft_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "draft_tokens": self.draft_tokens,
            "accepted_draft_tokens": self.accepted_draft_tokens,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LocalPrediction":
        """Reconstrói uma predição a partir de um dicionário."""
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            reasoning_tokens=data.get("reasoning_tokens", 0),
            draft_tokens=data.get("draft_tokens", 0),
            accepted_draft_tokens=data.get("accepted_draft_tokens", 0),
            timestamp=datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data else datetime.now(),
        )


@dataclass
class ProviderSnapshot:
    """
    Agregação completa de dados de uso de um provedor.

    É o objeto principal que a API retorna.
    """
    id: str
    name: str
    fidelity: Fidelity = Fidelity.OFFICIAL
    status: ProviderStatus = ProviderStatus.OK
    windows: list[LimitWindow] = field(default_factory=list)
    context: Optional[UsageContext] = None
    ledger: Optional[LocalTokenLedger] = None
    error_message: Optional[str] = None

    @property
    def headline(self) -> Optional[LimitWindow]:
        """Janela principal (a primeira ou a de sessão)."""
        if not self.windows:
            return None

        for window in self.windows:
            if window.type == WindowType.SESSION:
                return window

        return self.windows[0]

    @property
    def weekly_window(self) -> Optional[LimitWindow]:
        """Segunda janela (semanal ou mensal, nunca igual à headline)."""
        headline = self.headline
        for window in self.windows:
            if window != headline:
                return window
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "fidelity": self.fidelity.value,
            "status": self.status.value,
            "windows": [w.to_dict() for w in self.windows],
            "headline": self.headline.format_for_display(self.fidelity) if self.headline else None,
            "context": {
                "timestamp": self.context.timestamp.isoformat() if self.context else None,
                "instance": self.context.instance if self.context else None,
                "model": self.context.model if self.context else None,
            } if self.context else None,
            "ledger_today": self.ledger.totals_today().to_dict() if self.ledger else None,
            "error_message": self.error_message,
        }


# =============================================================================
# Money Breakdown
# =============================================================================

@dataclass
class UsageMoneyBreakdown:
    """Saldo em dinheiro."""
    currency: str = "USD"
    spent: float = 0.0
    remaining: float = 0.0

    @property
    def spent_fraction(self) -> float:
        total = self.spent + self.remaining
        if total == 0:
            return 0.0
        return min(1.0, self.spent / total)


# =============================================================================
# Usage Block (quando limite é atingido)
# =============================================================================

@dataclass
class UsageBlock:
    """Indica que um limite foi atingido."""
    reason: str
    resets_at: datetime

    def format_until_reset(self) -> str:
        """Retorna 'X until HH:mm'."""
        delta = self.resets_at - datetime.now()
        if delta.total_seconds() < 0:
            return "now"

        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m until {self.resets_at.strftime('%H:%M')}"
        return f"{minutes}m until {self.resets_at.strftime('%H:%M')}"
