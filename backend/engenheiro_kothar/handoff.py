"""
=============================================================
 KOTHAR v4.0 — Handoff (Passagem de Bastão entre Agentes)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Mandamento #3: Handoff explícito entre agentes.
 O Engenheiro Kothar usa este módulo para delegar tarefas
 e garantir que o contexto é passado corretamente.
"""

from typing import Any

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.engineer_agent import EngineerAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.security_agent import SecurityAgent
from backend.core.exceptions import AgentError
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("engenheiro_kothar.handoff")

# Registro de agentes disponíveis
AGENT_REGISTRY = {
    "architect": ArchitectAgent,
    "engineer":  EngineerAgent,
    "security":  SecurityAgent,
    "qa":        QAAgent,
}


class Handoff:
    """
    Gerencia a passagem de bastão entre agentes.

    Fluxo:
        orchestrator → architect  (análise + blueprint)
        architect    → engineer   (execução)
        engineer     → security   (auditoria isolada)
        security     → qa         (validação)
        qa           → orchestrator (entrega)
    """

    async def delegate(
        self,
        agent_name: str,
        session_id: str,
        task: dict[str, Any],
        from_agent: str = "engenheiro_kothar",
    ) -> dict[str, Any]:
        """
        Delega uma tarefa para um agente específico.
        Registra o handoff no trace antes e depois.
        """
        if agent_name not in AGENT_REGISTRY:
            raise AgentError(
                f"Agente '{agent_name}' não registrado.",
                {"available": list(AGENT_REGISTRY.keys())},
            )

        # Registra o handoff no trace
        await trace_recorder.record(
            session_id=session_id,
            event_type="handoff",
            agent_name=from_agent,
            content=f"Handoff: {from_agent} → {agent_name} | Tarefa: {task.get('title', '')[:80]}",
            tool_name="handoff",
            tool_output={"to_agent": agent_name, "task_title": task.get("title", "")},
        )

        log.info(
            "🤝 Handoff",
            from_agent=from_agent,
            to_agent=agent_name,
            task=task.get("title", "")[:60],
        )

        # Instancia e executa o agente
        AgentClass = AGENT_REGISTRY[agent_name]
        agent = AgentClass(
            agent_name=agent_name,
            session_id=session_id,
        )

        result = await agent.run(task)

        # Registra conclusão do handoff
        await trace_recorder.record(
            session_id=session_id,
            event_type="handoff_complete",
            agent_name=agent_name,
            content=f"Handoff concluído: {agent_name} → {from_agent} | Status: {result.get('status', 'done')}",
            tool_output={"from_agent": agent_name, "status": result.get("status")},
        )

        return result

    async def run_pipeline(
        self,
        session_id: str,
        task_description: str,
        files: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Executa o pipeline completo de agentes para uma tarefa.

        Pipeline padrão:
        architect → engineer → security → qa
        """
        files = files or []
        results: dict[str, Any] = {}

        # Passo 1: Arquiteto cria o blueprint
        arch_result = await self.delegate(
            agent_name="architect",
            session_id=session_id,
            task={
                "title": task_description,
                "description": task_description,
                "files_to_analyse": files,
            },
        )
        results["architect"] = arch_result

        if arch_result.get("status") != "done":
            return {"status": "failed", "failed_at": "architect", "results": results}

        blueprint_steps = arch_result.get("blueprint_steps", [])

        # Passo 2: Engenheiro executa os passos do blueprint
        for step in blueprint_steps:
            if step.get("agent") != "engineer":
                continue
            eng_result = await self.delegate(
                agent_name="engineer",
                session_id=session_id,
                task={**step, "files": files},
            )
            results[f"engineer_step_{step['id']}"] = eng_result

        # Passo 3: Auditoria de segurança nos arquivos modificados
        sec_result = await self.delegate(
            agent_name="security",
            session_id=session_id,
            task={"title": "auditoria de segurança", "files": files},
        )
        results["security"] = sec_result

        if sec_result.get("status") == "failed":
            log.warn("Auditoria de segurança falhou", issues=len(sec_result.get("issues", [])))

        # Passo 4: QA
        qa_result = await self.delegate(
            agent_name="qa",
            session_id=session_id,
            task={"title": "validação QA", "files": files, "expected_files": files},
        )
        results["qa"] = qa_result

        overall_status = "completed" if qa_result.get("status") == "passed" else "completed_with_warnings"

        return {
            "status": overall_status,
            "pipeline": "architect → engineer → security → qa",
            "results": results,
        }


# Singleton
handoff = Handoff()
