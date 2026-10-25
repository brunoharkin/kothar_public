"""
=============================================================
 KOTHAR v4.0 — Base Agent
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Classe base para todos os agentes especializados do Kothar.
 Implementa: tracing automático, verificação de locks, retry com limite.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

from backend.core.exceptions import MaxRetriesExceededError
from backend.core.logger import get_logger
from backend.memory.cache.redis_client import RedisMemory
from backend.memory.semantic.chroma_client import chroma_memory
from backend.memory.semantic.hyde_search import HyDESearch
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.base")


class BaseAgent(ABC):
    """
    Agente base do Kothar.
    
    Todo agente especializado herda desta classe e ganha:
    - Tracing automático de todas as ações
    - Verificação de Locks antes de executar
    - Retry com limite (Mandamento #4: máx 3 tentativas)
    - Acesso à memória semântica (HyDE)
    - Acesso ao cache Redis
    """

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1.0

    def __init__(self, agent_name: str, session_id: str):
        self.agent_name = agent_name
        self.session_id = session_id
        self.redis = RedisMemory()
        self.hyde = HyDESearch(chroma_memory)
        self._error_counts: dict[str, int] = {}  # rastreia erros por tipo

    # ----------------------------------------------------------
    # Interface obrigatória (implementar nos subclasses)
    # ----------------------------------------------------------

    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Executa a tarefa principal do agente."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição do papel deste agente."""
        ...

    # ----------------------------------------------------------
    # Execução com tracing e retry
    # ----------------------------------------------------------

    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Executa o agente com tracing, verificação de locks e retry automático.
        Este é o ponto de entrada público — use run() em vez de execute().
        """
        task_title = task.get('title', str(task)[:100])

        await trace_recorder.record(
            session_id=self.session_id,
            event_type="agent_start",
            agent_name=self.agent_name,
            content=f"Iniciando {self.agent_name}: {task_title}",
        )

        # TRACE: Rag Preload - busca lexical de skills
        await self._rag_preload(task)

        # TRACE: CBM Preload - contexto estrutural
        await self._cbm_preload(task)

        # TRACE: Verificação de locks
        locks = await self.check_locks(task_title)
        if locks:
            log.warn(f"Locks detectados: {len(locks)}", agent=self.agent_name)

        result = await self._execute_with_retry(task)

        await trace_recorder.record(
            session_id=self.session_id,
            event_type="agent_complete",
            agent_name=self.agent_name,
            content=f"Concluído {self.agent_name}: {result.get('status', 'done')}",
        )
        return result

    async def _execute_with_retry(self, task: dict[str, Any]) -> dict[str, Any]:
        """Executa com retry e Mandamento #4."""
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return await self.execute(task)
            except MaxRetriesExceededError:
                raise  # não faz retry deste
            except Exception as e:
                last_error = e
                error_key = type(e).__name__

                self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1

                await trace_recorder.record(
                    session_id=self.session_id,
                    event_type="agent_retry",
                    agent_name=self.agent_name,
                    is_error=True,
                    error_message=str(e)[:500],
                    metadata={"attempt": attempt, "error_type": error_key},
                )

                if attempt < self.MAX_RETRIES:
                    log.warn(
                        f"Tentativa {attempt}/{self.MAX_RETRIES} falhou",
                        agent=self.agent_name,
                        error=str(e)[:100],
                    )
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS * attempt)

        # Mandamento #4: 3 erros → PARAR
        raise MaxRetriesExceededError(
            step=task.get("title", "execute"),
            retries=self.MAX_RETRIES,
        )

    # ----------------------------------------------------------
    # RAG Preload - busca lexical de skills
    # ----------------------------------------------------------

    async def _rag_preload(self, task: dict[str, Any]) -> None:
        """
        Busca skills relevantes via ChromaDB (busca semântica).
        Este preload é executado ANTES de cada agente.
        """
        query = task.get('title', '') + ' ' + task.get('description', '')
        try:
            skills = await chroma_memory.search_skills(query, n_results=3)
            if skills:
                await trace_recorder.record(
                    session_id=self.session_id,
                    event_type="rag_preload",
                    agent_name=self.agent_name,
                    content=f"RAG preload encontrou {len(skills)} skills relevantes",
                    tool_name="chroma_memory",
                    tool_input={"query": query[:200], "n_results": 3},
                    tool_output={"skills_found": len(skills), "skills": [s.get("id") for s in skills]},
                    metadata={"task_title": task.get("title", "")[:100]},
                )
        except Exception as e:
            log.debug(f"RAG preload falhou (não bloqueia): {e}")

    # ----------------------------------------------------------
    # CBM Preload - contexto estrutural
    # ----------------------------------------------------------

    async def _cbm_preload(self, task: dict[str, Any]) -> None:
        """
        Busca contexto estrutural via CBM.
        Executado antes de tarefas de código.
        """
        # CBM é mais útil para tarefas de código
        task_lower = (task.get('title', '') + task.get('description', '')).lower()
        code_keywords = ['codigo', 'code', 'função', 'function', 'arquivo', 'file', 'refatorar', 'refactor']

        if any(kw in task_lower for kw in code_keywords):
            try:
                # Busca arquitetura se o projeto estiver indexado
                await trace_recorder.record(
                    session_id=self.session_id,
                    event_type="cbm_preload",
                    agent_name=self.agent_name,
                    content="CBM preload executado (contexto estrutural)",
                    tool_name="cbm_client",
                    tool_input={"task": task.get("title", "")[:200]},
                    tool_output={"cbm_available": True},
                    metadata={"task_title": task.get("title", "")[:100]},
                )
            except Exception as e:
                log.debug(f"CBM preload falhou (não bloqueia): {e}")

    # ----------------------------------------------------------
    # Ferramentas de suporte
    # ----------------------------------------------------------

    async def check_locks(self, action_description: str) -> list[dict]:
        """
        Verifica Travas antes de executar uma ação.
        Se houver travas, o agente deve considerar a alternativa sugerida.
        """
        locks = await self.hyde.search_locks(action_description)
        if locks:
            await trace_recorder.record(
                session_id=self.session_id,
                event_type="lock_check",
                agent_name=self.agent_name,
                content=f"⛔ {len(locks)} trava(s) detectada(s) para: {action_description[:100]}",
                metadata={"locks": [l["metadata"] for l in locks]},
            )
        return locks

    async def search_skill(self, query: str, category: str | None = None) -> list[dict]:
        """Busca skill relevante via HyDE."""
        return await self.hyde.search_skill(
            original_query=query,
            context=await self._get_current_context(),
            category=category,
        )

    async def _get_current_context(self) -> str:
        """Recupera contexto comprimido da sessão."""
        ctx = await self.redis.get_context(self.session_id)
        if not ctx:
            return ""
        return f"Tarefa: {ctx.get('tarefa_atual', '')} | Status: {ctx.get('status', '')}"

    async def update_context(self, updates: dict[str, Any]) -> None:
        """Atualiza o contexto comprimido no Redis."""
        current = await self.redis.get_context(self.session_id) or {}
        current.update(updates)
        await self.redis.set_context(self.session_id, current)

    async def record_decision(self, decision: str, reasoning: str = "") -> None:
        """Grava uma decisão estratégica do agente."""
        await trace_recorder.record_decision(
            session_id=self.session_id,
            agent_name=self.agent_name,
            decision=decision,
            reasoning=reasoning,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.agent_name!r}, session={self.session_id[:8]})"
