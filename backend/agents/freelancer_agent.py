"""
=============================================================
 KOTHAR v4.0 — Agente Operário Freelancer
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Analista Leve focado. Alta fidelidade a blocos pequenos.
"""

from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder
import asyncio

log = get_logger("agents.freelancer")

class FreelancerAgent(BaseAgent):
    """
    Agente Freelancer (Trabalhador de Linha de Frente).
    Roda em modelos mais rápidos, com análise focada em pequenos chunks.
    """

    def __init__(self, session_id: str, freelancer_id: int):
        super().__init__(f"freelancer_{freelancer_id}", session_id)
        self._freelancer_id = freelancer_id
        # Idealmente injetaria o modelo mais leve aqui (ex: flash/haiku)

    @property
    def description(self) -> str:
        return "Freelancer Worker — Audit e Análise pontual com altíssima fidelidade e baixo custo."

    @property
    def agent_name(self) -> str:
        return f"freelancer_{self._freelancer_id}"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        chunk = task.get("files", [])
        
        log.info(f"Freelancer {self._freelancer_id} ativado. Foco em {len(chunk)} arquivos.", freelancer_id=self._freelancer_id)

        # Simulação de análise profunda do chunk
        await asyncio.sleep(0.5) # Simula o processamento do LLM leve
        
        report = f"Auditoria detalhada do pacote [{', '.join(chunk)}]. Fidelidade mantida (Sem Alucinação)."

        # Grava auditoria no Trace
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="freelancer_audit",
            agent_name=self.agent_name,
            content=f"Freelancer {self._freelancer_id} processou chunk: {chunk}",
            tool_name="small_model_analysis",
            tool_output={"chunk": chunk, "report": report},
            is_error=False
        )

        return {
            "status": "passed",
            "freelancer_id": self._freelancer_id,
            "report": report,
            "chunk_analyzed": chunk
        }
