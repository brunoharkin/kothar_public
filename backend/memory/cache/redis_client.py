"""
=============================================================
 KOTHAR v4.0 — Redis Client (Cache de Curto Prazo)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Gerencia o estado dinâmico de blueprints e contexto comprimido.
 A LLM nunca lê o histórico inteiro — lê apenas o JSON do Redis.
"""

import json
from typing import Any

from backend.core.database import get_redis
from backend.core.exceptions import CacheError
from backend.core.logger import get_logger

log = get_logger("memory.cache.redis")

# Prefixos de chave para namespacing
KEY_BLUEPRINT = "kothar:blueprint:{session_id}"
KEY_CONTEXT   = "kothar:context:{session_id}"
KEY_LOCK      = "kothar:lock:{pattern_hash}"
KEY_SESSION   = "kothar:session:{session_id}"


class RedisMemory:
    """
    Interface de alto nível para o cache de curto prazo do Kothar.
    
    Padrão de uso:
        redis_mem = RedisMemory()
        await redis_mem.set_blueprint(session_id, {"tarefa": "criar botão", ...})
        blueprint = await redis_mem.get_blueprint(session_id)
    """

    def __init__(self, ttl_seconds: int = 0):
        """
        TTL 0 = eterno (não expira). Sessões devem ter memória permanente.
        Se quiser expirar cache temporário (ex: rate limit), passe ttl explícito.
        """
        self.ttl = ttl_seconds

    async def _client(self):
        return await get_redis()

    # ----------------------------------------------------------
    # Blueprint — Estado da tarefa atual
    # ----------------------------------------------------------

    async def set_blueprint(self, session_id: str, data: dict[str, Any]) -> None:
        """
        Salva o blueprint da tarefa atual no Redis.
        Os agentes especialistas leem apenas isso — não o chat inteiro.
        """
        try:
            r = await self._client()
            key = KEY_BLUEPRINT.format(session_id=session_id)
            await r.set(key, json.dumps(data, ensure_ascii=False), ex=self.ttl) if self.ttl else await r.set(key, json.dumps(data, ensure_ascii=False))
            log.debug("Blueprint salvo", session_id=session_id, keys=list(data.keys()))
        except Exception as e:
            raise CacheError(f"Falha ao salvar blueprint: {e}", {"session_id": session_id})

    async def get_blueprint(self, session_id: str) -> dict[str, Any] | None:
        """Recupera o blueprint da sessão atual."""
        try:
            r = await self._client()
            key = KEY_BLUEPRINT.format(session_id=session_id)
            raw = await r.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            raise CacheError(f"Falha ao ler blueprint: {e}", {"session_id": session_id})

    async def update_blueprint_step(
        self, session_id: str, step_id: int, status: str, result: Any = None
    ) -> None:
        """Atualiza status de um passo específico do blueprint."""
        blueprint = await self.get_blueprint(session_id)
        if not blueprint:
            raise CacheError("Blueprint não encontrado", {"session_id": session_id})
        
        steps = blueprint.get("steps", [])
        for step in steps:
            if step.get("id") == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                break
        
        await self.set_blueprint(session_id, blueprint)
        log.info("Passo atualizado", session_id=session_id, step_id=step_id, status=status)

    # ----------------------------------------------------------
    # Contexto Comprimido — Resumo para agentes especialistas
    # ----------------------------------------------------------

    async def set_context(self, session_id: str, context: dict[str, Any]) -> None:
        """
        Salva contexto comprimido para agentes especialistas.
        Formato esperado:
            {
                "tarefa_atual": "criar botão de login",
                "requisitos": "react, typescript, zod",
                "arquivos_relevantes": ["src/auth/Login.tsx"],
                "status": "em_progresso",
                "erros_anteriores": []
            }
        """
        try:
            r = await self._client()
            key = KEY_CONTEXT.format(session_id=session_id)
            await r.set(key, json.dumps(context, ensure_ascii=False), ex=self.ttl) if self.ttl else await r.set(key, json.dumps(context, ensure_ascii=False))
        except Exception as e:
            raise CacheError(f"Falha ao salvar contexto: {e}", {"session_id": session_id})

    async def get_context(self, session_id: str) -> dict[str, Any] | None:
        """Recupera o contexto comprimido da sessão."""
        try:
            r = await self._client()
            key = KEY_CONTEXT.format(session_id=session_id)
            raw = await r.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            raise CacheError(f"Falha ao ler contexto: {e}", {"session_id": session_id})

    # ----------------------------------------------------------
    # Sessão — Metadados rápidos
    # ----------------------------------------------------------

    async def set_session_meta(self, session_id: str, meta: dict[str, Any]) -> None:
        try:
            r = await self._client()
            key = KEY_SESSION.format(session_id=session_id)
            await r.set(key, json.dumps(meta, ensure_ascii=False), ex=self.ttl) if self.ttl else await r.set(key, json.dumps(meta, ensure_ascii=False))
        except Exception as e:
            raise CacheError(f"Falha ao salvar sessão: {e}", {"session_id": session_id})

    async def get_session_meta(self, session_id: str) -> dict[str, Any] | None:
        try:
            r = await self._client()
            key = KEY_SESSION.format(session_id=session_id)
            raw = await r.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            raise CacheError(f"Falha ao ler sessão: {e}", {"session_id": session_id})

    async def delete_session(self, session_id: str) -> None:
        """Remove todos os dados da sessão do cache."""
        r = await self._client()
        keys = [
            KEY_BLUEPRINT.format(session_id=session_id),
            KEY_CONTEXT.format(session_id=session_id),
            KEY_SESSION.format(session_id=session_id),
        ]
        await r.delete(*keys)
        log.info("Cache de sessão removido", session_id=session_id)
