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


from .worker import worker_state, ollama_background_worker
from .rag_injection import inject_rag_into_messages

# URL base do Ollama (configurável via env)
# Ollama roda no container kothar_ollama na rede docker
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://kothar_ollama:11434")

# Timeout para requisições
TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)


async def proxy_request(method: str, path: str, body: Optional[dict] = None, headers: dict = None):
    """
    Faz proxy de uma requisição para o Ollama.
    Adiciona headers para contornar bloqueios do Cloudflare/Ngrok.
    """
    url = f"{OLLAMA_BASE_URL}{path}"

    # Headers para contornar Cloudflare
    proxy_headers = {
        "Accept": "application/json",
        "User-Agent": "Kothar-LocalAI/1.0 (proxy)",
    }

    if headers:
        proxy_headers.update(headers)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=proxy_headers)
            elif method == "POST":
                response = await client.post(url, json=body, headers=proxy_headers)
            else:
                raise HTTPException(status_code=405, detail=f"Método {method} não suportado")

            content_type = response.headers.get("content-type", "application/json")

            if "text/event-stream" in content_type:
                # Streaming response (chat)
                return StreamingResponse(
                    iter([response.content]),
                    media_type=content_type,
                    status_code=response.status_code,
                )

            try:
                content = response.json() if response.content else {}
            except Exception as json_e:
                log.warning(f"Resposta não-JSON do Ollama ({response.status_code}): {response.text[:100]}")
                content = {"error": "Invalid JSON response", "raw": response.text[:200]}

            return JSONResponse(
                content=content,
                status_code=response.status_code,
            )

        except httpx.ConnectError as e:
            log.error(f"Erro de conexão com Ollama: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível conectar ao Ollama em {OLLAMA_BASE_URL}: {str(e)}",
            )
        except httpx.TimeoutException as e:
            log.error(f"Timeout ao conectar ao Ollama: {e}")
            raise HTTPException(
                status_code=504,
                detail=f"Timeout ao conectar ao Ollama: {str(e)}",
            )
        except Exception as e:
            log.error(f"Erro no proxy Ollama: {e}")
            raise HTTPException(status_code=500, detail=str(e))





@router.post("/proxy/chat")
async def proxy_chat_custom(request: Request, body: dict):
    """Chat com Ollama via proxy. Aceita _ollama_url no body."""
    target_url = body.get("_ollama_url") or body.get("ollama_url") or OLLAMA_BASE_URL
    
    if target_url and "localhost" in target_url:
        target_url = target_url.replace("localhost", "kothar_ollama")
        
    session_id = body.get("session_id") or body.get("_ollama_session") or "default"

    clean_body = {k: v for k, v in body.items() if k not in ["_ollama_url", "ollama_url"]}
    await inject_rag_into_messages(clean_body, session_id)

    # === AGENTIC TOOL CALLING LOOP ===
    from backend.core.tools import TOOLS_SCHEMA, execute_tool, format_tool_result
    
    # Prepara a chamada para avaliar ferramentas (sem stream)
    original_stream = clean_body.get("stream", True)
    
    # === REDUZ O CONTEXTO PARA AVALIACAO DE TOOLS ===
    # Enviar 20k chars + Tools faz o Ollama do Colab dar OOM/Crash (502 Ngrok).
    # Mandamos apenas as ultimas 3 mensagens para ele decidir a tool.
    tool_check_body = clean_body.copy()
    tool_check_body["stream"] = False
    tool_check_body["tools"] = TOOLS_SCHEMA
    
    # Filtra mensagens grandes de RAG/System para nao explodir o contexto
    safe_msgs = []
    for m in clean_body.get("messages", [])[-3:]:
        if m.get("role") == "system":
            continue # Ignora system gigantes
        if len(m.get("content", "")) > 1000:
            m = m.copy()
            m["content"] = m["content"][-1000:]
        safe_msgs.append(m)
        
    # Adiciona um system prompt minimalista instruindo sobre tools
    safe_msgs.insert(0, {
        "role": "system", 
        "content": "Voce e um assistente tecnico. O usuario vai pedir para ler arquivos ou codigo. Use as ferramentas adequadas se necessario. Se nao for necessario, apenas responda normal."
    })
    
    tool_check_body["messages"] = safe_msgs
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        url = f"{target_url.rstrip('/')}/api/chat"
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": "Kothar-LocalAI/1.0 (proxy)",
                "Content-Type": "application/json",
            }
            resp = await client.post(url, json=tool_check_body, headers=headers)
        except Exception as e:
            log.error(f"[{session_id[:8]}] Erro ao conectar no Ollama para tools: {e}")
            clean_body["stream"] = original_stream
            del clean_body["tools"]
            return await stream_chat_to(target_url, clean_body)
            
        if resp.status_code == 200:
            data = resp.json()
            message = data.get("message", {})
            
            if message.get("tool_calls"):
                log.info(f"[{session_id[:8]}] LLM invocou tools: {message['tool_calls']}")
                
                # Anexa a decisao (tool_calls) ao historico para o LLM ter o contexto
                clean_body["messages"].append(message)
                
                # Executa cada tool e anexa a resposta
                for tcall in message["tool_calls"]:
                    func = tcall.get("function", {})
                    name = func.get("name")
                    args = func.get("arguments", {})
                    
                    log.info(f"[{session_id[:8]}] Executando tool '{name}' com args: {args}")
                    result = execute_tool(name, args)
                    formatted_result = format_tool_result(result)
                    
                    clean_body["messages"].append({
                        "role": "tool",
                        "content": formatted_result,
                        "name": name
                    })
                
                # O Ollama precisa do schema de tools se enviarmos tool_calls no historico
                clean_body["tools"] = TOOLS_SCHEMA
                
                # Remove o RAG context gigante (Cofre) para nao explodir a memoria quando tools estao presentes
                clean_body["messages"] = [
                    m for m in clean_body["messages"] 
                    if m.get("role") != "system" or len(m.get("content", "")) < 1000
                ]
                
                # Restaura o stream para responder ao usuario com os resultados lidos
                clean_body["stream"] = original_stream
                return await stream_chat_to(target_url, clean_body)
            else:
                # O LLM NAO usou ferramentas. Como consumimos a resposta, enviamos em um unico chunk (fake stream).
                async def fake_stream():
                    d = json.dumps(data)
                    yield d.encode('utf-8') + b'\n'
                
                return StreamingResponse(fake_stream(), media_type="application/x-ndjson")
        else:
            log.warning(f"[{session_id[:8]}] Ollama tool-check error {resp.status_code}: {resp.text[:200]}")
            clean_body["stream"] = original_stream
            if "tools" in clean_body: del clean_body["tools"]
            return await stream_chat_to(target_url, clean_body)


@router.post("/proxy/chat_async")
async def proxy_chat_async(request: Request, body: dict):
    """Enfileira um chat para gerar em background"""
    target_url = body.get("_ollama_url") or body.get("ollama_url") or OLLAMA_BASE_URL
    if target_url and "localhost" in target_url:
        target_url = target_url.replace("localhost", "kothar_ollama")
        
    session_id = body.get("session_id") or body.get("_ollama_session")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    clean_body = {k: v for k, v in body.items() if k not in ["_ollama_url", "ollama_url"]}
    await inject_rag_into_messages(clean_body, session_id)

    # Inicia sessão
    worker_state.sessions[session_id] = {
        "history": [],
        "subscribers": [],
        "is_done": False,
        "metrics": None,
        "error": None
    }
    
    await worker_state.queue.put({
        "session_id": session_id,
        "target_url": target_url,
        "body": clean_body
    })
    
    return {"status": "queued", "session_id": session_id}

@router.get("/proxy/chat_stream/{session_id}")
async def proxy_chat_stream(session_id: str):
    """Lê os chunks ao vivo ou histórico se já acabou, via SSE"""
    sess = worker_state.sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Sessão não encontrada no worker")
        
    async def event_generator():
        # Envia histórico que já rolou
        for chunk in sess["history"]:
            yield f"data: {chunk}\n\n"
            
        if sess["is_done"]:
            return
            
        # Se não acabou, se inscreve pra receber novos
        q = asyncio.Queue()
        sess["subscribers"].append(q)
        try:
            while True:
                chunk = await q.get()
                yield f"data: {chunk}\n\n"
                try:
                    d = json.loads(chunk)
                    if d.get("done") or "error" in d:
                        break
                except:
                    pass
        finally:
            if q in sess["subscribers"]:
                sess["subscribers"].remove(q)
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def proxy_request_to(target_url: str, method: str, path: str, body: Optional[dict] = None):
    """Faz proxy para URL customizada."""
    url = f"{target_url.rstrip('/')}{path}"
    proxy_headers = {
        "Accept": "application/json",
        "User-Agent": "Kothar-LocalAI/1.0 (proxy)",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=proxy_headers)
            elif method == "POST":
                response = await client.post(url, json=body, headers=proxy_headers)
            else:
                raise HTTPException(status_code=405, detail=f"Método {method} não suportado")

            try:
                content = response.json() if response.content else {}
            except Exception as json_e:
                log.warning(f"Resposta não-JSON do Ollama ({response.status_code}): {response.text[:100]}")
                content = {"error": "Invalid JSON response", "raw": response.text[:200]}

            return JSONResponse(
                content=content,
                status_code=response.status_code,
            )
        except httpx.ConnectError as e:
            log.error(f"Erro de conexão com Ollama em {target_url}: {e}")
            return JSONResponse(
                status_code=502,
                content={"connected": False, "error": f"Não conectou em {target_url}", "models": []},
            )
        except Exception as e:
            log.error(f"Erro no proxy: {e}")
            return JSONResponse(
                status_code=500,
                content={"connected": False, "error": str(e), "models": []},
            )


async def stream_chat_to(target_url: str, body: dict):
    """Streaming chat para URL customizada."""
    url = f"{target_url.rstrip('/')}/api/chat"

    async def event_stream():
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    json=body,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Kothar-LocalAI/1.0 (proxy)",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception as e:
                error_json = json.dumps({"error": str(e)})
                yield error_json.encode()

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

