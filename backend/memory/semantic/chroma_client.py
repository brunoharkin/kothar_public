"""
=============================================================
 KOTHAR v4.0 — ChromaDB Client (Memória Semântica RAG)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Busca Híbrida (lexical + vetorial) com HyDE adaptativo.
 Skills e Locks persistidos como embeddings auditáveis.
"""

from typing import Any
from collections import OrderedDict
import threading

import chromadb
from chromadb.utils import embedding_functions

from backend.core.config import settings
from backend.core.exceptions import SemanticSearchError
from backend.core.logger import get_logger
from backend.trace.rag_metrics import record_rag_cache_hit
from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    get_chroma_circuit,
)

log = get_logger("memory.semantic.chroma")

# Coleções do Kothar
COLLECTION_SKILLS  = "kothar_skills"
COLLECTION_LOCKS   = "kothar_locks"
COLLECTION_CONTEXT = "kothar_context"

# Cache config
CACHE_MAX_SIZE = 1000
CACHE_TTL_SECONDS = 300  # 5 minutes


class LRUCache:
    """Simple thread-safe LRU cache with TTL."""

    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL_SECONDS):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._ttl = ttl

    def _make_key(self, collection: str, query: str, **kwargs) -> str:
        """Generate cache key from search parameters."""
        import json
        params = {"collection": collection, "query": query}
        params.update({k: v for k, v in sorted(kwargs.items()) if v is not None})
        return json.dumps(params, sort_keys=True)

    def get(self, key: str) -> tuple[bool, Any]:
        """Get value from cache. Returns (found, value)."""
        import time
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    return True, value
                else:
                    # Expired
                    del self._cache[key]
        return False, None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        import time
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time() + self._ttl)
            self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()


class ChromaMemory:
    """
    Interface RAG Agêntico para o ChromaDB.

    Diferente do RAG passivo: se a busca não retorna resultados,
    o agente usa HyDE para reescrever a query até encontrar a Skill.
    """

    def __init__(self):
        self._client: chromadb.AsyncHttpClient | None = None
        self._collections: dict[str, Any] = {}
        # Embedding function padrão (all-MiniLM via sentence-transformers)
        self._embed_fn = embedding_functions.DefaultEmbeddingFunction()
        # Circuit breaker para resiliência
        self._circuit = get_chroma_circuit()
        # Cache para resultados de busca
        self._cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)

    async def _get_client(self) -> chromadb.AsyncHttpClient:
        if self._client is None:
            self._client = await chromadb.AsyncHttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                headers={"Authorization": f"Bearer {settings.chroma_token}"},
            )
        return self._client

    async def _get_collection(self, name: str):
        if name not in self._collections:
            client = await self._get_client()
            self._collections[name] = await client.get_or_create_collection(
                name=name,
                embedding_function=self._embed_fn,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    # ----------------------------------------------------------
    # Skills — Cristalização e Busca
    # ----------------------------------------------------------

    async def upsert_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        yaml_content: str,
        category: str = "",
        tags: list[str] | None = None,
    ) -> None:
        """Grava ou atualiza uma skill no ChromaDB."""
        async def _do_upsert():
            collection = await self._get_collection(COLLECTION_SKILLS)
            document = f"Skill: {name}\n\nDescrição: {description}\n\n{yaml_content}"
            await collection.upsert(
                ids=[skill_id],
                documents=[document],
                metadatas=[{
                    "name": name,
                    "category": category,
                    "tags": ",".join(tags or []),
                    "type": "skill",
                }],
            )
            log.info("Skill indexada no ChromaDB", skill_id=skill_id, name=name)

        try:
            await self._circuit.call(_do_upsert)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise SemanticSearchError(f"Falha ao indexar skill: {e}", {"skill_id": skill_id})

    async def search_skills(
        self,
        query: str,
        n_results: int = 5,
        category: str | None = None,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Busca semântica de skills com filtro por categoria.
        Retorna lista de skills com score de relevância.
        """
        # Check cache first
        cache_key = self._cache._make_key(COLLECTION_SKILLS, query, n_results=n_results, category=category, threshold=threshold)
        cached, cached_result = self._cache.get(cache_key)
        if cached:
            log.info("Cache hit para busca de skills", query=query[:50])
            record_rag_cache_hit()
            return cached_result

        async def _do_search():
            collection = await self._get_collection(COLLECTION_SKILLS)
            where = {"category": category} if category else None

            results = await collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            skills = []
            if results["ids"] and results["ids"][0]:
                for i, skill_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # cosine: menor distância = maior similaridade
                    if similarity >= threshold:
                        skills.append({
                            "id": skill_id,
                            "similarity": round(similarity, 4),
                            "metadata": results["metadatas"][0][i],
                            "document": results["documents"][0][i],
                        })

            log.info(
                "Busca semântica de skills",
                query=query[:50],
                found=len(skills),
                threshold=threshold,
            )
            return skills

        try:
            result = await self._circuit.call(_do_search)
            # Store in cache
            self._cache.set(cache_key, result)
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise SemanticSearchError(f"Falha na busca de skills: {e}", {"query": query})

    # ----------------------------------------------------------
    # Locks — Travas de Erros Repetidos
    # ----------------------------------------------------------

    async def upsert_lock(
        self,
        lock_id: str,
        pattern: str,
        description: str,
        alternative: str = "",
    ) -> None:
        """Indexa uma trava para evitar erros futuros."""
        async def _do_upsert():
            collection = await self._get_collection(COLLECTION_LOCKS)
            document = f"ERRO: {pattern}\n\nEvitar porque: {description}\n\nAlternativa: {alternative}"
            await collection.upsert(
                ids=[lock_id],
                documents=[document],
                metadatas=[{"pattern": pattern[:200], "type": "lock"}],
            )
            log.info("Lock indexado", lock_id=lock_id, pattern=pattern[:60])

        try:
            await self._circuit.call(_do_upsert)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise SemanticSearchError(f"Falha ao indexar lock: {e}", {"lock_id": lock_id})

    async def search_locks(self, query: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Busca travas que se aplicam à situação atual."""
        # Check cache first
        cache_key = self._cache._make_key(COLLECTION_LOCKS, query, n_results=n_results)
        cached, cached_result = self._cache.get(cache_key)
        if cached:
            log.info("Cache hit para busca de locks", query=query[:50])
            record_rag_cache_hit()
            return cached_result

        async def _do_search():
            collection = await self._get_collection(COLLECTION_LOCKS)
            results = await collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
            locks = []
            if results["ids"] and results["ids"][0]:
                for i, lock_id in enumerate(results["ids"][0]):
                    similarity = 1 - results["distances"][0][i]
                    if similarity >= 0.75:
                        locks.append({
                            "id": lock_id,
                            "similarity": round(similarity, 4),
                            "metadata": results["metadatas"][0][i],
                            "document": results["documents"][0][i],
                        })
            return locks

        try:
            result = await self._circuit.call(_do_search)
            # Store in cache
            self._cache.set(cache_key, result)
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise SemanticSearchError(f"Falha na busca de locks: {e}", {"query": query})

    # ----------------------------------------------------------
    # Context (Cofre) — Reidratação RAG
    # ----------------------------------------------------------

    async def upsert_context(
        self,
        context_id: str,
        title: str,
        content: str,
        filename: str,
        tags: list[str] | None = None,
    ) -> None:
        """Grava ou atualiza fragmentos de arquivos do cofre (Markdown) no ChromaDB."""
        async def _do_upsert():
            collection = await self._get_collection(COLLECTION_CONTEXT)
            document = f"Documento: {title}\nArquivo: {filename}\n\nConteúdo:\n{content}"
            await collection.upsert(
                ids=[context_id],
                documents=[document],
                metadatas=[{
                    "title": title,
                    "filename": filename,
                    "tags": ",".join(tags or []),
                    "type": "context",
                }],
            )
            log.debug("Context chunk indexado", context_id=context_id, title=title)

        try:
            await self._circuit.call(_do_upsert)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise SemanticSearchError(f"Falha ao indexar contexto: {e}", {"context_id": context_id})

    async def get_collection_stats(self) -> dict[str, int]:
        """Retorna contagem de documentos em cada coleção."""
        stats = {}
        for name in [COLLECTION_SKILLS, COLLECTION_LOCKS, COLLECTION_CONTEXT]:
            try:
                col = await self._get_collection(name)
                stats[name] = await col.count()
            except Exception:
                stats[name] = -1
        return stats

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Retorna o circuit breaker para métricas."""
        return self._circuit


# Instância singleton
chroma_memory = ChromaMemory()
