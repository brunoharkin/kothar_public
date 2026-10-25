"""
KOTHAR v4.0 — Tipos do Decisor System One Local
Inspiração: TypeSafe AI Jev (System One Model)
Implementação: modelos Pydantic tipados, zero alucinação de schema.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FonteMemoria(Enum):
    """Para qual banco rotear a query."""
    CHROMA_SEMANTICO = "chroma"       # busca vetorial — "o que é parecido com X?"
    NEO4J_GRAFO = "neo4j"             # dependências — "o que usa Y?"
    POSTGRES_AUDITORIA = "postgres"   # traces históricos — "o que aconteceu em Z?"
    DIRETO = "direto"                 # sem banco, resposta direta


@dataclass
class Escolha:
    """Choice — qual opção selecionar (inspirado em Jev Choice type)."""
    valor: str
    confianca: float  # 0.0 a 1.0
    alternativas: list[str] = field(default_factory=list)
    
    @property
    def confiavel(self) -> bool:
        return self.confianca >= 0.7


@dataclass
class Pontuacao:
    """Score — valor numérico com confiança (inspirado em Jev Score type)."""
    valor: float   # 0.0 a 1.0
    confianca: float
    motivo: str = ""
    
    @property
    def relevante(self) -> bool:
        return self.valor >= 0.5


@dataclass
class Noul:
    """Boolean calibrado — sim/não com probabilidade (inspirado em Jev Noul type)."""
    resultado: bool
    confianca: float  # 0.0 a 1.0
    motivo: str = ""
    
    @property
    def certo(self) -> bool:
        """Só é considerado certo se confiança >= 0.8."""
        return self.resultado and self.confianca >= 0.8


@dataclass
class DecisaoRouting:
    """Decisão completa de routing para uma query."""
    fonte: FonteMemoria
    confianca: float
    razao: str
    fallback: FonteMemoria = FonteMemoria.CHROMA_SEMANTICO
