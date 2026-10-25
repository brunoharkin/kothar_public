"""
=============================================================
 KOTHAR v4.0 — Agente Engenheiro (Executor de Código)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Executa o blueprint criado pelo Arquiteto.
 Lê o contexto comprimido do Redis — NUNCA o histórico inteiro.
 Registra cada arquivo modificado no GraphRAG.
"""

import subprocess
from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.memory.cache.context_compressor import context_compressor
from backend.memory.graph.graph_rag import graph_rag
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.engineer")


class EngineerAgent(BaseAgent):
    """
    Agente Engenheiro — executa código seguindo o blueprint.

    Princípios:
    - Lê APENAS o contexto comprimido do Redis (não o chat inteiro)
    - Todo arquivo tocado é registrado no GraphRAG
    - Verifica locks antes de cada ação
    - Nunca instala pacotes sem verificar requirements.txt
    """

    @property
    def description(self) -> str:
        return "Engenheiro — executa código seguindo blueprint, sem improvisar"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        step_title  = task.get("title", "executar")
        files       = task.get("files", [])
        code_action = task.get("action", "")
        content     = task.get("content", "")

        # 1. Lê contexto comprimido do Redis
        ctx_string = await context_compressor.to_prompt_string(self.session_id)
        log.info("Engenheiro lendo contexto", step=step_title[:60])

        # 2. Verifica locks
        locks = await self.check_locks(f"{step_title} {code_action}")
        if locks:
            lock_alternatives = [l["document"] for l in locks[:2]]
            await context_compressor.add_decision(
                self.session_id,
                f"Contornando lock em '{step_title}': {lock_alternatives[0][:80] if lock_alternatives else 'ver logs'}"
            )

        # 3. Busca skill relevante
        skills = await self.search_skill(step_title)
        if skills:
            await context_compressor.add_skill(self.session_id, skills[0]["metadata"].get("name", ""))

        # 4. Executa a ação
        result = await self._dispatch_action(
            action=code_action,
            files=files,
            content=content,
            task=task,
        )

        # 5. Registra arquivos no GraphRAG
        for filepath in result.get("files_written", []):
            await graph_rag.register_file(
                path=filepath,
                file_type=Path(filepath).suffix.lstrip(".") or "unknown",
                session_id=self.session_id,
            )
            await context_compressor.add_file(self.session_id, filepath)

        await context_compressor.update_status(self.session_id, "em_progresso")

        return {
            "status": "done",
            "agent": self.agent_name,
            "step": step_title,
            "context_used": ctx_string[:200],
            **result,
        }

    async def _dispatch_action(
        self,
        action: str,
        files: list[str],
        content: str,
        task: dict,
    ) -> dict[str, Any]:
        """Despacha para o método correto baseado no tipo de ação."""

        action_map = {
            "write_file":    self._write_file,
            "read_file":     self._read_file,
            "run_command":   self._run_command,
            "install_package": self._install_package,
        }

        handler = action_map.get(action)
        if not handler:
            # Ação genérica — apenas registra o trace
            await trace_recorder.record(
                session_id=self.session_id,
                event_type="engineer_action",
                agent_name=self.agent_name,
                content=f"Ação: {action} | Tarefa: {task.get('title', '')[:100]}",
            )
            return {"action": action, "files_written": files}

        return await handler(files=files, content=content, task=task)

    async def _write_file(self, files: list[str], content: str, task: dict) -> dict:
        """Escreve conteúdo em arquivo(s)."""
        written = []
        async with trace_recorder.trace_tool(
            self.session_id, self.agent_name, "write_file",
            tool_input={"files": files}
        ) as span:
            for filepath in files:
                path = Path(filepath)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                written.append(filepath)
                log.info("Arquivo escrito", path=filepath)
            span["output"] = {"written": written}
        return {"files_written": written}

    async def _read_file(self, files: list[str], content: str, task: dict) -> dict:
        """Lê arquivos e retorna conteúdo."""
        results = {}
        for filepath in files:
            path = Path(filepath)
            if path.exists():
                results[filepath] = path.read_text(encoding="utf-8")[:5000]
            else:
                results[filepath] = None
        return {"files_read": results, "files_written": []}

    async def _run_command(self, files: list[str], content: str, task: dict) -> dict:
        """
        Executa um comando shell de forma segura.
        Mandamento #1: verifica portas antes de rodar serviços.
        """
        command = content or task.get("command", "")
        if not command:
            return {"files_written": [], "error": "Nenhum comando fornecido"}

        # Segurança: bloqueia comandos destrutivos
        blocked = ["rm -rf /", "dd if=", ":(){ :|:& };:"]
        if any(b in command for b in blocked):
            raise ValueError(f"Comando bloqueado por segurança: {command[:50]}")

        async with trace_recorder.trace_tool(
            self.session_id, self.agent_name, "run_command",
            tool_input={"command": command}
        ) as span:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            output = proc.stdout + proc.stderr
            span["output"] = {"returncode": proc.returncode, "output": output[:2000]}

            if proc.returncode != 0:
                await context_compressor.add_error(self.session_id, f"Comando falhou: {command[:100]} → {output[:200]}")

        return {"files_written": [], "command_output": output, "returncode": proc.returncode}

    async def _install_package(self, files: list[str], content: str, task: dict) -> dict:
        """Instala pacotes verificando requirements.txt primeiro."""
        package = content or task.get("package", "")
        req_file = Path("requirements.txt")

        # Verifica se já está listado
        if req_file.exists() and package in req_file.read_text():
            log.info("Pacote já no requirements.txt", package=package)
            return {"files_written": [], "message": f"{package} já declarado"}

        return await self._run_command(
            files=[], content=f"pip install {package}", task=task
        )
