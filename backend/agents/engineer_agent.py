"""
=============================================================
 KOTHAR v4.0 — Agente Engenheiro (Executor de Código)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Executa o blueprint criado pelo Arquiteto.
 Lê o contexto comprimido do Redis — NUNCA o histórico inteiro.
 Registra cada arquivo modificado no GraphRAG.
"""

from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.core.workspace_files import (
    WorkspaceError,
    configured_workspace,
    create_workspace_file,
    read_workspace_file,
    replace_workspace_text,
)
from backend.memory.cache.context_compressor import context_compressor
from backend.memory.graph.graph_rag import graph_rag

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
            lock_alternatives = [lock["document"] for lock in locks[:2]]
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
            "create_file":   self._write_file,
            "replace_text":  self._replace_text,
            "read_file":     self._read_file,
            "run_command":   self._run_command,
            "install_package": self._install_package,
        }

        handler = action_map.get(action)
        if not handler:
            return {"status": "blocked", "files_written": [],
                    "error": "Ação executável desconhecida ou ausente."}

        return await handler(files=files, content=content, task=task)

    async def _write_file(self, files: list[str], content: str, task: dict) -> dict:
        """Cria um arquivo sem sobrescrever conteúdo existente."""
        if len(files) != 1:
            return {"status": "blocked", "files_written": [], "error": "Uma operação exige um arquivo."}
        try:
            root = configured_workspace()
            digest = create_workspace_file(root, files[0], content)
        except (WorkspaceError, OSError) as exc:
            message = str(exc) if isinstance(exc, WorkspaceError) else "Falha ao criar arquivo."
            return {"status": "blocked", "files_written": [], "error": message}
        return {"files_written": [str(root / files[0])], "sha256": digest}

    async def _replace_text(self, files: list[str], content: str, task: dict) -> dict:
        """Edita somente o trecho revisado, com precondição de conteúdo."""
        if len(files) != 1 or not task.get("expected_sha256") or not task.get("old_text"):
            return {"status": "blocked", "files_written": [], "error": "Edição exige arquivo, trecho e SHA-256."}
        try:
            root = configured_workspace()
            digest = replace_workspace_text(root, files[0], task["old_text"], content,
                                            task["expected_sha256"])
        except (WorkspaceError, OSError) as exc:
            message = str(exc) if isinstance(exc, WorkspaceError) else "Falha ao editar arquivo."
            return {"status": "blocked", "files_written": [], "error": message}
        return {"files_written": [str(root / files[0])], "sha256": digest}

    async def _read_file(self, files: list[str], content: str, task: dict) -> dict:
        """Lê arquivos e retorna conteúdo."""
        if len(files) != 1:
            return {"status": "blocked", "files_written": [], "error": "Uma operação exige um arquivo."}
        try:
            root = configured_workspace()
            value = read_workspace_file(root, files[0])
        except (WorkspaceError, OSError) as exc:
            message = str(exc) if isinstance(exc, WorkspaceError) else "Falha ao ler arquivo."
            return {"status": "blocked", "files_written": [], "error": message}
        return {"files_read": {files[0]: value}, "files_written": []}

    async def _run_command(self, files: list[str], content: str, task: dict) -> dict:
        """Nega shell arbitrário; comandos precisam de um executor tipado dedicado."""
        log.warning("Execução de shell negada", agent=self.agent_name)
        return {
            "files_written": [],
            "status": "blocked",
            "error": "Shell arbitrário desabilitado; use uma operação tipada e permitida",
        }

    async def _install_package(self, files: list[str], content: str, task: dict) -> dict:
        """Instala pacotes verificando requirements.txt primeiro."""
        package = content or task.get("package", "")
        req_file = Path("requirements.txt")

        # Verifica se já está listado
        if req_file.exists() and package in req_file.read_text():
            log.info("Pacote já no requirements.txt", package=package)
            return {"files_written": [], "message": f"{package} já declarado"}

        return {
            "files_written": [],
            "status": "blocked",
            "error": "Instalação automática desabilitada; declare e revise a dependência",
        }
