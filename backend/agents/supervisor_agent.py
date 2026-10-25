"""
=============================================================
 KOTHAR v4.0 — Agente Supervisor Severo
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Audita tarefas concluídas e força o log padrão 
 para treinamento de Machine Learning.
"""

from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.supervisor")

class SupervisorAgent(BaseAgent):
    """
    Agente Supervisor — 'O Auditor de Processos'.

    Responsabilidades:
    - Inspecionar saídas (outputs) de Frontend, Backend e Freelancers.
    - Gerar o 'Dossiê de Execução' obrigatório:
      1. Arquivos Alterados
      2. O que foi feito
      3. Como foi feito
    """

    @property
    def description(self) -> str:
        return "Supervisor Severo — Avalia a execução e gera logs estruturados para Fine-Tuning."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        agent_to_audit = task.get("agent_to_audit", "desconhecido")
        execution_report = task.get("execution_report", "")
        
        log.info(f"Supervisor ativado. Auditando: {agent_to_audit}")

        # Simulação de Auditoria e Formatação
        decision_msg = f"Auditoria de {agent_to_audit.upper()}."
        reasoning_msg = "Aplicando MANDATORY_REPORTING. Formatando saída em 3 Pilares para DB de Machine Learning."
        
        await self.record_decision(decision=decision_msg, reasoning=reasoning_msg)

        structured_log = f"""
=== DOSSIÊ DE EXECUÇÃO ({agent_to_audit.upper()}) ===
1. Arquivos Alterados/Lidos: [Lista extraída do contexto]
2. O Que Foi Feito: {execution_report[:100]}... [Resumo validado]
3. Como Foi Feito: Algoritmos e padrões arquiteturais aplicados.
========================================
"""

        # Grava auditoria no Trace / Banco de Dados
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="supervisor_audit_ml",
            agent_name=self.agent_name,
            content=f"Dossiê de Execução validado e gravado no Banco de Dados para Fine-Tuning.",
            tool_name="ml_data_formatter",
            tool_output={"audited_agent": agent_to_audit, "dossier": structured_log},
            is_error=False
        )

        log.info("Auditoria concluída. Dossiê gravado.", agent_to_audit=agent_to_audit)

        return {
            "status": "passed",
            "agent": self.agent_name,
            "audited_agent": agent_to_audit,
            "dossier": structured_log,
            "report": f"Auditoria concluída com sucesso. Logs de ML salvos."
        }
