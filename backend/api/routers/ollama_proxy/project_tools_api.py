"""
=============================================================
 KOTHAR v6.0 — Ollama Proxy Router
 Faz proxy para APIs do Ollama, contornando CORS e bloqueios 403
 do Cloudflare Tunnel / Ngrok.
=============================================================
"""

import os
import re
import json
import httpx
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.core.logger import get_logger
from backend.core.rag_supremo import rag_supremo, build_rag_context, RAG_MAX_TOTAL_CHUNKS, RAG_CHUNK_MAX_CHARS
from backend.core.memory import get_memory as get_conversation_memory
from backend.core.query_intel import (
    detect_intent, get_system_prompt_for_intent,
    decompose_query, hybrid_search,
    COT_PROMPT, FEW_SHOT_EXAMPLES,
)
from backend.core.rag_v2 import (
    filter_by_category, extractive_compress,
    self_check_answer, rerank_with_position_bias,
)
from backend.core.web_fetcher import (
    fetch_url, web_search, extract_urls, is_safe_url,
)
from backend.core.router import route_model
from backend.core.tools import (
    TOOLS_SCHEMA, execute_tool, format_tool_result,
)
from backend.core.project_mode import (
    index_project, get_project_collection, list_indexed_projects,
)
from backend.core.cache import (
    get_cached_context, set_cached_context, invalidate_session,
    get_cache_stats, clear_cache,
)

log = get_logger("api.ollama_proxy")
router = APIRouter()


# =====================================================
# ENDPOINTS v6.0 SUPREMO: Project Mode, Tools, Cache
# =====================================================

class IndexProjectRequest(BaseModel):
    path: str
    file_patterns: Optional[list] = None
    max_files: int = 500


@router.post("/project/index")
async def api_index_project(req: IndexProjectRequest):
    """Indexa uma pasta como projeto (Project Mode)."""
    result = await index_project(
        project_path=req.path,
        file_patterns=req.file_patterns,
        max_files=req.max_files,
    )
    return result


@router.get("/project/list")
async def api_list_projects():
    """Lista projetos indexados."""
    return {"projects": list_indexed_projects()}


@router.get("/cache/stats")
async def api_cache_stats():
    """Estatísticas do context cache."""
    return get_cache_stats()


@router.post("/cache/clear")
async def api_cache_clear():
    """Limpa todo o context cache."""
    clear_cache()
    return {"ok": True}


@router.post("/cache/invalidate/{session_id}")
async def api_cache_invalidate(session_id: str):
    """Invalida cache de uma sessão."""
    invalidate_session(session_id)
    return {"ok": True}


@router.get("/tools/schema")
async def api_tools_schema():
    """Retorna schema das tools disponíveis (para function calling Ollama)."""
    return {"tools": TOOLS_SCHEMA}


@router.post("/tools/execute")
async def api_execute_tool(request: Request):
    """Executa uma tool diretamente (sem LLM)."""
    body = await request.json()
    name = body.get("name")
    args = body.get("args", {})
    if not name:
        return {"ok": False, "error": "Missing tool name"}
    result = execute_tool(name, args)
    return result


@router.get("/router/decision")
async def api_router_decision(q: str):
    """Preview: qual modelo o router escolheria para esta query."""
    intent = detect_intent(q)
    model, reason = route_model(q, intent)
    return {"intent": intent, "model": model, "reason": reason}
