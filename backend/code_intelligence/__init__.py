"""
=============================================================
 KOTHAR v5.0 — Code Intelligence Module
 Wrapper para Codebase Memory MCP
=============================================================
"""

from .cbm_client import CBMClient
from .indexer import CodebaseIndexer
from .query_engine import QueryEngine

__all__ = ["CBMClient", "CodebaseIndexer", "QueryEngine"]
