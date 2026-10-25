#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Memory & RAG Tracker Hook
 Registra eventos de Memória e RAG automaticamente no trace.
 Pode ser chamado pelo claude_hook.py ou manualmente.
=============================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Configuração
KOTHAR_API_URL = os.environ.get("KOTHAR_API_URL", "http://localhost:8080")
KOTHAR_TRACE_URL = f"{KOTHAR_API_URL}/api/traces/"
KOTHAR_SESSION_ID = os.environ.get("KOTHAR_SESSION_ID", "")

# Contador de eventos registrados
_event_count = {"memory": 0, "rag": 0, "skill": 0}


def log(msg: str):
    """Log para stderr."""
    print(f"[KOTHAR-MEM-RAG] {msg}", file=sys.stderr)


def register_trace(
    session_id: str,
    event_type: str,
    tool_name: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    metadata: dict = None,
    duration_ms: int = None,
):
    """
    Registra um evento de trace no backend.
    """
    if not session_id:
        return

    payload = {
        "session_id": session_id,
        "sequence": 0,
        "event_type": event_type,
        "agent_name": "kothar",
        "tool_name": tool_name,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_used": tokens_input + tokens_output,
        "is_error": False,
        "duration_ms": duration_ms,
        "metadata": metadata or {},
    }

    try:
        req = urllib.request.Request(
            KOTHAR_TRACE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status in (200, 201):
                _event_count[event_type.split("_")[0] if "_" in event_type else "memory"] += 1
                return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        log(f"Erro registrando trace: {e}")
    return False


def track_memory_load(
    session_id: str,
    memory_type: str = "conversation_history",
    chunks_loaded: int = 0,
    tokens: int = 0,
    duration_ms: int = None,
):
    """
    Registra carregamento de memória (histórico de conversa).
    """
    register_trace(
        session_id=session_id,
        event_type="memory_load",
        tool_name=f"memory:{memory_type}",
        tokens_input=tokens,
        metadata={
            "memory_type": memory_type,
            "chunks_loaded": chunks_loaded,
            "source": "claude_history",
        },
        duration_ms=duration_ms,
    )
    log(f"Memory loaded: {memory_type} ({chunks_loaded} chunks, {tokens} tokens)")


def track_rag_preload(
    session_id: str,
    query: str,
    chunks_loaded: int = 0,
    tokens: int = 0,
    duration_ms: int = None,
    collection: str = "kothar_skills",
):
    """
    Registra carregamento de contexto RAG.
    """
    register_trace(
        session_id=session_id,
        event_type="rag_preload",
        tool_name=f"rag:{collection}",
        tokens_input=tokens,
        metadata={
            "query": query[:200],
            "chunks_loaded": chunks_loaded,
            "collection": collection,
            "source": "chromadb",
        },
        duration_ms=duration_ms,
    )
    log(f"RAG preload: {collection} query='{query[:50]}...' ({chunks_loaded} chunks, {tokens} tokens)")


def track_skill_retrieval(
    session_id: str,
    skill_name: str,
    relevance: float = 0.0,
    tokens: int = 0,
):
    """
    Registra recuperação de skill do RAG.
    """
    register_trace(
        session_id=session_id,
        event_type="skill_retrieval",
        tool_name=f"skill:{skill_name}",
        tokens_input=tokens,
        metadata={
            "skill_name": skill_name,
            "relevance": relevance,
            "source": "kothar_skills",
        },
    )
    log(f"Skill retrieved: {skill_name} (relevance: {relevance:.2f})")


# ============================================================
# CLI para registro manual
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kothar Memory/RAG Tracker")
    parser.add_argument("--type", required=True,
                        choices=["memory_load", "rag_preload", "skill_retrieval"],
                        help="Tipo de evento")
    parser.add_argument("--session", required=True, help="Session ID")
    parser.add_argument("--name", required=True, help="Nome do tool/memory/skill")
    parser.add_argument("--tokens", type=int, default=0, help="Tokens consumidos")
    parser.add_argument("--chunks", type=int, default=0, help="Chunks carregados")
    parser.add_argument("--query", default="", help="Query RAG")
    parser.add_argument("--relevance", type=float, default=0.0, help="Relevância da skill")

    args = parser.parse_args()

    if args.type == "memory_load":
        track_memory_load(args.session, args.name, args.chunks, args.tokens)
    elif args.type == "rag_preload":
        track_rag_preload(args.session, args.query, args.chunks, args.tokens)
    elif args.type == "skill_retrieval":
        track_skill_retrieval(args.session, args.name, args.relevance, args.tokens)

    print(json.dumps({"success": True, "events": _event_count}))
