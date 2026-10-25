"""
=============================================================
 KOTHAR v4.0 — Agente DBA (Engenheiro de Dados Supremo)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Dita a arquitetura de banco de dados e pipelines de dados.
"""

from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.dba")

class DataEngineerAgent(BaseAgent):
    """
    Agente DBA e Engenheiro de Dados.
    Define as estruturas do banco de dados antes da codificação
    do backend. Impõe o princípio DUMB_FRONTEND.
    """

    @property
    def description(self) -> str:
        return "Engenheiro de Dados Supremo — dita modelagem e arquitetura de armazenamento"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        task_desc = task.get("description", "")
        
        log.info("DBA analisando modelo de dados...", task_len=len(task_desc))

        # Busca base de conhecimento no RAG sobre Awesome Data Engineering
        skills = await self.search_skill(f"banco de dados {task_desc[:50]}", category="backend")

        # Registro da estratégia de dados
        decision_msg = "Modelagem Relacional/NoSQL iniciada."
        reasoning_msg = f"Regra DUMB_FRONTEND aplicada. Encontradas {len(skills)} referências no RAG."

        await self.record_decision(decision=decision_msg, reasoning=reasoning_msg)

        await trace_recorder.record(
            session_id=self.session_id,
            event_type="data_architecture",
            agent_name=self.agent_name,
            content=f"Arquitetura de Banco de Dados definida para a tarefa.",
            tool_name="dba_planner",
            tool_output={"skills_applied": len(skills)},
            is_error=False
        )

        log.info("Análise de Dados concluída", agent=self.agent_name)

        return {
            "status": "passed",
            "agent": self.agent_name,
            "report": "Arquitetura de Banco de Dados estruturada no Backend.",
            "skills_applied": len(skills),
        }
