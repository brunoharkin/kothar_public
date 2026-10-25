"""Contratos executáveis do registry e das transições do Kothar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "configuracao" / "kothar-agent-registry.json"
TRANSITIONS_PATH = ROOT / "configuracao" / "kothar-transitions.json"

ALIASES = {
    "engenheiro_kothar": "core",
    "triage_agent": "triage",
    "frontend_engineer": "frontend",
    "backend_engineer": "backend",
    "structure_agent": "structure",
    "supervisor_agent": "supervisor",
    "code_reviewer": "code-reviewer",
    "ui_artist": "ui-artist",
    "data_engineer": "data-engineer",
}


class OrchestrationContractError(ValueError):
    """Contrato de orquestração inválido ou inconsistente."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestrationContractError(f"Não foi possível carregar {path}: {exc}") from exc


def available_agents() -> set[str]:
    registry = _load_json(REGISTRY_PATH)
    return set(registry.get("profiles", {}).get("full", []))


def resolve_agent_name(name: str) -> str:
    resolved = ALIASES.get(name, name)
    if resolved not in available_agents():
        raise OrchestrationContractError(
            f"Agente '{name}' não está no perfil full do registry "
            f"(resolvido: '{resolved}')."
        )
    return resolved


def validate_blueprint_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve aliases e rejeita passos sem agente verificável."""
    normalized: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            raise OrchestrationContractError("Cada passo do blueprint deve ser um objeto.")
        if "agent" not in step:
            raise OrchestrationContractError(
                f"Passo '{step.get('title', '<sem título>')}' não possui agente."
            )
        normalized_step = dict(step)
        normalized_step["agent"] = resolve_agent_name(str(step["agent"]))
        normalized.append(normalized_step)
    return normalized


def transition_contract() -> dict[str, Any]:
    """Retorna as transições declaradas após validar a estrutura mínima."""
    transitions = _load_json(TRANSITIONS_PATH)
    if not isinstance(transitions.get("transitions"), list):
        raise OrchestrationContractError("kothar-transitions.json não possui transitions.")
    return transitions
