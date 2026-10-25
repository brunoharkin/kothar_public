"""
=============================================================
 KOTHAR v4.0 — Agente Copywriter
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Responsável por: textos de vendas, CTAs, aplicação de frameworks
 PAS/AIDA e prevenção de AI Slop.
"""

from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.copywriter")


class CopywriterAgent(BaseAgent):
    """
    Agente Copywriter — 'Palavras que Convertem'.

    Responsabilidades:
    - Escrever H1s e textos de venda usando PAS/AIDA.
    - Evitar completamente "AI Slop" (textos genéricos).
    - Focar na dor do cliente e na persuasão.
    """

    @property
    def description(self) -> str:
        return "Copywriter — escreve textos de vendas, CTAs persuasivos e aplica frameworks de marketing"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        title = task.get("title", "tarefa de copy")
        description = task.get("description", "")
        
        log.info("Copywriter iniciando criação textual", task=title[:60])

        # 1. Verifica locks de copywriting
        locks = await self.check_locks(description)
        
        # 2. Busca regras e skills no RAG de Marketing
        skills = await self.search_skill(f"copywriting vendas {title}", category="copywriting")
        
        # 3. Execução do modelo (Mock estrutural para o orquestrador)
        # Em produção, usaria o LLM injetando os prompts do RAG
        await self.record_decision(
            decision=f"Textos e CTAs gerados para: {title}",
            reasoning=f"Regras de marketing aplicadas (Skills: {len(skills)}) e AI Slop filtrado.",
        )

        return {
            "status": "done",
            "agent": self.agent_name,
            "generated_copy": "Copy gerado (mock estrutural)",
            "locks_found": len(locks),
            "skills_applied": len(skills),
        }
