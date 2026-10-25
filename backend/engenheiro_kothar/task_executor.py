"""Liga as capacidades do mapa a agentes e operações reais, com falha fechada."""

import hashlib
from pathlib import Path

from pydantic import ValidationError

from backend.contracts.security import approved_result
from backend.contracts.task_execution import TaskExecutionPlan
from backend.core.workspace_files import (
    WorkspaceError,
    check_artifact,
    check_content,
    configured_workspace,
    read_workspace_file,
    relative_parts,
)
from backend.engenheiro_kothar.handoff import handoff
from backend.engenheiro_kothar.routing import route_task

SKILLS_ROOT = Path(__file__).resolve().parents[2] / ".agents" / "skills"


class RoutedTaskExecutor:
    """Executa apenas o mapa vigente e o plano tipado persistidos na sessão."""

    def __init__(self, blueprint: dict):
        self.blueprint = blueprint
        self.plan = TaskExecutionPlan.model_validate(blueprint.get("execution_plan") or {})
        self.root: Path | None = None
        self.skill_instructions: dict[str, str] = {}
        self.skill_hashes: dict[str, str] = {}

    def preflight(self) -> list[str]:
        routing = self.blueprint.get("routing")
        if not isinstance(routing, dict):
            return ["Blueprint legado sem mapa executável; gere um novo plano."]
        current = route_task(self.blueprint.get("description", ""), routing.get("requirements"))
        if current["blockers"]:
            return current["blockers"]
        expected = current["steps"]
        steps = self.blueprint.get("steps", [])
        fields = ("id", "agent", "capability", "skills", "depends_on")
        if not isinstance(steps, list) or len(steps) != len(expected) or any(
            not isinstance(step, dict) or any(step.get(key) != template.get(key) for key in fields)
            for step, template in zip(steps, expected, strict=True)
        ):
            return ["Etapas divergem do mapa de capacidades vigente."]
        agents = {step["agent"] for step in steps if step["capability"] == "file_operations"}
        if any(operation.agent not in agents for operation in self.plan.operations):
            return ["Operação atribuída a agente fora do escopo selecionado."]
        if any(not any(operation.agent == agent for operation in self.plan.operations) for agent in agents):
            return ["Plano sem operações executáveis para cada agente de implementação."]
        if any(not any(operation.agent == agent and operation.action != "read_file"
                       for operation in self.plan.operations) for agent in agents):
            return ["Artefato não verificável: leitura isolada não implementa alteração."]
        if not self.plan.operations and not self.plan.files:
            return ["Plano sem arquivos definidos para execução ou verificação."]
        try:
            self.root = configured_workspace()
            for path in self.relative_files:
                relative_parts(path)
                candidate = self.root / path
                if not candidate.resolve().is_relative_to(self.root):
                    raise WorkspaceError("Arquivo fora do workspace de execução.")
                if any(parent.is_symlink() for parent in [candidate, *candidate.parents]
                       if parent.is_relative_to(self.root)):
                    raise WorkspaceError("Links simbólicos não são permitidos no plano.")
            for operation in self.plan.operations:
                if operation.agent == "frontend" and operation.path.startswith("backend/"):
                    raise WorkspaceError("Operação frontend fora de sua camada.")
                if operation.agent == "backend" and operation.path.startswith("frontend/"):
                    raise WorkspaceError("Operação backend fora de sua camada.")
                check_content(operation.content)
            self._validate_operation_preconditions(steps)
            for name in dict.fromkeys(name for step in steps for name in step["skills"]):
                path = SKILLS_ROOT / name / "SKILL.md"
                body = path.read_text(encoding="utf-8")
                if len(body.encode("utf-8")) > 100_000:
                    raise WorkspaceError("Skill acima do limite de instruções.")
                self.skill_instructions[name] = body
                self.skill_hashes[name] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        except (WorkspaceError, OSError, ValueError) as exc:
            return [str(exc) if isinstance(exc, WorkspaceError) else "Arquivos ou skills do plano indisponíveis."]
        return []

    def _validate_operation_preconditions(self, steps: list[dict]) -> None:
        """Simula o plano inteiro em memória antes de permitir a primeira escrita."""
        virtual: dict[str, str | None] = {}
        planned_directories: set[str] = set()
        for step in steps:
            for operation in self.plan.operations:
                if operation.agent != step["agent"]:
                    continue
                path = operation.path
                candidate = self.root / path
                if path in planned_directories:
                    raise WorkspaceError("Plano inválido: caminho de arquivo também é usado como diretório.")
                for parent in candidate.parents:
                    if parent == self.root:
                        break
                    parent_path = str(parent.relative_to(self.root))
                    if virtual.get(parent_path) is not None:
                        raise WorkspaceError("Plano inválido: arquivo planejado usado como diretório.")
                    if parent.exists() and not parent.is_dir():
                        raise WorkspaceError("Diretório da operação é inválido.")
                    planned_directories.add(parent_path)
                if path not in virtual:
                    virtual[path] = read_workspace_file(self.root, path) if candidate.exists() else None
                original = virtual[path]
                if operation.action == "create_file":
                    if original is not None:
                        raise WorkspaceError("Criação recusada: arquivo já existe.")
                    updated = operation.content
                elif original is None:
                    raise WorkspaceError("Operação recusada: arquivo inexistente.")
                elif operation.action == "replace_text":
                    if hashlib.sha256(original.encode("utf-8")).hexdigest() != operation.expected_sha256:
                        raise WorkspaceError("Precondição de edição: SHA-256 divergente.")
                    occurrences = original.count(operation.old_text)
                    if occurrences != 1:
                        reason = "inexistente" if occurrences == 0 else "não é único"
                        raise WorkspaceError(f"Precondição de edição: trecho original {reason}.")
                    updated = original.replace(operation.old_text, operation.content, 1)
                else:
                    continue  # Leitura não muda o estado virtual.
                check_content(updated)
                check_artifact(updated, path, previous=original)
                virtual[path] = updated
        for path in self.plan.files:
            if path not in virtual:
                read_workspace_file(self.root, path)

    @property
    def relative_files(self) -> list[str]:
        return list(dict.fromkeys([operation.path for operation in self.plan.operations] + self.plan.files))

    async def __call__(self, step: dict, session_id: str, context: dict) -> dict:
        if self.root is None:
            return {"status": "blocked", "error": "Pré-validação obrigatória não executada."}
        common = {
            "title": step["title"],
            "description": step["description"],
            "project_root": str(self.root),
            "requires_frontend_verification": any(item["agent"] == "frontend" for item in self.blueprint["steps"]),
            "requires_auth_verification": bool(self.blueprint["routing"]["requirements"].get("authentication")),
            "skill_instructions": {name: self.skill_instructions[name] for name in step["skills"]},
        }
        if step["capability"] == "file_operations":
            operations = [operation for operation in self.plan.operations if operation.agent == step["agent"]]
            if not operations:
                return {"status": "blocked", "error": "Nenhuma operação para este agente."}
            evidence = []
            files_written = []
            for operation in operations:
                expected_content = operation.content
                if operation.action == "replace_text":
                    try:
                        original = read_workspace_file(self.root, operation.path)
                        if (hashlib.sha256(original.encode("utf-8")).hexdigest() != operation.expected_sha256
                                or original.count(operation.old_text) != 1):
                            raise WorkspaceError("Precondição de edição não atendida.")
                        expected_content = original.replace(operation.old_text, operation.content, 1)
                        check_artifact(expected_content, operation.path, previous=original)
                    except (WorkspaceError, OSError):
                        return {"status": "failed", "error": "Precondição de edição não atendida.",
                                "files_written": files_written}
                result = await handoff.delegate(
                    agent_name=step["agent"], session_id=session_id,
                    task={**common, **operation.model_dump(), "files": [operation.path]},
                )
                if not approved_result(result, "done"):
                    return {"status": "failed", "error": "Operação não foi concluída pelo agente.",
                            "files_written": files_written, "operation_results": evidence + [result]}
                try:
                    actual = read_workspace_file(self.root, operation.path)
                    digest = hashlib.sha256(actual.encode("utf-8")).hexdigest()
                    if operation.action == "read_file":
                        verified = result.get("files_read", {}).get(operation.path) == actual
                    else:
                        verified = (result.get("sha256") == digest
                                    and result.get("files_written") == [str(self.root / operation.path)]
                                    and actual == expected_content)
                    if not verified:
                        raise WorkspaceError("Artefato diverge da evidência retornada pelo agente.")
                except (WorkspaceError, OSError):
                    return {"status": "failed", "error": "Operação sem artefato verificável.",
                            "files_written": files_written}
                files_written.extend(result.get("files_written", []))
                evidence.append(result)
            output = {"status": "done", "files_written": files_written, "operation_results": evidence}
        elif step["capability"] in {"credential_scan", "qa_checks"}:
            files = [str(self.root / path) for path in self.relative_files]
            output = await handoff.delegate(
                agent_name=step["agent"], session_id=session_id,
                task={**common, "files": files, "expected_files": files,
                      "acceptance": step["acceptance"], "strict_artifact_checks": True},
            )
        else:
            return {"status": "blocked", "error": "Capacidade sem executor real."}
        # Carregar instruções é evidência de carregamento, não de aplicação ou aprovação.
        return {**output, "skills_loaded": {name: self.skill_hashes[name] for name in step["skills"]},
                "production_ready": False}


def prepare_task_executor(blueprint: dict) -> tuple[RoutedTaskExecutor | None, list[str]]:
    try:
        executor = RoutedTaskExecutor(blueprint)
        blockers = executor.preflight()
    except (ValidationError, TypeError, ValueError):
        return None, ["Plano de execução inválido."]
    return (None, blockers) if blockers else (executor, [])
