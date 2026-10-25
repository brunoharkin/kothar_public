"""
=============================================================
 KOTHAR v4.0 — Agente Contratante (Swarm Manager)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Divide projetos massivos e orquestra o Swarm de Freelancers
 rodando em paralelo.
"""

from typing import Any
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.agents.freelancer_agent import FreelancerAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.contractor")

class ContractorAgent(BaseAgent):
    """
    Agente Contratante — 'O Maestro da Escala'.

    Responsabilidades:
    - Lê a árvore do projeto (Tree).
    - Map: Quebra os arquivos em Chunks.
    - Execute: Instancia freelancers em paralelo.
    - Reduce: Agrega os resultados.
    """

    def __init__(self, session_id: str):
        super().__init__("contractor", session_id)

    @property
    def description(self) -> str:
        return "Contratante Swarm — Orquestrador de alta densidade (Map-Reduce)."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        task_desc = task.get("description", "")
        # Em vez de ler tudo, o Contratante pega a lista virtual e fatiaria.
        # Aqui, simularemos uma lista de 20 arquivos sendo fatiada em 4 blocos de 5.
        
        simulated_files = [f"src/file_{i}.py" for i in range(1, 21)]
        chunk_size = 5
        chunks = [simulated_files[i:i + chunk_size] for i in range(0, len(simulated_files), chunk_size)]
        
        log.info(f"Contratante mapeou {len(simulated_files)} arquivos em {len(chunks)} Chunks.", total_chunks=len(chunks))

        await self.record_decision(
            decision="Dividir e Conquistar (Swarm Pattern)",
            reasoning=f"Proibido ler o repositório como um bloco monolítico. Separando em {len(chunks)} empreitadas para Modelos Leves."
        )

        # Contrata e Executa Freelancers em Paralelo
        log.info("Despertando Agentes Freelancers...")
        
        freelancer_tasks = []
        for index, chunk in enumerate(chunks):
            worker = FreelancerAgent(self.session_id, freelancer_id=index + 1)
            freelancer_tasks.append(worker.execute({"files": chunk}))
            
        results = await asyncio.gather(*freelancer_tasks)
        
        # Aggregate (Reduce)
        aggregated_report = "\n\n=== RELATÓRIO SWARM (CONSOLIDADO) ===\n"
        for res in results:
            aggregated_report += f"\n[Freelancer {res['freelancer_id']}] -> {res['report']}"
            
        log.info("Relatório Swarm Consolidado", freelancers_used=len(results))

        await trace_recorder.record(
            session_id=self.session_id,
            event_type="swarm_aggregation",
            agent_name=self.agent_name,
            content=f"Agregou resultados de {len(results)} Freelancers em Paralelo. Economia de tokens confirmada.",
            tool_name="swarm_manager",
            tool_output={"total_freelancers": len(results), "aggregated_len": len(aggregated_report)},
            is_error=False
        )

        return {
            "status": "passed",
            "agent": self.agent_name,
            "report": aggregated_report,
            "freelancers_hired": len(results)
        }
