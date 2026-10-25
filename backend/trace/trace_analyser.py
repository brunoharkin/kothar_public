"""
=============================================================
 KOTHAR v4.0 — Trace Analyser
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Analisa falhas nos traces e cristaliza Travas (Locks) no ChromaDB.
 Mandamento #4: 3 erros iguais → cria Trava para sessões futuras.
"""

import hashlib
import uuid
from collections import Counter
from typing import Any

from sqlalchemy import select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.memory.semantic.chroma_client import chroma_memory
from backend.trace.models import Lock, Trace

log = get_logger("trace.analyser")

# Limite de erros antes de criar uma Trava
MAX_ERRORS_BEFORE_LOCK = 3


class TraceAnalyser:
    """
    Analisa padrões de falha nos traces e cria Travas automáticas.
    
    Ciclo de aprendizado:
    1. Agente falha ao executar uma ação
    2. O erro é gravado no trace
    3. Se o mesmo erro ocorre 3x, o Analyser detecta
    4. Cria uma Trava no PostgreSQL + embedding no ChromaDB
    5. Próximas sessões consultam o ChromaDB antes de executar ações similares
    """

    async def analyse_session(self, session_id: str) -> dict[str, Any]:
        """
        Analisa os traces de uma sessão e cria Travas se necessário.
        Retorna relatório de análise.
        """
        log.info("Analisando traces da sessão", session_id=session_id)

        async with get_db_session() as db:
            result = await db.execute(
                select(Trace)
                .where(Trace.session_id == uuid.UUID(session_id))
                .where(Trace.is_error == True)
                .order_by(Trace.sequence)
            )
            error_traces = result.scalars().all()

        if not error_traces:
            log.info("Nenhum erro encontrado na sessão", session_id=session_id)
            return {"session_id": session_id, "errors": 0, "locks_created": 0}

        # Agrupa erros por padrão (tool_name + error_message normalizado)
        error_patterns = self._group_by_pattern(error_traces)
        locks_created = 0

        for pattern, traces_in_group in error_patterns.items():
            if len(traces_in_group) >= MAX_ERRORS_BEFORE_LOCK:
                lock_created = await self._create_lock(
                    pattern=pattern,
                    error_traces=traces_in_group,
                    session_id=session_id,
                )
                if lock_created:
                    locks_created += 1

        log.info(
            "Análise concluída",
            session_id=session_id,
            total_errors=len(error_traces),
            unique_patterns=len(error_patterns),
            locks_created=locks_created,
        )

        return {
            "session_id": session_id,
            "errors": len(error_traces),
            "unique_patterns": len(error_patterns),
            "locks_created": locks_created,
        }

    async def analyse_all_recent_errors(self, limit: int = 500) -> dict[str, Any]:
        """
        Analisa os erros mais recentes de todas as sessões.
        Detecta padrões globais que ocorrem em múltiplas sessões.
        """
        async with get_db_session() as db:
            result = await db.execute(
                select(Trace)
                .where(Trace.is_error == True)
                .order_by(Trace.created_at.desc())
                .limit(limit)
            )
            all_errors = result.scalars().all()

        error_patterns = self._group_by_pattern(all_errors)
        locks_created = 0

        for pattern, traces_in_group in error_patterns.items():
            if len(traces_in_group) >= MAX_ERRORS_BEFORE_LOCK:
                lock_created = await self._create_lock(
                    pattern=pattern,
                    error_traces=traces_in_group,
                    session_id=None,
                )
                if lock_created:
                    locks_created += 1

        return {
            "total_errors_analysed": len(all_errors),
            "unique_patterns": len(error_patterns),
            "locks_created": locks_created,
        }

    def _group_by_pattern(self, traces: list[Trace]) -> dict[str, list[Trace]]:
        """Agrupa traces de erro por padrão de falha."""
        groups: dict[str, list[Trace]] = {}
        for trace in traces:
            pattern = self._normalize_pattern(
                tool=trace.tool_name or "unknown",
                error=trace.error_message or "",
            )
            if pattern not in groups:
                groups[pattern] = []
            groups[pattern].append(trace)
        return groups

    @staticmethod
    def _normalize_pattern(tool: str, error: str) -> str:
        """Normaliza um padrão de erro para comparação."""
        # Remove detalhes específicos (IDs, caminhos) para agrupar padrões similares
        import re
        normalized = re.sub(r"/[\w/.-]+", "/PATH", error)  # remove paths
        normalized = re.sub(r"\b[0-9a-f-]{8,}\b", "ID", normalized)  # remove UUIDs
        normalized = re.sub(r"\d+", "N", normalized)  # remove números
        return f"{tool}::{normalized[:200]}"

    async def _create_lock(
        self,
        pattern: str,
        error_traces: list[Trace],
        session_id: str | None,
    ) -> bool:
        """
        Cria uma Trava no PostgreSQL e indexa no ChromaDB.
        Retorna True se criou nova trava, False se já existia.
        """
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()

        async with get_db_session() as db:
            # Verifica se já existe
            existing = await db.execute(
                select(Lock).where(Lock.chroma_doc_id == pattern_hash)
            )
            existing_lock = existing.scalar_one_or_none()

            if existing_lock:
                # Incrementa contagem
                existing_lock.trigger_count += len(error_traces)
                log.info("Trava existente incrementada", pattern=pattern[:60], count=existing_lock.trigger_count)
                return False

            # Cria nova trava
            tool_name = error_traces[0].tool_name or "unknown"
            error_msg = error_traces[0].error_message or "Erro desconhecido"
            alternative = self._suggest_alternative(tool_name, error_msg)

            description = (
                f"Ferramenta '{tool_name}' falhou {len(error_traces)}x com: {error_msg[:300]}"
            )

            lock = Lock(
                pattern=pattern[:500],
                description=description,
                alternative=alternative,
                chroma_doc_id=pattern_hash,
                trigger_count=len(error_traces),
                category=tool_name,
                source_session_id=uuid.UUID(session_id) if session_id else None,
                is_active=True,
            )
            db.add(lock)
            await db.flush()
            lock_id = str(lock.id)

        # Indexa no ChromaDB para busca semântica futura
        try:
            await chroma_memory.upsert_lock(
                lock_id=pattern_hash,
                pattern=pattern,
                description=description,
                alternative=alternative,
            )
        except Exception as e:
            log.warn("Falha ao indexar lock no ChromaDB", error=str(e))

        log.warn(
            "⛔ NOVA TRAVA CRIADA",
            pattern=pattern[:60],
            trigger_count=len(error_traces),
            lock_id=lock_id,
        )
        return True

    @staticmethod
    def _suggest_alternative(tool_name: str, error_message: str) -> str:
        """Sugere alternativa baseada no tipo de erro (determinístico)."""
        error_lower = error_message.lower()

        if "port" in error_lower and "in use" in error_lower:
            return "Verificar porta com 'lsof -i :PORTA' antes de usar. Trocar porta ou parar o processo."
        elif "permission denied" in error_lower:
            return "Verificar permissões do arquivo/diretório. Usar chmod ou executar com permissões adequadas."
        elif "module not found" in error_lower or "import error" in error_lower:
            return "Verificar se o pacote está instalado: pip install <pacote>. Verificar o ambiente virtual ativo."
        elif "connection refused" in error_lower or "connection error" in error_lower:
            return "Verificar se o serviço está rodando. Checar health check e logs do container."
        elif "timeout" in error_lower:
            return "Aumentar timeout ou verificar se o serviço está sobrecarregado."
        elif "not found" in error_lower or "404" in error_lower:
            return "Verificar se o recurso existe antes de acessar. Confirmar path ou ID."
        else:
            return f"Revisar o uso de '{tool_name}' com atenção ao erro: {error_message[:100]}"


# Instância singleton
trace_analyser = TraceAnalyser()
