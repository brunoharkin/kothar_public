"""Regressões de roteamento e da fronteira entre seleção e execução."""

import json

import pytest
from pydantic import ValidationError

from backend.engenheiro_kothar import routing
from backend.engenheiro_kothar.routing import TaskRequirements, route_task


@pytest.mark.parametrize("task", [
    "Crie uma página simples de login",
    "Crie uma página de login, somente frontend; backend já existe",
    "Crie uma página simples de login e testar o formulário",
    "Crie uma página simples de login com URL de recuperação",
])
def test_simple_login_only_selects_necessary_agents(task):
    result = route_task(task)
    assert result["route"] == "frontend"
    assert result["blockers"] == []
    assert [step["agent"] for step in result["steps"]] == ["frontend", "security", "qa"]
    assert result["requirements"]["authentication"] is True


def test_complete_login_with_backend_selects_four_agents():
    result = route_task("Crie login completo com backend")
    assert result["route"] == "fullstack"
    assert [step["agent"] for step in result["steps"]] == ["frontend", "backend", "security", "qa"]
    security = result["steps"][2]
    assert {"gate-producao", "gate-seguranca-credenciais", "kothar-seguranca"}.issubset(security["skills"])
    assert any("server-side" in criterion for criterion in security["acceptance"])


@pytest.mark.parametrize("scope, expected", [
    ("frontend", ["frontend", "security", "qa"]),
    ("backend", ["backend", "security", "qa"]),
    ("fullstack", ["frontend", "backend", "security", "qa"]),
    ("security", ["security", "qa"]),
    ("general", ["engineer", "security", "qa"]),
])
def test_explicit_scope_precedes_text_inference(scope, expected):
    result = route_task("Crie uma página de login com backend", {"scope": scope})
    assert result["route"] == scope
    assert [step["agent"] for step in result["steps"]] == expected


def test_existing_backend_and_explicit_authentication_are_preserved():
    requirements = TaskRequirements(scope="frontend", backend_exists=True, authentication=False)
    result = route_task("Criar login completo com backend", requirements)
    assert result["requirements"] == requirements.model_dump()
    assert len(result["steps"]) == 3


@pytest.mark.parametrize("requirements", [
    {"scope": "unknown"}, {"scope": "frontend", "deploy": True},
    {"backend_exists": "yes"}, {"authentication": 1}, {"persistence": "false"},
])
def test_requirements_are_strict_and_reject_unknown_fields(requirements):
    with pytest.raises(ValidationError):
        route_task("Criar interface", requirements)


@pytest.mark.parametrize("task", ["", " ", "x" * 20001, None, 2])
def test_invalid_tasks_are_rejected(task):
    with pytest.raises(ValueError):
        route_task(task)


@pytest.mark.parametrize("task, expected", [
    ("Execute DAST contra https://example.com", "unsupported_dast"),
    ("Faça um teste de invasão no alvo autorizado", "unsupported_dast"),
    ("Executar nuclei contra o alvo", "unsupported_dast"),
    ("Faça o deploy desta aplicação", "unsupported_deployment"),
    ("Publicar em produção", "unsupported_deployment"),
])
def test_offensive_and_deployment_requests_have_no_executable_steps(task, expected):
    result = route_task(task, {"scope": "frontend"})
    assert result["route"] == expected
    assert result["blockers"]
    assert result["steps"] == []


@pytest.mark.parametrize("task", [
    "Testar o formulário", "Verificar uma URL", "Criar interface para produção",
    "Testar URL da página simples de login",
])
def test_test_and_url_words_never_select_dast(task):
    result = route_task(task)
    assert result["blockers"] == []
    assert all(step["capability"] in {"file_operations", "credential_scan", "qa_checks"} for step in result["steps"])
    assert not result["route"].startswith("unsupported")


def test_stable_ids_dependencies_and_selection_notice():
    first = route_task("Crie login completo com backend")
    assert first == route_task("Crie login completo com backend")
    assert "não comprova" in first["selection_notice"]
    titles = []
    for index, step in enumerate(first["steps"], start=1):
        assert step["id"] == index
        assert type(step["id"]) is int
        assert step["depends_on"] == list(range(1, index))
        assert step["acceptance"]
        assert step["status"] == "pending"
        assert {"kothar-workflow", "definition-of-done", "kothar-dod"}.issubset(step["skills"])
        titles.append(step["title"])
    assert len(titles) == len(set(titles))
    assert {"frontend-ugarit-ui", "motionsites", "amarracao-logica"}.issubset(first["steps"][0]["skills"])
    assert "playwright-verification" in first["steps"][-1]["skills"]
    json.dumps(first)


@pytest.mark.parametrize("corruption", ["missing", "invalid_json", "unknown_field", "bad_skill", "missing_gate", "wrong_capability", "missing_route", "empty_acceptance"])
def test_invalid_routing_map_fails_closed(monkeypatch, tmp_path, corruption):
    path = tmp_path / "map.json"
    data = json.loads(routing.ROUTING_MAP_PATH.read_text())
    if corruption == "invalid_json":
        path.write_text("{")
    elif corruption != "missing":
        if corruption == "unknown_field":
            data["unknown"] = True
        elif corruption == "bad_skill":
            data["steps"]["frontend"]["skills"].append("../../outside")
        elif corruption == "missing_gate":
            data["steps"]["security"]["skills"].remove("gate-producao")
        elif corruption == "wrong_capability":
            data["steps"]["qa"]["capability"] = "file_operations"
        elif corruption == "missing_route":
            del data["routes"]["frontend"]
        elif corruption == "empty_acceptance":
            data["steps"]["qa"]["acceptance"] = [" "]
        path.write_text(json.dumps(data))
    monkeypatch.setattr(routing, "ROUTING_MAP_PATH", path)
    result = route_task("Crie uma página simples de login")
    assert result["route"] == "blocked"
    assert result["steps"] == []
    assert result["blockers"]


def test_missing_real_skill_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(routing, "SKILLS_ROOT", tmp_path)
    result = route_task("Crie login completo com backend")
    assert result["route"] == "blocked"
    assert result["steps"] == []


def test_backend_and_general_do_not_add_unrequested_frontend_specialists():
    assert route_task("Implemente endpoint de login no backend")["route"] == "backend"
    general = route_task("Ajuste o processamento dos arquivos")
    assert general["route"] == "general"
    assert [step["agent"] for step in general["steps"]] == ["engineer", "security", "qa"]


def test_persistence_requirement_only_adds_needed_backend():
    assert route_task("Criar interface", {"persistence": True})["route"] == "fullstack"
    assert route_task("Criar interface", {"persistence": True, "backend_exists": True})["route"] == "frontend"


def test_clear_fullstack_request_selects_fullstack():
    assert route_task("Crie uma aplicação fullstack")["route"] == "fullstack"
