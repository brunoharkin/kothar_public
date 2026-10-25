"""
=============================================================
 KOTHAR v4.0 — Context Compressor (Redis)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Comprime o histórico de conversas em um JSON leve.
 Agentes especialistas leem APENAS este resumo — nunca o chat inteiro.
 Economiza milhares de tokens por sessão.
"""

from typing import Any

from backend.core.logger import get_logger
from backend.memory.cache.redis_client import RedisMemory

log = get_logger("memory.cache.context_compressor")


class ContextCompressor:
    """
    Mantém o contexto comprimido da sessão no Redis.

    Formato padrão do contexto comprimido:
    {
        "tarefa_atual": "criar endpoint de autenticação JWT",
        "requisitos": ["FastAPI", "JWT", "PostgreSQL"],
        "arquivos_relevantes": ["backend/api/routers/auth.py"],
        "status": "em_progresso",      # planejando | em_progresso | revisando | concluido
        "passo_atual": 3,
        "total_passos": 8,
        "erros_anteriores": ["ImportError: jwt não instalado"],
        "skills_ativas": ["fastapi_jwt_auth"],
        "decisoes": ["usar python-jose para JWT"],
    }
    """

    def __init__(self):
        self.redis = RedisMemory()

    async def initialize(self, session_id: str, task: str, steps: list[dict]) -> None:
        """Inicializa o contexto comprimido de uma nova sessão."""
        context = {
            "tarefa_atual": task,
            "requisitos": [],
            "arquivos_relevantes": [],
            "status": "planejando",
            "passo_atual": 0,
            "total_passos": len(steps),
            "erros_anteriores": [],
            "skills_ativas": [],
            "decisoes": [],
        }
        await self.redis.set_context(session_id, context)
        log.info("Contexto inicializado", session_id=session_id, task=task[:60])

    async def get(self, session_id: str) -> dict[str, Any]:
        """Retorna o contexto atual. Retorna dict vazio se não existir."""
        ctx = await self.redis.get_context(session_id)
        return ctx or {}

    async def update_status(self, session_id: str, status: str, step: int | None = None) -> None:
        """Atualiza o status e passo atual."""
        ctx = await self.get(session_id)
        ctx["status"] = status
        if step is not None:
            ctx["passo_atual"] = step
        await self.redis.set_context(session_id, ctx)

    async def add_file(self, session_id: str, filepath: str) -> None:
        """Registra um arquivo como relevante para a tarefa."""
        ctx = await self.get(session_id)
        files = ctx.get("arquivos_relevantes", [])
        if filepath not in files:
            files.append(filepath)
            ctx["arquivos_relevantes"] = files[-20:]  # mantém os 20 mais recentes
        await self.redis.set_context(session_id, ctx)

    async def add_error(self, session_id: str, error: str) -> None:
        """Registra um erro ocorrido para evitar repetição."""
        ctx = await self.get(session_id)
        errors = ctx.get("erros_anteriores", [])
        errors.append(error[:200])
        ctx["erros_anteriores"] = errors[-5:]  # mantém os 5 mais recentes
        await self.redis.set_context(session_id, ctx)

    async def add_skill(self, session_id: str, skill_name: str) -> None:
        """Registra uma skill ativa na sessão."""
        ctx = await self.get(session_id)
        skills = ctx.get("skills_ativas", [])
        if skill_name not in skills:
            skills.append(skill_name)
        ctx["skills_ativas"] = skills
        await self.redis.set_context(session_id, ctx)

    async def add_decision(self, session_id: str, decision: str) -> None:
        """Registra uma decisão arquitetural tomada."""
        ctx = await self.get(session_id)
        decisions = ctx.get("decisoes", [])
        decisions.append(decision[:150])
        ctx["decisoes"] = decisions[-10:]
        await self.redis.set_context(session_id, ctx)

    async def add_requirement(self, session_id: str, req: str) -> None:
        """Adiciona um requisito técnico."""
        ctx = await self.get(session_id)
        reqs = ctx.get("requisitos", [])
        if req not in reqs:
            reqs.append(req)
        ctx["requisitos"] = reqs
        await self.redis.set_context(session_id, ctx)

    async def to_prompt_string(self, session_id: str) -> str:
        """
        Serializa o contexto em string otimizada para prompt de LLM.
        Use este método ao injetar contexto em agentes especialistas.
        """
        ctx = await self.get(session_id)
        if not ctx:
            return "Contexto: nenhum contexto disponível."

        lines = [
            f"=== CONTEXTO DA SESSÃO ===",
            f"Tarefa: {ctx.get('tarefa_atual', 'N/A')}",
            f"Status: {ctx.get('status', 'N/A')} (Passo {ctx.get('passo_atual', 0)}/{ctx.get('total_passos', 0)})",
        ]
        if ctx.get("requisitos"):
            lines.append(f"Requisitos: {', '.join(ctx['requisitos'])}")
        if ctx.get("arquivos_relevantes"):
            lines.append(f"Arquivos relevantes:\n" + "\n".join(f"  - {f}" for f in ctx["arquivos_relevantes"]))
        if ctx.get("skills_ativas"):
            lines.append(f"Skills ativas: {', '.join(ctx['skills_ativas'])}")
        if ctx.get("decisoes"):
            lines.append(f"Decisões tomadas:\n" + "\n".join(f"  - {d}" for d in ctx["decisoes"]))
        if ctx.get("erros_anteriores"):
            lines.append(f"⚠️ Erros anteriores (EVITAR):\n" + "\n".join(f"  - {e}" for e in ctx["erros_anteriores"]))
        lines.append("=========================")
        return "\n".join(lines)


# Singleton
context_compressor = ContextCompressor()
