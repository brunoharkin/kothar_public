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


async def inject_rag_into_messages(body: dict, session_id: str = "default") -> None:
    """
    KOTHAR v6.0 — RAG SUPREMO + MEMÓRIA DE CONVERSA

    Enriquece o system prompt com:
    1. Identidade do Kothar
    2. Memória de conversas anteriores (sumarizada)
    3. RAG Supremo (20-30 chunks, query expansion, re-ranking)
    4. Últimas mensagens integrais

    Quando o usuário faz uma pergunta ao modelo local, esta função:
    - Carrega memória persistente da sessão
    - Busca contexto RAG rico em todas as collections
    - Injeta tudo antes de enviar ao Ollama
    """
    try:
        messages = body.get("messages", [])
        if not messages:
            return

        # Pega a última mensagem do usuário
        user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        if not user_msg or len(user_msg) < 5:
            return

        log.info(f"[{session_id[:8]}] Processando: '{user_msg[:60]}'")

        # === [MELHORIA D] INTENT DETECTION ===
        intent = detect_intent(user_msg)
        intent_prompt = get_system_prompt_for_intent(intent)

        # === [MELHORIA C] QUERY DECOMPOSITION ===
        sub_queries = decompose_query(user_msg)
        primary_query = sub_queries[0] if sub_queries else user_msg

        # === [MELHORIA 9] INTERNET ACCESS ===
        internet_context = ""
        urls_in_msg = extract_urls(user_msg)
        if urls_in_msg:
            for url in urls_in_msg[:2]:
                log.info(f"[{session_id[:8]}] Fetching URL: {url}")
                fetch_result = await fetch_url(url, max_chars=4000)
                if fetch_result.get("ok"):
                    content = fetch_result.get("content", "")
                    internet_context += f"\n# === CONTEÚDO DA WEB: {url} ===\n{content[:4000]}\n# === FIM DA WEB ===\n"
                else:
                    internet_context += f"\n[Não foi possível acessar {url}: {fetch_result.get('error', 'erro desconhecido')}]\n"

        # Web search trigger
        if any(kw in user_msg.lower() for kw in ["busque por", "pesquise", "procure por", "o que há de novo"]):
            log.info(f"[{session_id[:8]}] Web search triggered")
            try:
                search_query = re.sub(r"^(busque por|pesquise|procure por)\s*", "", user_msg.lower()).strip()
                if not search_query:
                    search_query = user_msg
                results = await web_search(search_query, max_results=3)
                if results:
                    internet_context += f"\n# === RESULTADOS DE BUSCA WEB: '{search_query}' ===\n"
                    for r in results:
                        internet_context += f"- **{r['title']}** ({r['url']})\n  {r['snippet']}\n"
                    internet_context += "# === FIM DA BUSCA ===\n"
            except Exception as e:
                log.warning(f"Web search falhou: {e}")

        # === [MELHORIA 1] CONTEXT CACHE ===
        # Tenta usar cache antes de recalcular RAG
        cached = get_cached_context(session_id, user_msg, similarity_threshold=0.5)
        use_cache = cached is not None and not internet_context  # não usa cache se teve internet

        # === [MELHORIA 6] MULTI-MODEL ROUTER ===
        # Decide o melhor modelo baseado no intent
        user_model_override = body.get("model")
        model_choice, model_reason = route_model(
            user_msg=user_msg,
            intent=intent,
            user_override=user_model_override,
        )
        body["model"] = model_choice
        log.debug(f"[{session_id[:8]}] Router: {model_reason}")

        # === MEMÓRIA DE CONVERSA ===
        memory_context = ""
        memory_stats = {}
        try:
            memory = get_conversation_memory(session_id)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(memory.add_message_async("user", user_msg))
                else:
                    memory.add_message("user", user_msg)
            except RuntimeError:
                memory.add_message("user", user_msg)

            memory_context = memory.get_context()
            memory_stats = memory.get_stats()
        except Exception as e:
            log.warning(f"Memória indisponível: {e}")

        # === [MELHORIA 2] RAG HÍBRIDO (BM25 + semântico) ===
        rag_chunks = []
        chunk_sources = []

        # Se tem cache, usa direto
        if use_cache and cached:
            rag_chunks = cached["rag_chunks"]
            chunk_sources = cached["chunk_sources"]
            log.info(f"[{session_id[:8]}] Cache HIT: {len(rag_chunks)} chunks (sim={cached['similarity']:.2f})")
        else:
            try:
                import chromadb
                from backend.core.config import settings
                client = chromadb.HttpClient(
                    host='kothar_chromadb', 
                    port=8000,
                    headers={"Authorization": f"Bearer {settings.chroma_token}"}
                )
                available_collections = [c.name for c in client.list_collections()]

                # === [MELHORIA A] HYBRID SEARCH ===
                # Pega resultados com metadata para filter_by_category
                hybrid_results = []
                for col_name in available_collections:
                    try:
                        col = client.get_collection(col_name)
                        r = col.query(
                            query_texts=[primary_query],
                            n_results=30,
                            include=["documents", "metadatas", "distances"],
                        )
                        docs = r.get("documents", [[]])[0]
                        metas = r.get("metadatas", [[]])[0]
                        dists = r.get("distances", [[]])[0]
                        for doc, meta, dist in zip(docs, metas, dists):
                            if doc and isinstance(doc, str) and len(doc) > 50:
                                md = meta if isinstance(meta, dict) else {}
                                source = md.get("filename", col_name)
                                hybrid_results.append((doc, source, md, dist))
                    except Exception:
                        pass

                if hybrid_results:
                    # Sort globally by ChromaDB semantic distance (lowest is best)
                    hybrid_results.sort(key=lambda x: x[3])
                    
                    # Aplica hybrid_search (BM25 + semântico)
                    sem_only = [(c, s) for c, s, m, d in hybrid_results]
                    reranked = hybrid_search(primary_query, sem_only, bm25_weight=0.3, semantic_weight=0.7)

                    # === [MELHORIA H] METADATA FILTERING ===
                    with_meta = []
                    for chunk_content, source, score in reranked:
                        meta = next((m for c, s, m, d in hybrid_results if c == chunk_content and s == source), {})
                        with_meta.append((chunk_content, source, score, meta))

                    filtered = filter_by_category(with_meta, primary_query, max_per_category=6)
                    rag_chunks = [c for c, s, sc, m in filtered]
                    chunk_sources = [s for c, s, sc, m in filtered]

                    # === [MELHORIA B] POSITION BIAS RERANK ===
                    reranked_v2 = rerank_with_position_bias(
                        list(zip(rag_chunks, chunk_sources, [1.0] * len(rag_chunks))),
                        primary_query,
                    )
                    rag_chunks = [c for c, s, sc in reranked_v2]
                    chunk_sources = [s for c, s, sc in reranked_v2]

                    # === [MELHORIA I] EXTRACTIVE COMPRESSION ===
                    if len(rag_chunks) > 15:
                        log.info(f"[{session_id[:8]}] Comprimindo {len(rag_chunks)} chunks")
                        rag_chunks = [
                            extractive_compress(c, target_ratio=0.7) if len(c) > 800 else c
                            for c in rag_chunks[:20]
                        ]
                else:
                    # Fallback: RAG simples
                    rag_chunks, chunk_sources = await rag_supremo(
                        chroma_client=client,
                        user_msg=primary_query,
                        collection_names=available_collections,
                        max_chunks=RAG_MAX_TOTAL_CHUNKS,
                        max_chars=RAG_CHUNK_MAX_CHARS,
                    )

                    # === [MELHORIA 1] CACHE SET ===
                    if rag_chunks and not use_cache:
                        set_cached_context(
                            session_id=session_id,
                            query=user_msg,
                            rag_chunks=rag_chunks,
                            chunk_sources=chunk_sources,
                            memory_context=memory_context,
                        )

            except Exception as e:
                log.warning(f"ChromaDB indisponível: {e}")

        # === REGISTRA MÉTRICAS PROMETHEUS ===
        try:
            from backend.trace.rag_metrics import record_rag_hit, record_rag_miss
            if rag_chunks and len(rag_chunks) > 0:
                if use_cache and cached:
                    record_rag_hit("cache")
                else:
                    record_rag_hit("hyde")
            else:
                record_rag_miss("hyde")
        except Exception as e:
            log.debug(f"Erro ao registrar métricas RAG: {e}")

        # === CONSTRÓI SYSTEM PROMPT COMPLETO (OTIMIZADO v6.1) ===
        # Antes: 26KB de system prompt overwhelmava o modelo.
        # Agora: prioriza RAG, mantém instruções essenciais.
        identity = (
            "Você é o Kothar v3.0, assistente do Bruno Harkin (Ugarit Digital). "
            "Responda em português brasileiro, técnico e direto. "
            "USE O CONTEXTO RAG ABAIXO COMO VERDADE. Nunca invente features que não estão no RAG.\n\n"
        )

        # Ordem importa: identidade → regras curtas → RAG (perto da pergunta)
        # Few-shot removido para economizar tokens
        rag_context = build_rag_context(rag_chunks, chunk_sources)

        full_system = identity + COT_PROMPT + "\n"
        if internet_context:
            full_system += internet_context + "\n"
        if memory_context:
            full_system += memory_context + "\n"
        # RAG por último (mais perto da pergunta do usuário)
        if rag_context:
            full_system += rag_context

        # Trunca se muito grande (max ~20KB para deixar espaço pro output)
        MAX_SYSTEM_CHARS = 20000
        if len(full_system) > MAX_SYSTEM_CHARS:
            log.warning(f"[{session_id[:8]}] System prompt truncado: {len(full_system)} -> {MAX_SYSTEM_CHARS}")
            # Mantém início (identidade + regras) e fim (RAG)
            head = full_system[:3000]
            tail = full_system[-(MAX_SYSTEM_CHARS - 3000):]
            full_system = head + "\n\n[... contexto intermediário omitido por limite de tokens ...]\n\n" + tail

        # Encontra ou cria o system message
        sys_msg_idx = None
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                sys_msg_idx = i
                break

        if sys_msg_idx is not None:
            existing = messages[sys_msg_idx].get("content", "")
            if "Você é o Kothar v3.0" not in existing:
                messages[sys_msg_idx]["content"] = full_system + existing
        else:
            messages.insert(0, {"role": "system", "content": full_system})

        body["messages"] = messages
        log.info(
            f"[{session_id[:8]}] Intent={intent}, RAG={len(rag_chunks)} chunks, "
            f"Memory={memory_stats.get('compression_count', 0)}, "
            f"Internet={'sim' if internet_context else 'não'}"
        )

        # Registra no tracker (direto em memória, sem HTTP)
        try:
            from backend.api.routers.rag_tracker import tracker
            tracker.record(
                session_id=session_id,
                query=user_msg,
                chunks=rag_chunks,
                sources=chunk_sources,
            )
        except Exception as e:
            log.debug(f"Falha tracker direto: {e}")

    except Exception as e:
        log.warning(f"Falha ao injetar RAG Supremo: {e}")

