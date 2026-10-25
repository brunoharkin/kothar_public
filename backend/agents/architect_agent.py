"""
=============================================================
 KOTHAR v4.0 — Agente Arquiteto Supremo (Principal Engineer)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Responsável por: diagnóstico crítico, auditoria de viabilidade (Anti-Sycophant), 
 decomposição de tarefas amarrando UI ao Backend e Banco (No Dead Ends),
 planejamento estrutural e adoção de integrações MCP.
"""

from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.memory.cache.context_compressor import context_compressor
from backend.memory.graph.graph_rag import graph_rag
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.architect")


class ArchitectAgent(BaseAgent):
    """
    Agente Arquiteto Supremo — 'O Crítico de Software'.

    Responsabilidades:
    - Analisar estado atual do projeto via GraphRAG e System Design Primer.
    - Vetar tecnologias ruins, inseguras ou gambiarras.
    - Impor integrações via MCP (Model Context Protocol).
    - Amarrar Frontend (Botões) com Backend (APIs) e DBA (Tabelas).
    """

    @property
    def description(self) -> str:
        return "Arquiteto — analisa, planeja e cria blueprints estruturais"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        title       = task.get("title", "tarefa")
        description = task.get("description", "")
        files       = task.get("files_to_analyse", [])

        log.info("Arquiteto iniciando análise", task=title[:60])

        # 1. Verifica locks antes de qualquer coisa
        locks = await self.check_locks(description)
        if locks:
            await trace_recorder.record(
                session_id=self.session_id,
                event_type="architect_lock_warning",
                agent_name=self.agent_name,
                content=f"Arquiteto Supremo detectou {len(locks)} trava(s). O plano será rigidamente adaptado.",
            )

        # 2. Busca skill de planejamento no Cofre System Design
        skills = await self.search_skill(f"system design {title}", category="architecture")
        
        # 2.5 Validação Crítica (Anti-Sycophant & MCP)
        await self.record_decision(
            decision="Aplicando mandatos NO_DEAD_ENDS e MCP_FIRST.",
            reasoning="Garantindo que todos os botões UI possuam API e que dependências externas usem MCP seguro."
        )

        # 3. Analisa impacto no GraphRAG para cada arquivo relevante
        impact_reports = []
        for filepath in files[:5]:  # analisa até 5 arquivos
            try:
                impact = await graph_rag.get_impact_analysis(filepath)
                impact_reports.append(impact)
                await trace_recorder.record(
                    session_id=self.session_id,
                    event_type="impact_analysis",
                    agent_name=self.agent_name,
                    tool_name="graph_rag.get_impact_analysis",
                    tool_output=impact,
                )
            except Exception as e:
                log.warn("Falha na análise de impacto", file=filepath, error=str(e))

        # 4. Decompõe a tarefa em passos estruturados
        blueprint_steps = self._decompose(title, description, locks, skills)

        # 5. Atualiza contexto comprimido no Redis
        await context_compressor.update_status(self.session_id, "planejando", step=1)
        for file in files:
            await context_compressor.add_file(self.session_id, file)
        if skills:
            await context_compressor.add_skill(self.session_id, skills[0]["metadata"].get("name", ""))

        await self.record_decision(
            decision=f"Blueprint criado com {len(blueprint_steps)} passos para: {title}",
            reasoning=f"Locks: {len(locks)} | Skills encontradas: {len(skills)} | Impacto analisado: {len(impact_reports)} arquivos",
        )

        return {
            "status": "done",
            "agent": self.agent_name,
            "blueprint_steps": blueprint_steps,
            "impact_reports": impact_reports,
            "locks_found": len(locks),
            "skills_found": len(skills),
        }

    def _decompose(
        self,
        title: str,
        description: str,
        locks: list[dict],
        skills: list[dict],
    ) -> list[dict[str, Any]]:
        """Decompõe a tarefa em passos. Em produção: usa LLM para decomposição inteligente."""
        base = [
            {"id": 1, "title": "Verificar estado atual", "agent": "architect", "status": "pending"},
            {"id": 2, "title": f"Implementar: {title[:80]}", "agent": "engineer", "status": "pending"},
        ]

        if locks:
            base.insert(1, {
                "id": 1.5,
                "title": f"Contornar {len(locks)} trava(s) conhecida(s)",
                "agent": "engineer",
                "status": "pending",
                "locks": [l["metadata"] for l in locks],
            })

        base.append({"id": len(base) + 1, "title": "Auditoria de segurança", "agent": "security", "status": "pending"})
        base.append({"id": len(base) + 1, "title": "Validação QA",           "agent": "qa",       "status": "pending"})

        return base
