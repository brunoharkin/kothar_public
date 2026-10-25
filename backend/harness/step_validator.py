"""
=============================================================
 KOTHAR v4.0 — Step Validator (Dependências e Locks)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Valida se um passo pode ser executado baseado em:
 - Dependências de outros passos
 - Locks ativos
 - Circuit breaker
"""

from typing import Any
from backend.core.logger import get_logger

log = get_logger("harness.step_validator")


# Mapeamento de dependências entre passos
# key = título do passo, value = lista de títulos que devem estar "done"
STEP_DEPENDENCIES: dict[str, list[str]] = {
    "Planejamento": ["Diagnóstico"],
    "Relational Experience Mapping": ["Diagnóstico"],
    "Verificação de Locks": [],
    "Busca de Skills": [],
    "Estrutura (Scaffold) & Portable Design": ["Planejamento"],
    "Auditoria de Passo (Supervisor)": ["Estrutura (Scaffold) & Portable Design"],
    "Copywriting (PAS/AIDA)": ["Planejamento"],
    "Diretrizes WebGL e Design": ["Planejamento"],
    "Execução Frontend": ["Auditoria de Passo (Supervisor)"],
    "Execução Backend": ["Auditoria de Passo (Supervisor)"],
    "Revisão de Código (Clean Code)": ["Execução Backend"],
    "Auditoria de Segurança": ["Revisão de Código (Clean Code)"],
    "QA": ["Auditoria de Segurança", "Execução Frontend"],
    "Containerização & Deploy": ["Auditoria de Segurança"],
    "Compilação": ["QA"],
}


class StepValidationResult:
    """Resultado da validação de um passo."""

    def __init__(
        self,
        can_execute: bool,
        reason: str = "",
        blocked_by: list[str] = None,
        locks_detected: list[dict] = None,
        circuit_open: bool = False,
    ):
        self.can_execute = can_execute
        self.reason = reason
        self.blocked_by = blocked_by or []
        self.locks_detected = locks_detected or []
        self.circuit_open = circuit_open

    def to_dict(self) -> dict:
        return {
            "can_execute": self.can_execute,
            "reason": self.reason,
            "blocked_by": self.blocked_by,
            "locks_detected": self.locks_detected,
            "circuit_open": self.circuit_open,
        }


class StepValidator:
    """
    Validador de passos do blueprint.

    Responsabilidades:
    1. Verificar dependências atendidas
    2. Verificar locks ativos
    3. Verificar circuit breaker
    4. Gerar razão clara do bloqueio
    """

    def __init__(self, session_id: str, blueprint: dict[str, Any], locks: list[dict] = None):
        self.session_id = session_id
        self.blueprint = blueprint
        self.locks = locks or []
        self._completed_steps: set[str] = set()

        # Popula passos concluídos
        for step in blueprint.get("steps", []):
            if step.get("status") == "done":
                self._completed_steps.add(step.get("title", ""))

    def validate(self, step: dict[str, Any], agent_name: str = None) -> StepValidationResult:
        """
        Valida se um passo pode ser executado.

        Args:
            step: O passo a validar
            agent_name: Nome do agente que executará (para circuit breaker)
        """
        step_title = step.get("title", "")
        step_id = step.get("id")

        # 1. Verifica se já foi executado
        if step.get("status") == "done":
            return StepValidationResult(
                can_execute=False,
                reason=f"Passo '{step_title}' já foi concluído",
            )

        # 2. Verifica se está em execução
        if step.get("status") == "in_progress":
            return StepValidationResult(
                can_execute=False,
                reason=f"Passo '{step_title}' já está em execução",
            )

        # 3. Verifica dependências
        deps_result = self._check_dependencies(step_title)
        if not deps_result["satisfied"]:
            return StepValidationResult(
                can_execute=False,
                reason=f"Dependências não atendidas para '{step_title}'",
                blocked_by=deps_result["missing"],
            )

        # 4. Verifica locks
        locks_result = self._check_locks(step)
        if locks_result["has_locks"]:
            return StepValidationResult(
                can_execute=False,
                reason=f"Locks ativos bloqueiam '{step_title}'",
                locks_detected=locks_result["locks"],
            )

        # 5. Verifica circuit breaker (checado na hora da execução)

        return StepValidationResult(
            can_execute=True,
            reason=f"Passo '{step_title}' pronto para execução",
        )

    def _check_dependencies(self, step_title: str) -> dict:
        """Verifica se as dependências estão atendidas."""
        required = STEP_DEPENDENCIES.get(step_title, [])

        if not required:
            return {"satisfied": True, "missing": []}

        missing = [dep for dep in required if dep not in self._completed_steps]

        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "required": required,
        }

    def _check_locks(self, step: dict) -> dict:
        """Verifica se há locks que afetam este passo."""
        step_title = step.get("title", "")
        step_desc = step.get("description", "")
        combined = f"{step_title} {step_desc}".lower()

        affected_locks = []

        for lock in self.locks:
            pattern = lock.get("metadata", {}).get("pattern", "").lower()
            if pattern and (pattern in combined or any(kw in combined for kw in pattern.split())):
                affected_locks.append(lock)

        return {
            "has_locks": len(affected_locks) > 0,
            "locks": affected_locks,
        }

    def get_executable_steps(self) -> list[dict]:
        """Retorna lista de passos que podem ser executados agora."""
        executable = []

        for step in self.blueprint.get("steps", []):
            if step.get("status") in ("done", "in_progress"):
                continue

            result = self.validate(step)
            if result.can_execute:
                executable.append(step)

        return executable

    def get_blocked_steps(self) -> list[dict]:
        """Retorna lista de passos bloqueados com motivo."""
        blocked = []

        for step in self.blueprint.get("steps", []):
            if step.get("status") in ("done", "in_progress"):
                continue

            result = self.validate(step)
            if not result.can_execute:
                blocked.append({
                    **step,
                    "block_reason": result.reason,
                    "blocked_by": result.blocked_by,
                    "locks_detected": result.locks_detected,
                })

        return blocked
