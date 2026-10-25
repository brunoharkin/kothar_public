"""
=============================================================
 Kothar v4.0 — RAG Tracker Router
 Rastreia uso de RAG em tempo real por sessão.
=============================================================
"""

import json
import time
from collections import defaultdict
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from backend.core.logger import get_logger

log = get_logger("api.rag_tracker")
router = APIRouter()

# Armazenamento em memória (pode ser movido para Redis depois)
class RAGTracker:
    """Rastreia queries RAG por sessão."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.global_stats = {
            "total_queries": 0,
            "total_hits": 0,
            "total_misses": 0,
            "total_chunks_retrieved": 0,
        }

    def record(self, session_id: str, query: str, chunks: List[str], sources: List[str]):
        """Registra uma query RAG."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "queries": [],
                "total_queries": 0,
                "total_hits": 0,
                "total_chunks": 0,
                "last_active": time.time(),
            }

        sess = self.sessions[session_id]
        is_hit = len(chunks) > 0

        sess["queries"].append({
            "query": query[:200],
            "chunks_count": len(chunks),
            "sources": sources[:5],
            "timestamp": time.time(),
            "is_hit": is_hit,
        })
        # Manter só últimas 50 queries
        sess["queries"] = sess["queries"][-50:]
        sess["total_queries"] += 1
        sess["total_hits"] += 1 if is_hit else 0
        sess["total_chunks"] += len(chunks)
        sess["last_active"] = time.time()

        self.global_stats["total_queries"] += 1
        self.global_stats["total_hits"] += 1 if is_hit else 0
        self.global_stats["total_misses"] += 1 if not is_hit else 0
        self.global_stats["total_chunks_retrieved"] += len(chunks)

    def get_session(self, session_id: str) -> Dict:
        """Retorna stats de uma sessão."""
        return self.sessions.get(session_id, {
            "queries": [],
            "total_queries": 0,
            "total_hits": 0,
            "total_chunks": 0,
        })

    def get_recent(self, limit: int = 20) -> List[Dict]:
        """Retorna queries recentes de todas as sessões."""
        all_queries = []
        for sid, data in self.sessions.items():
            for q in data["queries"]:
                all_queries.append({"session_id": sid, **q})
        # Ordenar por timestamp desc
        all_queries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return all_queries[:limit]


# Singleton global
tracker = RAGTracker()


@router.get("/sessions")
async def list_sessions() -> dict:
    """Lista todas as sessões que usaram RAG."""
    sessions_summary = []
    for sid, data in tracker.sessions.items():
        sessions_summary.append({
            "session_id": sid,
            "total_queries": data["total_queries"],
            "total_hits": data["total_hits"],
            "hit_rate": data["total_hits"] / max(data["total_queries"], 1),
            "total_chunks": data["total_chunks"],
            "last_active": data["last_active"],
        })
    # Ordenar por last_active desc
    sessions_summary.sort(key=lambda x: x["last_active"], reverse=True)
    return {"sessions": sessions_summary, "total": len(sessions_summary)}


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str) -> dict:
    """Detalhe de uma sessão: queries, chunks, fontes."""
    return tracker.get_session(session_id)


@router.get("/recent")
async def get_recent_queries(limit: int = 20) -> dict:
    """Últimas queries RAG executadas."""
    return {"queries": tracker.get_recent(limit)}


@router.get("/stats")
async def get_global_stats() -> dict:
    """Estatísticas globais do RAG."""
    return {
        **tracker.global_stats,
        "active_sessions": len(tracker.sessions),
        "hit_rate": tracker.global_stats["total_hits"] / max(tracker.global_stats["total_queries"], 1),
    }


class RecordRequest(BaseModel):
    session_id: str
    query: str
    chunks: List[str] = []
    sources: List[str] = []


@router.post("/record")
async def record_query(req: RecordRequest) -> dict:
    """Endpoint para o proxy Ollama registrar uso de RAG."""
    tracker.record(req.session_id, req.query, req.chunks, req.sources)
    return {"recorded": True, "session_id": req.session_id}
