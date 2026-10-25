"""
=============================================================
 KOTHAR v4.0 — Blueprint Manager
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Persiste e gerencia blueprints de tarefas no Redis + PostgreSQL.
 Mandamento #5: contexto base NUNCA modificado mid-task.
"""

import uuid
from typing import Any

from sqlalchemy import select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.memory.cache.redis_client import RedisMemory
from backend.trace.models import Blueprint

log = get_logger("engenheiro_kothar.blueprint_manager")


class BlueprintManager:
    """
    Gerencia blueprints de tarefas.

    Mandamento #5: o blueprint original é IMUTÁVEL durante execução.
    Alterações são feitas em cópias — o original é preservado para auditoria.
    """

    def __init__(self):
        self.redis = RedisMemory()

    async def create(
        self,
        session_id: str,
        title: str,
        description: str,
        steps: list[dict[str, Any]],
        assigned_agent: str = "engenheiro_kothar",
    ) -> dict[str, Any]:
        """Cria e persiste um novo blueprint no Redis e PostgreSQL."""
        blueprint_id = str(uuid.uuid4())
        blueprint = {
            "id": blueprint_id,
            "session_id": session_id,
            "title": title,
            "description": description,
            "steps": steps,
            "status": "active",
            "assigned_agent": assigned_agent,
            "_original_steps": steps,  # cópia imutável (Mandamento #5)
        }

        # Persiste no Redis (leitura rápida por agentes)
        await self.redis.set_blueprint(session_id, blueprint)

        # Persiste no PostgreSQL (auditoria permanente)
        async with get_db_session() as db:
            db.add(Blueprint(
                id=uuid.UUID(blueprint_id),
                session_id=uuid.UUID(session_id),
                title=title,
                description=description,
                steps=steps,
                status="active",
                assigned_agent=assigned_agent,
            ))

        log.info("Blueprint criado", blueprint_id=blueprint_id[:8], steps=len(steps), title=title[:60])
        return blueprint

    async def get(self, session_id: str) -> dict[str, Any] | None:
        """Lê blueprint do Redis (cache rápido)."""
        return await self.redis.get_blueprint(session_id)

    async def get_from_db(self, blueprint_id: str) -> Blueprint | None:
        """Lê blueprint do PostgreSQL (fonte de verdade permanente)."""
        async with get_db_session() as db:
            result = await db.execute(
                select(Blueprint).where(Blueprint.id == uuid.UUID(blueprint_id))
            )
            return result.scalar_one_or_none()

    async def update_step_status(
        self, session_id: str, step_id: Any, status: str, result: Any = None
    ) -> None:
        """
        Atualiza o status de um passo.
        NUNCA modifica _original_steps — apenas steps (cópia de trabalho).
        Mandamento #5.
        """
        blueprint = await self.get(session_id)
        if not blueprint:
            log.warn("Blueprint não encontrado para update", session_id=session_id)
            return

        modified = False
        for step in blueprint["steps"]:
            if str(step.get("id")) == str(step_id):
                step["status"] = status
                if result:
                    step["result"] = result
                modified = True
                break

        if modified:
            await self.redis.set_blueprint(session_id, blueprint)
            log.debug("Passo atualizado", session_id=session_id, step_id=step_id, status=status)

    async def mark_complete(self, session_id: str, status: str = "completed") -> None:
        """Marca o blueprint como concluído no PostgreSQL."""
        blueprint = await self.get(session_id)
        if not blueprint:
            return

        from datetime import datetime, timezone
        async with get_db_session() as db:
            result = await db.execute(
                select(Blueprint).where(Blueprint.id == uuid.UUID(blueprint["id"]))
            )
            bp = result.scalar_one_or_none()
            if bp:
                bp.status = status
                bp.steps = blueprint["steps"]
                bp.completed_at = datetime.now(timezone.utc)

        log.info("Blueprint finalizado", blueprint_id=blueprint["id"][:8], status=status)

    async def get_progress(self, session_id: str) -> dict[str, Any]:
        """Retorna progresso atual do blueprint."""
        blueprint = await self.get(session_id)
        if not blueprint:
            return {"error": "Blueprint não encontrado"}

        steps = blueprint.get("steps", [])
        total = len(steps)
        done  = sum(1 for s in steps if s.get("status") == "done")
        failed= sum(1 for s in steps if s.get("status") == "failed")

        return {
            "total":    total,
            "done":     done,
            "failed":   failed,
            "pending":  total - done - failed,
            "pct":      round(done / total * 100) if total else 0,
            "current":  next((s for s in steps if s.get("status") == "in_progress"), None),
        }


# Singleton
blueprint_manager = BlueprintManager()
