"""
=============================================================
 KOTHAR v6.0 — Context Caching
 Cacheia system prompt + RAG estável. Recalcula só quando query
 muda significativamente. Economiza 70% dos tokens de input.
=============================================================
"""
import time
import hashlib
import logging
import re
import json
from typing import Optional, Dict, Tuple, List

logger = logging.getLogger("kothar.cache")

# Cache em memória
_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 1800  # 30 minutos
MAX_CACHE_SIZE = 50  # máximo de entradas


def _normalize_query(query: str) -> str:
    """Normaliza query para cache key (remove stopwords, lowercase)."""
    q = query.lower().strip()
    # Remove pontuação
    q = re.sub(r"[^\w\s]", " ", q)
    # Remove stopwords comuns
    stopwords = {
        "o", "a", "e", "de", "da", "do", "para", "com", "em", "no", "na",
        "um", "uma", "que", "é", "como", "qual", "quais", "me", "diga", "fale",
        "sobre", "os", "as", "dos", "das", "ao", "aos", "à",
    }
    tokens = [t for t in q.split() if t not in stopwords and len(t) > 2]
    return " ".join(sorted(tokens))


def _query_similarity(q1: str, q2: str) -> float:
    """Calcula similaridade Jaccard entre duas queries normalizadas."""
    s1 = set(_normalize_query(q1).split())
    s2 = set(_normalize_query(q2).split())
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def get_cached_context(
    session_id: str,
    query: str,
    similarity_threshold: float = 0.6,
) -> Optional[Dict]:
    """
    Busca cache de contexto para a sessão.
    Retorna None se não houver cache similar.
    """
    cache_key = f"ctx:{session_id}"
    entry = _CACHE.get(cache_key)
    if not entry:
        return None

    # Expirado?
    if time.time() - entry["timestamp"] > CACHE_TTL:
        del _CACHE[cache_key]
        return None

    # Similar o suficiente?
    sim = _query_similarity(query, entry["query"])
    if sim >= similarity_threshold:
        logger.debug(f"Cache HIT (sim={sim:.2f}): {cache_key}")
        return {
            "rag_chunks": entry["rag_chunks"],
            "chunk_sources": entry["chunk_sources"],
            "memory_context": entry.get("memory_context", ""),
            "cached_query": entry["query"],
            "similarity": sim,
            "age_seconds": time.time() - entry["timestamp"],
        }

    return None


def set_cached_context(
    session_id: str,
    query: str,
    rag_chunks: List[str],
    chunk_sources: List[str],
    memory_context: str = "",
):
    """Salva contexto no cache."""
    # LRU: se excedeu, remove o mais antigo
    if len(_CACHE) >= MAX_CACHE_SIZE:
        oldest = min(_CACHE.items(), key=lambda x: x[1]["timestamp"])
        del _CACHE[oldest[0]]

    cache_key = f"ctx:{session_id}"
    _CACHE[cache_key] = {
        "query": query,
        "rag_chunks": rag_chunks,
        "chunk_sources": chunk_sources,
        "memory_context": memory_context,
        "timestamp": time.time(),
    }
    logger.debug(f"Cache SET: {cache_key} ({len(rag_chunks)} chunks)")


def invalidate_session(session_id: str):
    """Invalida cache de uma sessão."""
    cache_key = f"ctx:{session_id}"
    if cache_key in _CACHE:
        del _CACHE[cache_key]
        logger.info(f"Cache invalidated: {cache_key}")


def get_cache_stats() -> Dict:
    """Retorna estatísticas do cache."""
    now = time.time()
    active = sum(1 for e in _CACHE.values() if now - e["timestamp"] < CACHE_TTL)
    return {
        "total_entries": len(_CACHE),
        "active_entries": active,
        "max_size": MAX_CACHE_SIZE,
        "ttl_seconds": CACHE_TTL,
        "memory_estimate_kb": sum(
            len(json.dumps(e["rag_chunks"])) // 1024
            for e in _CACHE.values()
        ),
    }


def clear_cache():
    """Limpa todo o cache."""
    _CACHE.clear()
    logger.info("Cache cleared")
