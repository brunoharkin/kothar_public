"""
Protocolo base para Providers de Uso
====================================

Inspirado em UsageProvider.swift do Codenotch.

Define a interface abstrata que todos os provedores devem implementar
para obter dados de uso de diferentes fontes (Claude Code, Cursor, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, runtime_checkable

from token_counter.models import (
    Fidelity,
    ProviderSnapshot,
    ProviderStatus,
)


class ProviderKind(Enum):
    """Categoria do provedor."""
    USAGE = "usage"               # Provedor que busca dados externos
    LOCAL_RUNTIME = "localRuntime"  # Provedor de runtime local


class UsageProviderError(Exception):
    """
    Erros específicos de provedor de uso.

    Usados para categorizar falhas e decidir estratégia de retry.
    """

    NEEDS_AUTH = "needsAuth"
    ACCESS_DENIED = "accessDenied"
    RATE_LIMITED = "rateLimited"
    CREDENTIAL_EXPIRED = "credentialExpired"
    UNSUPPORTED = "unsupported"
    NETWORK_ERROR = "networkError"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

    @classmethod
    def needs_auth(cls, message: str = "Authentication required") -> "UsageProviderError":
        return cls(cls.NEEDS_AUTH, message)

    @classmethod
    def access_denied(cls, message: str = "Access denied") -> "UsageProviderError":
        return cls(cls.ACCESS_DENIED, message)

    @classmethod
    def rate_limited(cls, message: str = "Rate limit exceeded") -> "UsageProviderError":
        return cls(cls.RATE_LIMITED, message)

    @classmethod
    def credential_expired(cls, message: str = "Credentials expired") -> "UsageProviderError":
        return cls(cls.CREDENTIAL_EXPIRED, message)

    @classmethod
    def unsupported(cls, message: str = "Provider not supported") -> "UsageProviderError":
        return cls(cls.UNSUPPORTED, message)

    @classmethod
    def network_error(cls, message: str = "Network error") -> "UsageProviderError":
        return cls(cls.NETWORK_ERROR, message)

    @classmethod
    def timeout(cls, message: str = "Request timeout") -> "UsageProviderError":
        return cls(cls.TIMEOUT, message)

    @classmethod
    def unknown(cls, message: str = "Unknown error") -> "UsageProviderError":
        return cls(cls.UNKNOWN, message)


@runtime_checkable
class UsageProvider(Protocol):
    """
    Protocolo abstrato para provedores de dados de uso.

    Cada provedor (Claude, Cursor, Ollama, etc.) implementa esta interface
    para fornecer dados de consumo de tokens.

    Atributos obrigatórios:
        id: Identificador único do provedor
        display_name: Nome para exibição
        kind: Categoria do provedor

    Métodos obrigatórios:
        fetch_snapshot(): Busca dados de uso atuais
        is_available(): Verifica se o provedor está disponível
    """

    @property
    def id(self) -> str:
        """Identificador único do provedor."""
        ...

    @property
    def display_name(self) -> str:
        """Nome para exibição no UI."""
        ...

    @property
    def kind(self) -> ProviderKind:
        """Categoria do provedor."""
        ...

    @property
    def is_visible_when_absent(self) -> bool:
        """
        Se True, o provedor aparece mesmo quando não está instalado/disponível.
        Útil para provedores que podem ser configurados mas ainda não estão ativos.
        """
        return True

    @abstractmethod
    async def fetch_snapshot(self) -> ProviderSnapshot:
        """
        Busca dados de uso atuais.

        Returns:
            ProviderSnapshot com dados de uso

        Raises:
            UsageProviderError: Em caso de falha
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica se o provedor está disponível/configurado.

        Returns:
            True se puder ser usado, False caso contrário
        """
        ...


class BaseUsageProvider(ABC):
    """
    Implementação base abstrata com defaults para UsageProvider.

    Subclasses só precisam implementar os métodos específicos.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Identificador único do provedor."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nome para exibição no UI."""
        ...

    @property
    def kind(self) -> ProviderKind:
        """Categoria do provedor - default é USAGE."""
        return ProviderKind.USAGE

    @property
    def is_visible_when_absent(self) -> bool:
        """Por padrão, provedores são visíveis mesmo quando ausentes."""
        return True

    def account(self) -> Optional[dict]:
        """Retorna informações da conta se disponível."""
        return None

    def sign_in_route(self) -> Optional[str]:
        """URL/route para fazer sign in."""
        return None

    async def sign_out(self) -> None:
        """Encerra sessão."""
        pass

    async def present_sign_in(self) -> bool:
        """Inicia fluxo de sign in. Retorna True se sucesso."""
        return False

    async def present_account_switch(self) -> bool:
        """Inicia fluxo de troca de conta. Retorna True se sucesso."""
        return await self.present_sign_in()

    def forget_cached_credential(self) -> None:
        """Limpa credenciais em cache."""
        pass

    @abstractmethod
    async def fetch_snapshot(self) -> ProviderSnapshot:
        """Busca dados de uso atuais."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o provedor está disponível."""
        ...

    def glyph(self) -> Optional[str]:
        """Retorna glyph/emoji para o provedor."""
        return None
