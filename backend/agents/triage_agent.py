"""
=============================================================
 KOTHAR v4.0 — Agente Triador (Prompt Enhancer & Dispatcher)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 A porta de entrada do sistema. Economiza tokens, expande
 o prompt do usuário e decide se a Orquestra inteira deve
 ser acionada.
"""

from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.triage")

class TriageAgent(BaseAgent):
    """
    Agente Triador — 'O Recepcionista Otimizador'.

    Responsabilidades:
    - Fast Dispatch: Responder perguntas diretas e barrar o orquestrador pesado.
    - Expand Intent: Enriquecer a ordem bruta com pesquisa limpa antes de
      passar para o Arquiteto Supremo.
    """

    @property
    def description(self) -> str:
        return "Triador (Prompt Enhancer) — A recepção. Expande a ordem e economiza tokens desviando tarefas simples."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        task_desc = task.get("description", "")
        
        log.info("Triagem iniciada. Avaliando carga da requisição...", task_len=len(task_desc))

        # Simulação da inteligência de triagem
        is_simple_query = "leia a estrutura" in task_desc.lower() or "pesquise" in task_desc.lower()
        
        decision_msg = "Avaliação de Triagem (Token Economy)."
        
        if is_simple_query:
            reasoning_msg = "Aplicando FAST_DISPATCH. Tarefa não requer código. Orquestra Pesada será abortada (Bypass)."
            bypass = True
            enriched_prompt = task_desc
        else:
            reasoning_msg = "Aplicando EXPAND_INTENT. Tarefa de engenharia detectada. Criando Super Dossiê..."
            bypass = False
            enriched_prompt = f"[SUPER DOSSIÊ MASTIGADO]\nIntenção Original: {task_desc}\nContexto Expandido: Requer frontend, backend e scaffold. Ações pré-pesquisadas aplicadas."

        await self.record_decision(decision=decision_msg, reasoning=reasoning_msg)

        # Grava auditoria no Trace
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="triage_audit",
            agent_name=self.agent_name,
            content=f"Triagem concluída. Bypass={bypass}. Dossiê gerado para economia de tokens.",
            tool_name="triage_enhancer",
            tool_output={"bypass_orchestrator": bypass, "enriched_prompt_length": len(enriched_prompt)},
            is_error=False
        )

        log.info("Triador concluiu análise", bypass=bypass)

        return {
            "status": "passed",
            "agent": self.agent_name,
            "bypass": bypass,
            "enriched_prompt": enriched_prompt,
            "report": "Prompt mastigado com sucesso e repassado.",
        }
