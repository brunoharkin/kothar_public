"""
=============================================================
 KOTHAR v4.0 — Session Compiler (Compilador de Sessão)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Ao fim de cada sessão: compila traces → relatório no Cofre.
 Ativa o Trace Analyser para detectar padrões de erro.
 Extrai aprendizados para cristalizar Skills futuras.
"""

import uuid
from typing import Any

from sqlalchemy import select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.memory.graph.graph_rag import graph_rag
from backend.memory.vault.vault_writer import vault_writer
from backend.trace.models import Session, Trace
from backend.trace.trace_analyser import trace_analyser

log = get_logger("trace.session_compiler")


class SessionCompiler:
    """
    Orquestra o fechamento completo de uma sessão:
    1. Busca todos os traces da sessão
    2. Busca arquivos modificados no GraphRAG
    3. Roda o Trace Analyser (detecta padrões de erro)
    4. Compila relatório e grava no Cofre (Obsidian)
    5. Retorna sumário para o Maestro
    """

    async def compile(self, session_id: str) -> dict[str, Any]:
        """
        Compila e persiste o relatório completo de uma sessão.
        Retorna sumário com path do relatório no Cofre.
        """
        log.info("Compilando sessão", session_id=session_id)

        # 1. Busca metadados da sessão
        session = await self._get_session(session_id)
        if not session:
            log.warn("Sessão não encontrada para compilação", session_id=session_id)
            return {"error": "Sessão não encontrada", "session_id": session_id}

        # 2. Busca todos os traces
        traces = await self._get_traces(session_id)

        # 3. Arquivos modificados (via GraphRAG)
        try:
            files_modified = await graph_rag.get_files_modified_in_session(session_id)
        except Exception as e:
            log.warn("Falha ao buscar arquivos do grafo", error=str(e))
            files_modified = []

        # 4. Skills usadas (extraídas dos metadados dos traces)
        skills_used = self._extract_skills_used(traces)

        # 5. Analisa erros e cria Travas
        analysis = await trace_analyser.analyse_session(session_id)

        # 6. Calcula totais
        tokens_total = sum(t.tokens_used or 0 for t in traces)
        errors_count = sum(1 for t in traces if t.is_error)

        # 7. Grava relatório no Cofre
        traces_dicts = [self._trace_to_dict(t) for t in traces]
        try:
            report_path = vault_writer.write_session_report(
                session_id=session_id,
                agent_name=session.agent_name,
                task_summary=session.task_summary or "Sessão sem título",
                traces=traces_dicts,
                files_modified=files_modified,
                skills_used=skills_used,
                tokens_total=tokens_total,
                cost_usd=float(session.total_cost_usd or 0),
                status=session.status,
            )
            vault_path = str(report_path)
        except Exception as e:
            log.error("Falha ao gravar relatório no Cofre", error=str(e))
            vault_path = None

        result = {
            "session_id": session_id,
            "agent_name": session.agent_name,
            "task_summary": session.task_summary,
            "status": session.status,
            "traces_count": len(traces),
            "files_modified": len(files_modified),
            "skills_used": skills_used,
            "tokens_total": tokens_total,
            "errors": errors_count,
            "locks_created": analysis.get("locks_created", 0),
            "vault_report": vault_path,
        }

        log.info(
            "✅ Sessão compilada com sucesso",
            session_id=session_id,
            traces=len(traces),
            vault_path=vault_path,
        )
        return result

    async def _get_session(self, session_id: str) -> Session | None:
        async with get_db_session() as db:
            result = await db.execute(
                select(Session).where(Session.id == uuid.UUID(session_id))
            )
            return result.scalar_one_or_none()

    async def _get_traces(self, session_id: str) -> list[Trace]:
        async with get_db_session() as db:
            result = await db.execute(
                select(Trace)
                .where(Trace.session_id == uuid.UUID(session_id))
                .order_by(Trace.sequence)
            )
            return result.scalars().all()

    def _extract_skills_used(self, traces: list[Trace]) -> list[str]:
        """Extrai nomes de skills dos metadados dos traces."""
        skills = set()
        for trace in traces:
            if trace.metadata_:
                skill = trace.metadata_.get("skill_used")
                if skill:
                    skills.add(skill)
        return sorted(skills)

    @staticmethod
    def _trace_to_dict(t: Trace) -> dict[str, Any]:
        return {
            "id": str(t.id),
            "sequence": t.sequence,
            "event_type": t.event_type,
            "agent_name": t.agent_name,
            "content": t.content,
            "tool_name": t.tool_name,
            "tokens_used": t.tokens_used,
            "is_error": t.is_error,
            "error_message": t.error_message,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }


# Instância singleton
session_compiler = SessionCompiler()
