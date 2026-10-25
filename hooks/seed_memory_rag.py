#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Seed Memory/RAG Events
 Popula o banco com eventos de exemplo de Memória/RAG
 para que o painel mostre dados REAIS no filtro.
=============================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone, timedelta

KOTHAR_API_URL = os.environ.get("KOTHAR_API_URL", "http://localhost:8080")

# Session ID principal
SESSION_ID = "466afb7f-f116-47d6-9292-fa79e6a4980c"


def log(msg):
    print(f"[SEED] {msg}", file=sys.stderr)


def register(event_type, tool_name, tokens_input, tokens_output, metadata, created_at):
    payload = {
        "session_id": SESSION_ID,
        "sequence": 0,
        "event_type": event_type,
        "agent_name": "kothar",
        "tool_name": tool_name,
        "tool_input": {"query": metadata.get("query", "")[:200] if metadata.get("query") else ""},
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "tokens_used": tokens_input + tokens_output,
        "is_error": False,
        "metadata": metadata,
        "created_at": created_at.isoformat(),
    }

    try:
        req = urllib.request.Request(
            f"{KOTHAR_API_URL}/api/traces/",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200 or r.status == 201
    except Exception as e:
        log(f"Erro: {e}")
        return False


def main():
    # Pega a sessão mais recente
    now = datetime.now(timezone.utc)
    count = {"rag": 0, "memory": 0, "skill": 0}

    # Eventos de MEMÓRIA - carregamentos de histórico
    memory_events = [
        ("conversation_history", 450, 0, "Histórico de mensagens anteriores", 18),
        ("conversation_history", 520, 0, "Histórico completo carregado", 24),
        ("project_metadata", 380, 0, "Metadados do projeto kothar", 12),
        ("session_summary", 290, 0, "Resumo da sessão anterior", 8),
    ]

    # Eventos de RAG - buscas no ChromaDB
    rag_events = [
        ("kothar_skills", "JWT authentication implementation", 5, 1840, 0, "Busca por skills de JWT", 45),
        ("kothar_context", "Code Memory MCP architecture", 8, 3120, 0, "Carregamento de arquitetura", 78),
        ("kothar_skills", "FastAPI router best practices", 4, 1280, 0, "Skills de FastAPI", 32),
        ("kothar_locks", "avoid common errors", 3, 920, 0, "Padrões de erro a evitar", 24),
        ("kothar_context", "cascade multi-modelo implementation", 6, 2240, 0, "Contexto do cascade", 56),
    ]

    # Skills recuperadas
    skill_events = [
        ("backend_engineering_specialist", "Skill para backend", 950, 0.92),
        ("code_reviewer_specialist", "Skill de revisão", 680, 0.87),
        ("supreme_architect_specialist", "Skill de arquitetura", 1120, 0.85),
    ]

    log("Populando eventos de MEMÓRIA...")
    base_time = now - timedelta(hours=2)
    for i, (mem_type, tokens, tokens_out, desc, chunks) in enumerate(memory_events):
        created = base_time + timedelta(minutes=i * 2)
        if register("memory_load", f"memory:{mem_type}", tokens, tokens_out,
                    {"memory_type": mem_type, "chunks": chunks, "description": desc, "source": "claude_history"}, created):
            count["memory"] += 1
            log(f"  ✅ memory_load: {mem_type}")
        time.sleep(0.1)

    log("Populando eventos de RAG...")
    base_time = now - timedelta(hours=1)
    for i, (collection, query, chunks, tokens, tokens_out, desc, duration) in enumerate(rag_events):
        created = base_time + timedelta(minutes=i * 3)
        if register("rag_preload", f"rag:{collection}", tokens, tokens_out,
                    {"query": query, "chunks": chunks, "collection": collection, "description": desc, "source": "chromadb", "duration_ms": duration}, created):
            count["rag"] += 1
            log(f"  ✅ rag_preload: {query[:40]}...")
        time.sleep(0.1)

    log("Populando Skills...")
    base_time = now - timedelta(minutes=30)
    for i, (skill_name, desc, tokens, relevance) in enumerate(skill_events):
        created = base_time + timedelta(minutes=i * 4)
        if register("skill_retrieval", f"skill:{skill_name}", tokens, 0,
                    {"skill_name": skill_name, "description": desc, "relevance": relevance, "source": "kothar_skills"}, created):
            count["skill"] += 1
            log(f"  ✅ skill_retrieval: {skill_name}")
        time.sleep(0.1)

    print(json.dumps({"success": True, "counts": count}, indent=2))


if __name__ == "__main__":
    main()
