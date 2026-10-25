"""
=============================================================
 KOTHAR v4.0 — Skill Trainer (Forjador de Skills)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Ao fim de uma sessão aprovada, o Maestro extrai o aprendizado
 e forja um Perfil Especialista (YAML + embedding ChromaDB).
 Próximas sessões invocam o Especialista com aquele manual perfeito.
"""

from typing import Any

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.memory.semantic.skill_embedder import skill_embedder
from backend.trace.trace_recorder import trace_recorder
from sqlalchemy import select

log = get_logger("engenheiro_kothar.skill_trainer")


class SkillTrainer:
    """
    Extrai aprendizado de sessões aprovadas e cristaliza Skills.

    Ciclo de aprendizado (ARQUITETURA_SUPER_RAG.md §3):
    1. Usuário aprova o resultado final da sessão
    2. O SkillTrainer analisa o que funcionou
    3. Extrai: passos, ferramentas, decisões, padrões
    4. Forja um YAML de skill via SkillEmbedder
    5. Próxima sessão similar: RAG Agêntico encontra a skill
    6. Agente especialista roda com custo mínimo de tokens
    """

    async def train_from_session(
        self,
        session_id: str,
        skill_name: str,
        skill_description: str,
        category: str,
        tags: list[str] | None = None,
        user_approved: bool = True,
    ) -> dict[str, Any]:
        """
        Forja uma skill a partir de uma sessão aprovada.

        Args:
            session_id: ID da sessão de origem
            skill_name: Nome descritivo da skill
            skill_description: O que esta skill resolve
            category: Categoria (frontend, backend, devops, etc.)
            tags: Tags para busca semântica
            user_approved: Se False, não cristaliza (sessão com erros)
        """
        if not user_approved:
            log.info("Sessão não aprovada — skill não cristalizada", session_id=session_id)
            return {"status": "skipped", "reason": "Sessão não aprovada pelo usuário"}

        log.info("Treinando skill a partir de sessão", session_id=session_id, skill=skill_name)

        # 1. Extrai traces bem-sucedidos da sessão
        steps, locks = await self._extract_patterns(session_id)

        if not steps:
            return {"status": "skipped", "reason": "Nenhum padrão extraível da sessão"}

        # 2. Forja a skill via SkillEmbedder
        skill_id = await skill_embedder.forge_from_session(
            session_id=session_id,
            name=skill_name,
            description=skill_description,
            category=category,
            steps=steps,
            tags=tags or [],
            locks=locks,
        )

        # 3. Registra a ação no trace
        await trace_recorder.record(
            session_id=session_id,
            event_type="skill_forged",
            agent_name="skill_trainer",
            content=f"Skill cristalizada: '{skill_name}' ({category})",
            tool_name="skill_embedder.forge_from_session",
            tool_output={
                "skill_id": skill_id,
                "skill_name": skill_name,
                "steps_count": len(steps),
                "locks_count": len(locks),
            },
        )

        log.info(
            "✅ Skill cristalizada com sucesso",
            skill_id=skill_id[:8],
            name=skill_name,
            steps=len(steps),
            locks=len(locks),
        )

        return {
            "status": "done",
            "skill_id": skill_id,
            "skill_name": skill_name,
            "category": category,
            "steps_extracted": len(steps),
            "locks_extracted": len(locks),
        }

    async def _extract_patterns(self, session_id: str) -> tuple[list[dict], list[str]]:
        """
        Extrai padrões de sucesso dos traces da sessão.
        Retorna (steps, locks).
        """
        from backend.trace.models import Trace
        import uuid

        async with get_db_session() as db:
            result = await db.execute(
                select(Trace)
                .where(Trace.session_id == uuid.UUID(session_id))
                .where(Trace.is_error == False)
                .order_by(Trace.sequence)
            )
            success_traces = result.scalars().all()

        steps = []
        locks = []

        for trace in success_traces:
            # Extrai passos das chamadas de ferramenta bem-sucedidas
            if trace.event_type == "tool_call" and trace.tool_name:
                steps.append({
                    "id": trace.sequence,
                    "action": f"Usar {trace.tool_name}",
                    "tool": trace.tool_name,
                    "description": (trace.content or "")[:200],
                    "duration_ms": trace.duration_ms,
                })

            # Extrai decisões como recomendações da skill
            elif trace.event_type == "decision" and trace.content:
                steps.append({
                    "id": trace.sequence,
                    "action": "Decisão arquitetural",
                    "description": trace.content[:200],
                })

        # Extrai locks dos traces de erro
        async with get_db_session() as db:
            result = await db.execute(
                select(Trace)
                .where(Trace.session_id == uuid.UUID(session_id))
                .where(Trace.is_error == True)
                .order_by(Trace.sequence)
            )
            error_traces = result.scalars().all()

        for trace in error_traces:
            if trace.error_message:
                locks.append(f"Evitar: {trace.error_message[:150]}")

        return steps[:20], locks[:5]  # limita para manter skill compacta


# Singleton
skill_trainer = SkillTrainer()
