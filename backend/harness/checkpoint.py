"""
=============================================================
 KOTHAR v4.0 — Checkpoint Manager
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Salva estado do fluxo a cada passo executado.
 Permite recuperação após falhas ou reinicializações.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.core.logger import get_logger
from backend.memory.cache.redis_client import RedisMemory

log = get_logger("harness.checkpoint")


class CheckpointData:
    """Estrutura de um checkpoint."""

    def __init__(
        self,
        session_id: str,
        step_id: float,
        step_title: str,
        status: str,
        result: Any = None,
        error: str = None,
        timestamp: str = None,
        metadata: dict = None,
    ):
        self.session_id = session_id
        self.step_id = step_id
        self.step_title = step_title
        self.status = status  # "started", "done", "failed", "skipped", "locked"
        self.result = result
        self.error = error
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "step_id": self.step_id,
            "step_title": self.step_title,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointData":
        return cls(
            session_id=data.get("session_id", ""),
            step_id=data.get("step_id", 0),
            step_title=data.get("step_title", ""),
            status=data.get("status", "unknown"),
            result=data.get("result"),
            error=data.get("error"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )


class CheckpointManager:
    """
    Gerenciador de checkpoints do fluxo.

    Salva o estado a cada passo para permitir:
    - Recuperação após falhas
    - Análise de onde o fluxo parou
    - Reexecução a partir de um ponto
    """

    CHECKPOINT_TTL = 86400  # 24 horas

    def __init__(self):
        self.redis = RedisMemory()

    async def save_checkpoint(
        self,
        session_id: str,
        step_id: float,
        step_title: str,
        status: str,
        result: Any = None,
        error: str = None,
        metadata: dict = None,
    ) -> CheckpointData:
        """
        Salva um checkpoint.

        Args:
            session_id: ID da sessão
            step_id: ID do passo
            step_title: Título do passo
            status: "started" | "done" | "failed" | "skipped" | "locked"
            result: Resultado da execução (opcional)
            error: Mensagem de erro (opcional)
            metadata: Metadados adicionais (opcional)
        """
        checkpoint = CheckpointData(
            session_id=session_id,
            step_id=step_id,
            step_title=step_title,
            status=status,
            result=result,
            error=error,
            metadata=metadata,
        )

        # Salva no Redis com TTL
        key = f"kothar:checkpoint:{session_id}:{step_id}"
        r = await self.redis._client()

        # Armazena checkpoint individual
        await r.setex(key, self.CHECKPOINT_TTL, json.dumps(checkpoint.to_dict()))

        # Atualiza lista de checkpoints da sessão
        list_key = f"kothar:checkpoints:{session_id}"
        await r.zadd(list_key, {json.dumps(checkpoint.to_dict()): step_id})
        await r.expire(list_key, self.CHECKPOINT_TTL)

        # Atualiza checkpoint "current" da sessão
        current_key = f"kothar:current:{session_id}"
        await r.setex(current_key, self.CHECKPOINT_TTL, json.dumps({
            "step_id": step_id,
            "step_title": step_title,
            "status": status,
            "timestamp": checkpoint.timestamp,
        }))

        log.info(
            f"Checkpoint salvo: {step_title} -> {status}",
            session_id=session_id,
            step_id=step_id,
        )

        return checkpoint

    async def get_last_checkpoint(self, session_id: str) -> Optional[CheckpointData]:
        """Retorna o último checkpoint da sessão."""
        key = f"kothar:current:{session_id}"
        r = await self.redis._client()
        raw = await r.get(key)

        if not raw:
            return None

        data = json.loads(raw)
        return CheckpointData(
            session_id=session_id,
            step_id=data.get("step_id"),
            step_title=data.get("step_title"),
            status=data.get("status"),
            timestamp=data.get("timestamp"),
        )

    async def get_checkpoint_history(self, session_id: str) -> list[CheckpointData]:
        """Retorna histórico completo de checkpoints da sessão."""
        list_key = f"kothar:checkpoints:{session_id}"
        r = await self.redis._client()

        # Pega todos os checkpoints ordenados por step_id
        raw_list = await r.zrange(list_key, 0, -1)

        checkpoints = []
        for raw in raw_list:
            try:
                data = json.loads(raw)
                checkpoints.append(CheckpointData.from_dict(data))
            except json.JSONDecodeError:
                continue

        return checkpoints

    async def get_failed_checkpoint(self, session_id: str) -> Optional[CheckpointData]:
        """Retorna o último checkpoint com falha."""
        history = await self.get_checkpoint_history(session_id)

        for checkpoint in reversed(history):
            if checkpoint.status == "failed":
                return checkpoint

        return None

    async def can_resume_from_checkpoint(self, session_id: str) -> tuple[bool, str]:
        """
        Verifica se a sessão pode ser retomada de um checkpoint.

        Returns:
            (can_resume, reason)
        """
        last = await self.get_last_checkpoint(session_id)
        if not last:
            return False, "Nenhum checkpoint encontrado"

        if last.status == "failed":
            # Verifica se o erro foi recuperável
            return True, f"Pode retomar do passo '{last.step_title}'"

        if last.status == "done":
            return True, "Último passo concluído, pode continuar"

        return False, f"Checkpoint em estado inesperado: {last.status}"

    async def clear_checkpoints(self, session_id: str) -> None:
        """Remove todos os checkpoints da sessão."""
        r = await self.redis._client()
        keys = [
            f"kothar:checkpoint:{session_id}:*",
            f"kothar:checkpoints:{session_id}",
            f"kothar:current:{session_id}",
        ]

        for pattern in keys:
            if "*" in pattern:
                # Busca chaves que matcham o padrão
                cursor = 0
                while True:
                    cursor, keys_found = await r.scan(cursor, match=pattern, count=100)
                    if keys_found:
                        await r.delete(*keys_found)
                    if cursor == 0:
                        break
            else:
                await r.delete(pattern)

        log.info(f"Checkpoints removidos", session_id=session_id)


# Instância global
checkpoint_manager = CheckpointManager()
