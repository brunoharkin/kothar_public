"""
=============================================================
 KOTHAR v4.0 — Exceções Customizadas
 Engenheiro Kothar | Ugarit Digital
=============================================================
"""

from typing import Any


class KotharError(Exception):
    """Exceção base do sistema Kothar."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, context={self.context})"


# --- Memória ---
class MemoryError(KotharError):
    """Erros relacionados à camada de memória."""


class GraphRAGError(MemoryError):
    """Erro no GraphRAG (Neo4j)."""


class SemanticSearchError(MemoryError):
    """Erro na busca semântica (ChromaDB)."""


class CacheError(MemoryError):
    """Erro no cache (Redis)."""


class VaultError(MemoryError):
    """Erro ao acessar o Cofre (Obsidian)."""


# --- Agentes ---
class AgentError(KotharError):
    """Erros dos agentes."""


class OrchestrationError(AgentError):
    """Erro na orquestração de agentes."""


class BlueprintError(AgentError):
    """Erro no blueprint de tarefa."""


class SkillNotFoundError(AgentError):
    """Skill não encontrada no ChromaDB ou .claude/skills/."""

    def __init__(self, skill_name: str):
        super().__init__(
            f"Skill '{skill_name}' não encontrada na memória semântica.",
            context={"skill_name": skill_name},
        )


class MaxRetriesExceededError(AgentError):
    """
    Mandamento #4: 3 erros iguais → PARAR.
    Disparado quando um agente falha 3x consecutivas no mesmo passo.
    """

    def __init__(self, step: str, retries: int = 3):
        super().__init__(
            f"Limite de {retries} tentativas atingido no passo '{step}'. "
            "Intervenção humana necessária.",
            context={"step": step, "retries": retries},
        )


# --- Trace ---
class TraceError(KotharError):
    """Erros na gravação de traces."""


# --- API ---
class NotFoundError(KotharError):
    """Recurso não encontrado."""

    http_status: int = 404


class UnauthorizedError(KotharError):
    """Acesso não autorizado."""

    http_status: int = 401


class ValidationError(KotharError):
    """Erro de validação de entrada."""

    http_status: int = 422
