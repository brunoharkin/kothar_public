"""
=============================================================
 KOTHAR v6.0 — RAG Supremo
 Query expansion + re-ranking + 20-30 chunks ricos
 Substitui inject_rag_into_messages com versão suprema
=============================================================
"""
import os
import re
import hashlib
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger("kothar.rag_supremo")

# === CONFIGURAÇÕES DO RAG SUPREMO ===
RAG_N_RESULTS_PER_COLLECTION = 10   # antes era 3
RAG_MAX_TOTAL_CHUNKS = 30           # antes era 5
RAG_CHUNK_MAX_CHARS = 2000          # antes era 600
RAG_MIN_RELEVANCE_SCORE = 0.0       # ChromaDB distance (0=idêntico, 2=ortogonal)
RAG_DEDUP_OVERLAP_THRESHOLD = 0.85  # 85% overlap = duplicado
RAG_MAX_CONTEXT_CHARS = 50000       # limite total de chars injetados (~12k tokens)


def expand_query(user_msg: str) -> List[str]:
    """
    Gera variações semânticas da query para melhorar recall.
    Sem dependência de LLM — usa transformações léxicas determinísticas.
    """
    queries = [user_msg]

    # 1. lowercase
    lower = user_msg.lower().strip()
    if lower != user_msg:
        queries.append(lower)

    # 2. substituições semânticas básicas (português)
    substitutions = [
        (r"\bo que\b", "como funciona"),
        (r"\bcomo\b", "qual a forma de"),
        (r"\bpor que\b", "qual o motivo de"),
        (r"\bquando\b", "em que situação"),
        (r"\bonde\b", "em qual local"),
        (r"\bqual\b", "quais são os"),
    ]
    for pattern, replacement in substitutions:
        new_q = re.sub(pattern, replacement, lower, flags=re.IGNORECASE)
        if new_q != lower and new_q not in queries:
            queries.append(new_q)

    # 3. extrair palavras-chave principais
    keywords = re.findall(r"\b[a-zà-ú]{4,}\b", lower)
    if len(keywords) >= 2:
        kw_query = " ".join(keywords[:5])
        if kw_query not in queries:
            queries.append(kw_query)

    return queries[:5]  # máximo 5 variações


def _content_hash(chunk: str, length: int = 200) -> str:
    """Hash para deduplicação baseado em início do conteúdo."""
    normalized = re.sub(r"\s+", " ", chunk[:length].lower().strip())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def _is_duplicate(chunk: str, seen_hashes: set, threshold: float = 0.85) -> bool:
    """Detecta duplicatas por overlap de conteúdo."""
    h = _content_hash(chunk)
    if h in seen_hashes:
        return True
    seen_hashes.add(h)
    return False


def _rerank_chunks(chunks: List[str], sources: List[str], query: str) -> List[Tuple[str, str, float]]:
    """
    Re-ranking por:
    - overlap de keywords com a query
    - tamanho ideal do chunk (prefere 800-1500 chars)
    - diversity penalty (penaliza sources repetidas)
    """
    query_tokens = set(re.findall(r"\b[a-zà-ú]{3,}\b", query.lower()))

    source_counts = {}
    scored = []

    for chunk, source in zip(chunks, sources):
        chunk_tokens = set(re.findall(r"\b[a-zà-ú]{3,}\b", chunk.lower()))

        # Score 1: overlap de tokens
        overlap = len(query_tokens & chunk_tokens)
        overlap_score = overlap / max(len(query_tokens), 1)

        # Score 2: tamanho ideal (prefere 800-1500)
        size = len(chunk)
        if 800 <= size <= 1500:
            size_score = 1.0
        elif 400 <= size <= 2000:
            size_score = 0.7
        else:
            size_score = 0.4

        # Score 3: diversity (penaliza se já temos muitos chunks da mesma source)
        source_counts[source] = source_counts.get(source, 0) + 1
        diversity_score = 1.0 / source_counts[source]

        # Score final ponderado
        final = (overlap_score * 0.5) + (size_score * 0.3) + (diversity_score * 0.2)
        scored.append((chunk, source, final))

    # Ordenar por score (maior primeiro)
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored


async def rag_supremo(
    chroma_client,
    user_msg: str,
    collection_names: List[str],
    max_chunks: int = RAG_MAX_TOTAL_CHUNKS,
    max_chars: int = RAG_CHUNK_MAX_CHARS,
    max_context_chars: int = RAG_MAX_CONTEXT_CHARS,
) -> Tuple[List[str], List[str]]:
    """
    RAG Supremo:
    1. Query expansion (3-5 variações)
    2. Busca n_results=10 por collection
    3. Deduplicação
    4. Re-ranking
    5. Truncamento por limite total de contexto

    Returns: (chunks, sources)
    """
    if not user_msg or len(user_msg) < 5:
        return [], []

    expanded_queries = expand_query(user_msg)
    all_chunks = []
    all_sources = []
    seen_hashes = set()

    try:
        for collection_name in collection_names:
            try:
                col = chroma_client.get_collection(collection_name)
            except Exception:
                continue

            for query in expanded_queries:
                try:
                    results = col.query(
                        query_texts=[query],
                        n_results=RAG_N_RESULTS_PER_COLLECTION,
                        where={"status": {"$ne": "expired"}}
                    )
                except Exception as e:
                    logger.debug(f"Query falhou em {collection_name}: {e}")
                    continue

                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(docs)

                for doc, meta, dist in zip(docs, metas, distances):
                    # Filtra por relevância (distance baixa = bom)
                    if dist > 1.5:
                        continue

                    # Filtra duplicatas
                    if _is_duplicate(doc, seen_hashes):
                        continue

                    all_chunks.append(doc)
                    source = meta.get("filename", collection_name) if isinstance(meta, dict) else collection_name
                    all_sources.append(source)

        if not all_chunks:
            return [], []

        # Re-ranking
        ranked = _rerank_chunks(all_chunks, all_sources, user_msg)

        # Selecionar top N respeitando limite total de chars
        final_chunks = []
        final_sources = []
        total_chars = 0

        for chunk, source, score in ranked:
            if len(final_chunks) >= max_chunks:
                break

            truncated = chunk[:max_chars] if isinstance(chunk, str) else str(chunk)[:max_chars]

            if total_chars + len(truncated) > max_context_chars:
                # Se já temos pelo menos 5 chunks, para
                if len(final_chunks) >= 5:
                    break
                # Senão, trunca este
                remaining = max_context_chars - total_chars
                if remaining > 500:  # só adiciona se sobrar espaço útil
                    truncated = truncated[:remaining]
                else:
                    break

            final_chunks.append(truncated)
            final_sources.append(source)
            total_chars += len(truncated)

        logger.info(
            f"RAG Supremo: {len(expanded_queries)} queries × {len(collection_names)} collections "
            f"→ {len(all_chunks)} candidatos → {len(final_chunks)} finais ({total_chars} chars)"
        )

        return final_chunks, final_sources

    except Exception as e:
        logger.warning(f"RAG Supremo falhou: {e}")
        return [], []


def build_rag_context(chunks: List[str], sources: List[str]) -> str:
    """Constrói o bloco de contexto RAG formatado para o system prompt."""
    if not chunks:
        return ""

    rag_context = "\n\n# === CONTEXTO RAG SUPREMO ===\n"
    rag_context += f"Foram recuperados {len(chunks)} trechos candidatos do Cofre Kothar.\n"
    rag_context += (
        "Use-os como evidência contextual, não como verdade absoluta. "
        "Verifique consistência, atualidade e escopo; se houver conflito ou ausência de suporte, "
        "declare a incerteza e cite a fonte correspondente.\n\n"
    )

    for i, (chunk, source) in enumerate(zip(chunks, sources), 1):
        # Escape minimal para não quebrar o prompt
        clean_chunk = chunk.replace("```", "'''")
        rag_context += f"## [Fonte {i}] {source}\n{clean_chunk}\n\n"

    rag_context += "# === FIM DO CONTEXTO RAG ===\n\n"
    return rag_context
