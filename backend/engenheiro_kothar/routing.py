"""Mapa declarativo de necessidades para passos com capacidades delimitadas.

Seleção de agentes e skills não é evidência de sua execução. Este módulo não
invoca modelos, ferramentas, scanners ofensivos ou implantação.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Scope = Literal["frontend", "backend", "fullstack", "security", "general"]
Agent = Literal["frontend", "backend", "engineer", "security", "qa"]
Capability = Literal["file_operations", "credential_scan", "qa_checks"]

ROOT = Path(__file__).resolve().parents[2]
ROUTING_MAP_PATH = ROOT / "configuracao" / "kothar-task-routing.json"
SKILLS_ROOT = ROOT / ".agents" / "skills"


class TaskRequirements(BaseModel):
    """Requisitos explícitos têm precedência sobre a inferência textual."""

    model_config = ConfigDict(extra="forbid", strict=True)

    scope: Scope | None = None
    backend_exists: bool = False
    authentication: bool | None = None
    persistence: bool = False
    external_api: bool = False


class _StepTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    capability: Capability
    skills: list[str]
    acceptance: list[str] = Field(min_length=1)


class _RoutingMap(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    selection_notice: str = Field(min_length=1)
    common_skills: list[str] = Field(min_length=1)
    routes: dict[Scope, list[Agent]]
    steps: dict[Agent, _StepTemplate]
    blocked_actions: dict[Literal["dast", "deployment"], str]

    @model_validator(mode="after")
    def validate_contract(self) -> _RoutingMap:
        expected_routes = {
            "frontend": ["frontend", "security", "qa"],
            "backend": ["backend", "security", "qa"],
            "fullstack": ["frontend", "backend", "security", "qa"],
            "security": ["security", "qa"],
            "general": ["engineer", "security", "qa"],
        }
        if self.routes != expected_routes:
            raise ValueError("Rotas devem preservar o contrato mínimo de agentes e gates")
        expected_capabilities = {
            "frontend": "file_operations", "backend": "file_operations",
            "engineer": "file_operations", "security": "credential_scan", "qa": "qa_checks",
        }
        if set(self.steps) != set(expected_capabilities):
            raise ValueError("Templates de agentes incompletos")
        if set(self.blocked_actions) != {"dast", "deployment"} or not all(self.blocked_actions.values()):
            raise ValueError("Ações excluídas precisam de motivos explícitos")
        titles = [step.title for step in self.steps.values()]
        if len(set(titles)) != len(titles):
            raise ValueError("Títulos devem ser únicos")
        required_common = {"kothar-workflow", "definition-of-done", "kothar-dod"}
        if not required_common.issubset(self.common_skills):
            raise ValueError("Skills comuns obrigatórias ausentes")
        mandatory = {
            "frontend": {"frontend-ugarit-ui", "motionsites", "amarracao-logica"},
            "backend": {"kothar-seguranca", "amarracao-logica"},
            "security": {"kothar-seguranca", "gate-seguranca-credenciais", "gate-producao"},
        }
        all_skills = set(self.common_skills) | {"playwright-verification"}
        for agent, step in self.steps.items():
            if step.capability != expected_capabilities[agent]:
                raise ValueError("Capacidade incompatível com agente")
            if not mandatory.get(agent, set()).issubset(step.skills):
                raise ValueError("Skills obrigatórias ausentes")
            if any(not criterion.strip() for criterion in step.acceptance):
                raise ValueError("Critérios de aceite não podem ser vazios")
            all_skills.update(step.skills)
        for skill in all_skills:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill):
                raise ValueError("Referência de skill inválida")
            skill_path = SKILLS_ROOT / skill / "SKILL.md"
            if not skill_path.is_file() or not skill_path.resolve().is_relative_to(SKILLS_ROOT.resolve()):
                raise ValueError("Skill referenciada indisponível")
        return self


def _normalized(task: str) -> str:
    return " ".join(
        "".join(char for char in unicodedata.normalize("NFKD", task.lower()) if not unicodedata.combining(char)).split()
    )


def _unsupported_action(task: str) -> str | None:
    # Frases expressas de ação; 'testar', 'url' e 'produção' isolados não
    # concedem nem solicitam capacidade ofensiva ou de implantação.
    if re.search(r"\b(?:dast|pentest|teste de invasao|teste de penetracao|penetration test)\b", task):
        return "dast"
    if re.search(r"\b(?:invadir|explorar vulnerabilidades|executar (?:o )?(?:nuclei|sqlmap))\b", task):
        return "dast"
    if re.search(r"\b(?:deploy|deployment|implantar em producao|publicar em producao|subir em producao)\b", task):
        return "deployment"
    return None


def _infer_requirements(task: str, supplied: TaskRequirements) -> tuple[TaskRequirements, str]:
    values = supplied.model_dump()
    explicit_scope = supplied.scope is not None
    backend_absent = bool(re.search(
        r"\b(?:sem (?:um |o )?(?:backend|back-end)|(?:backend|back-end) (?:ainda )?nao existe)\b", task
    ))
    backend_exists = supplied.backend_exists if "backend_exists" in supplied.model_fields_set else (
        not backend_absent and bool(re.search(
            r"\b(?:backend|back-end) (?:ja )?(?:existe|existente|pronto|disponivel)\b", task
        ))
    )
    values["backend_exists"] = backend_exists
    authentication = bool(re.search(r"\b(?:login|logout|autenticacao|autenticar|senha|sign in|sign-in)\b", task))
    if supplied.authentication is None:
        denied_auth = bool(re.search(
            r"\b(?:nao|sem) (?:implemente |implementar |crie |criar |adicione |adicionar |usar |use )?(?:a )?autenticacao(?: real)?\b",
            task,
        ))
        values["authentication"] = authentication and not denied_auth
    if explicit_scope:
        reason = "Escopo definido nos requisitos explícitos; inferência não altera a rota."
    else:
        frontend = bool(re.search(r"\b(?:frontend|front-end|pagina|interface|componente|tela|layout)\b", task))
        frontend_only = bool(re.search(r"\b(?:somente|apenas|so) (?:o |a )?(?:frontend|front-end|interface|tela)\b", task))
        backend = bool(re.search(r"\b(?:backend|back-end|endpoint|servidor)\b", task)) and not backend_exists
        fullstack = bool(re.search(r"\b(?:fullstack|full-stack)\b", task))
        complete_login = values["authentication"] and bool(re.search(r"\b(?:completo|completa)\b", task))
        if frontend_only or backend_exists and (frontend or authentication):
            scope = "frontend"
        elif fullstack or complete_login or backend and frontend:
            scope = "fullstack"
        elif backend:
            scope = "backend"
        elif frontend or authentication:
            scope = "fullstack" if supplied.persistence and not backend_exists else "frontend"
        elif supplied.persistence:
            scope = "backend"
        elif re.search(r"\b(?:auditoria de seguranca|revisao de seguranca|verificar credenciais)\b", task):
            scope = "security"
        else:
            scope = "general"
        values["scope"] = scope
        reason = "Escopo inferido de necessidade textual clara; pedido genérico usa rota geral sem especialidades extras."
    return TaskRequirements.model_validate(values), reason


def route_task(task: str, requirements: TaskRequirements | dict | None = None) -> dict:
    """Seleciona passos; capacidades externas excluídas bloqueiam sem execução.

    Entrada inválida gera ValidationError/ValueError para rejeição na fronteira
    da API. Configuração ausente ou inválida retorna uma rota sem passos.
    """
    if not isinstance(task, str) or not task.strip() or len(task) > 20000:
        raise ValueError("Tarefa deve conter entre 1 e 20000 caracteres")
    supplied = requirements if isinstance(requirements, TaskRequirements) else TaskRequirements.model_validate(
        {} if requirements is None else requirements
    )
    resolved, reason = _infer_requirements(_normalized(task), supplied)
    result = {
        "requirements": resolved.model_dump(), "route": resolved.scope,
        "reason": reason, "steps": [], "blockers": [],
        "selection_notice": "Seleção de skills não comprova execução ou aprovação de produção.",
    }
    try:
        routing_map = _RoutingMap.model_validate(json.loads(ROUTING_MAP_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError, ValidationError):
        result.update(route="blocked", reason="Mapa de roteamento indisponível ou inválido.",
                      blockers=["Configuração de rotas ou referências de skills não passaram na validação."])
        return result
    result["selection_notice"] = routing_map.selection_notice
    unsupported = _unsupported_action(_normalized(task))
    if unsupported:
        result.update(route=f"unsupported_{unsupported}", reason=routing_map.blocked_actions[unsupported],
                      blockers=[routing_map.blocked_actions[unsupported]])
        return result
    agents = routing_map.routes[resolved.scope]
    for step_id, agent in enumerate(agents, start=1):
        template = routing_map.steps[agent]
        skills = list(dict.fromkeys(routing_map.common_skills + template.skills))
        acceptance = list(template.acceptance)
        if agent == "qa" and "frontend" in agents:
            skills.append("playwright-verification")
        if resolved.authentication and agent in {"backend", "security"}:
            acceptance.extend([
                "Login limita tentativas; sessão é server-side com expiração e logout que invalida a sessão.",
                "Cookie de sessão usa HttpOnly, Secure e SameSite=Strict; autorização protege recursos.",
            ])
        result["steps"].append({
            "id": step_id, "title": template.title, "description": template.description,
            "agent": agent, "capability": template.capability, "skills": skills,
            "depends_on": list(range(1, step_id)), "acceptance": acceptance, "status": "pending",
        })
    return result


__all__ = ["TaskRequirements", "route_task"]
