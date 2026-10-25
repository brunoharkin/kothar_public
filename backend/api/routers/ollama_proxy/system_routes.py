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


@router.post("/proxy/generate")
async def proxy_generate(body: dict):
    """Gera texto simples."""
    return await proxy_request("POST", "/api/generate", body)


@router.get("/proxy/version")
async def proxy_version():
    """Versão do Ollama."""
    return await proxy_request("GET", "/api/version")


@router.get("/proxy/status")
async def proxy_status():
    """Status do proxy."""
    return {
        "proxy": "active",
        "ollama_url": OLLAMA_BASE_URL,
        "info": "Use /api/ollama/proxy/* para acessar Ollama via backend",
    }


@router.get("/proxy/models")
async def proxy_models_friendly():
    """
    Lista modelos (formato amigável).
    O destino é definido exclusivamente no servidor.
    """
    # Pega URL customizada do query param ou usa a padrão
    from fastapi import Request
    # (Implementação abaixo movida para get_models_with_url)
    pass


@router.get("/proxy/tags")
async def proxy_tags_custom(request: Request):
    """Lista modelos do Ollama pelo destino interno configurado."""
    target_url = OLLAMA_BASE_URL
    
    # Se o frontend mandar localhost, redirecionar para o container do Ollama
    if target_url and "localhost" in target_url:
        target_url = target_url.replace("localhost", "kothar_ollama")

    return await proxy_request_to(target_url, "GET", "/api/tags")

