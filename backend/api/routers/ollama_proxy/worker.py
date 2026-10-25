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


# --- Background Worker State ---
class ChatWorkerState:
    def __init__(self):
        self.sessions = {}
        self.queue = asyncio.Queue()

worker_state = ChatWorkerState()

async def ollama_background_worker():
    log.info("Iniciando Ollama Background Worker")
    while True:
        try:
            req = await worker_state.queue.get()
            session_id = req["session_id"]
            target_url = req["target_url"]
            body = req["body"]
            
            sess = worker_state.sessions.get(session_id)
            if not sess:
                worker_state.queue.task_done()
                continue

            # OLLAMA PROXY -> OPENAI PROXY
            import os
            openai_key = ""
            try:
                with open("/vault/OPENAI_API_KEY.env", "r") as f:
                    openai_key = f.read().replace("OPENAI_API_KEY=", "").strip()
            except:
                pass
                
            if not openai_key or openai_key == "sk-...":
                openai_key = os.environ.get("OPENAI_API_KEY", "")
                if openai_key == "sk-...":
                    openai_key = ""

            url = "https://api.openai.com/v1/chat/completions"
            
            # Fallback model se o router não definiu
            model_name = body.get("model", "gpt-4o-mini")
            if "kothar" in model_name.lower():
                model_name = "gpt-4o-mini"
                
            import time
            start_time = time.time()
            
            openai_body = {
                "model": model_name,
                "messages": body.get("messages", []),
                "stream": True,
                "stream_options": {"include_usage": True}
            }
            if "options" in body and "temperature" in body["options"]:
                openai_body["temperature"] = body["options"]["temperature"]

            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                try:
                    prompt_tokens = 0
                    completion_tokens = 0
                    
                    async with client.stream(
                        "POST",
                        url,
                        json=openai_body,
                        headers={"Authorization": f"Bearer {openai_key}", "Accept": "text/event-stream"}
                    ) as response:
                        if response.status_code != 200:
                            err_text = await response.aread()
                            raise Exception(f"OpenAI API Error {response.status_code}: {err_text}")
                            
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    data = json.loads(line[6:])
                                    
                                    # Extract usage if present
                                    if "usage" in data and data["usage"]:
                                        prompt_tokens = data["usage"].get("prompt_tokens", 0)
                                        completion_tokens = data["usage"].get("completion_tokens", 0)
                                        
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            chunk = json.dumps({"model": model_name, "message": {"role": "assistant", "content": content}, "done": False})
                                            sess["history"].append(chunk)
                                            for q in sess["subscribers"]:
                                                await q.put(chunk)
                                except Exception:
                                    pass
                        
                        duration_ns = int((time.time() - start_time) * 1e9)
                        
                        # Fallback for tokens if usage not returned
                        if prompt_tokens == 0:
                            prompt_tokens = sum(len(m.get("content", "")) for m in body.get("messages", [])) // 4
                        if completion_tokens == 0:
                            # We can estimate based on number of chunks, but since we didn't count chunks, just fallback to 0
                            pass

                        done_chunk = json.dumps({
                            "model": model_name, 
                            "done": True, 
                            "eval_count": completion_tokens, 
                            "prompt_eval_count": prompt_tokens,
                            "total_duration": duration_ns
                        })
                        sess["history"].append(done_chunk)
                        for q in sess["subscribers"]:
                            await q.put(done_chunk)
                        
                        sess["is_done"] = True
                        sess["metrics"] = {
                            "prompt_eval_count": prompt_tokens,
                            "eval_count": completion_tokens,
                            "total_duration": duration_ns
                        }
                except Exception as e:
                    error_json = json.dumps({"error": str(e), "done": True})
                    sess["history"].append(error_json)
                    sess["is_done"] = True
                    sess["error"] = str(e)
                    for q in sess["subscribers"]:
                        await q.put(error_json)
            
            # Auto-save trace
            if sess.get("is_done") and sess.get("metrics"):
                try:
                    full_text = ""
                    for line in sess["history"]:
                        try:
                            d = json.loads(line)
                            if "message" in d and "content" in d["message"]:
                                full_text += d["message"]["content"]
                            elif "response" in d:
                                full_text += d["response"]
                        except:
                            pass
                    
                    user_msg = ""
                    for m in reversed(body.get("messages", [])):
                        if m.get("role") == "user":
                            user_msg = m.get("content", "")
                            break
                    
                    async with httpx.AsyncClient() as c:
                        await c.post(
                            "http://localhost:8080/api/traces/",
                            json={
                                "session_id": session_id,
                                "event_type": "chat",
                                "agent_name": "kothar-local-ai",
                                "tool_name": body.get("model", "unknown"),
                                "tool_input": user_msg,
                                "tool_output": full_text,
                                "content": full_text,
                                "duration_ms": sess["metrics"].get("total_duration", 0) // 1000000,
                                "tokens_used": (sess["metrics"].get("prompt_eval_count", 0) or 0) + (sess["metrics"].get("eval_count", 0) or 0),
                                "tokens_input": sess["metrics"].get("prompt_eval_count", 0) or 0,
                                "tokens_output": sess["metrics"].get("eval_count", 0) or 0,
                                "is_error": False
                            }
                        )
                except Exception as db_e:
                    log.error(f"Erro ao salvar trace em background: {db_e}")
                    
            worker_state.queue.task_done()
        except Exception as e:
            log.error(f"Erro no background worker: {e}")
            await asyncio.sleep(1)

@router.on_event("startup")
async def start_worker():
    asyncio.create_task(ollama_background_worker())
    asyncio.create_task(memory_sweep_worker())

async def memory_sweep_worker():
    """
    Roda a cada 1 hora para marcar documentos expirados no ChromaDB.
    (Implementação nativa do Memanto)
    """
    import chromadb
    from datetime import datetime, timezone
    
    log.info("Iniciando Memory Sweep Worker (Memanto Nativado)")
    while True:
        try:
            client = chromadb.HttpClient(host="kothar_chromadb", port=8000)
            collections = client.list_collections()
            
            now_iso = datetime.now(timezone.utc).isoformat()
            
            for col in collections:
                try:
                    # ChromaDB metadata update: We query where expiry_date < now and status is not already expired
                    # ChromaDB only supports basic filtering. If we need date comparison, we might need to fetch all and filter in python.
                    results = col.get(include=["metadatas"])
                    ids_to_expire = []
                    new_metadatas = []
                    
                    if not results or not results.get("metadatas"):
                        continue
                        
                    for doc_id, meta in zip(results["ids"], results["metadatas"]):
                        if meta and meta.get("expiry_date") and meta.get("status") != "expired":
                            if meta["expiry_date"] < now_iso:
                                ids_to_expire.append(doc_id)
                                new_meta = meta.copy()
                                new_meta["status"] = "expired"
                                new_metadatas.append(new_meta)
                                
                    if ids_to_expire:
                        col.update(ids=ids_to_expire, metadatas=new_metadatas)
                        log.info(f"Sweep: {len(ids_to_expire)} memórias expiradas em {col.name}")
                except Exception as e:
                    log.error(f"Erro no sweep da collection {col.name}: {e}")
                    
        except Exception as e:
            log.error(f"Erro no memory sweep master: {e}")
            
        await asyncio.sleep(3600)  # Roda a cada 1 hora
