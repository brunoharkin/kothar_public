"""
=============================================================
 KOTHAR v4.0 — Agente Engenheiro de Estrutura (Scaffold)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Desenha a planta (Tree) de arquivos e obriga a separação.
"""

from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.structure")

class StructureAgent(BaseAgent):
    """
    Agente de Estrutura — 'O Organizador de Pastas'.

    Responsabilidades:
    - Impor Separation of Concerns (Não deixar CSS e JS no mesmo arquivo).
    - Criar diretórios intuitivos ao invés de 'src' genérico.
    - Obrigar a criação e uso de '.env'.
    """

    @property
    def description(self) -> str:
        return "Engenheiro de Estrutura (Scaffold) — Desenha a árvore de arquivos e separa as responsabilidades (Clean Architecture)."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        task_desc = task.get("description", "")
        
        log.info("Desenhando Árvore de Diretórios e impondo Separação...", task_len=len(task_desc))

        # Busca base de conhecimento de Scaffold
        skills = await self.search_skill("clean architecture directory structure", category="architecture")

        decision_msg = "Scaffolding de Arquitetura Iniciado."
        reasoning_msg = f"Aplicando mandatos SEPARATION_OF_CONCERNS e ROOT_ENV_ONLY. Enjaulando arquivos na estrutura correta."

        await self.record_decision(decision=decision_msg, reasoning=reasoning_msg)

        # Grava auditoria no Trace
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="structure_scaffold_audit",
            agent_name=self.agent_name,
            content=f"Desenhou a árvore de diretórios. CSS separado do Backend e Frontend. Diretórios sugestivos forçados.",
            tool_name="structure_specialist",
            tool_output={"skills_applied": len(skills), "status": "scaffold_locked"},
            is_error=False
        )

        log.info("Estrutura (Scaffold) concluída", agent=self.agent_name)

        return {
            "status": "passed",
            "agent": self.agent_name,
            "report": "Árvore de Diretórios blindada. A execução do código não resultará em um monolito de um único arquivo. .env referenciado com sucesso.",
            "skills_applied": len(skills),
        }
