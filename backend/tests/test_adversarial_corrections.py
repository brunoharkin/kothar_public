"""Regressões das correções: precondições globais e aceite funcional por necessidade."""

import hashlib

import pytest

from backend.engenheiro_kothar.routing import route_task
from backend.tests.test_routed_execution import payload, request

pytest_plugins = ("backend.tests.test_routed_execution",)


@pytest.mark.parametrize("prompt", [
    "Crie um login completo",
    "Faça uma página completa de autenticação",
    "Implemente login completo sem um backend existente",
])
def test_complete_authentication_requires_backend(prompt):
    result = route_task(prompt)
    assert [step["agent"] for step in result["steps"]] == ["frontend", "backend", "security", "qa"]


@pytest.mark.parametrize("prompt", [
    "Crie uma página de login. Não implemente autenticação real. Apenas o formulário visual.",
    "Crie login sem autenticação real, somente a interface.",
])
def test_authentication_denial_is_respected(prompt):
    result = route_task(prompt)
    assert result["requirements"]["authentication"] is False
    assert [step["agent"] for step in result["steps"]] == ["frontend", "security", "qa"]


def test_explicit_backend_absence_overrides_textual_existing_backend():
    result = route_task("Crie login completo. Backend já existe.", {"backend_exists": False})
    assert result["requirements"]["backend_exists"] is False
    assert "backend" in [step["agent"] for step in result["steps"]]


@pytest.mark.asyncio
@pytest.mark.parametrize("with_read", [False, True])
async def test_valid_create_then_edit_plan_still_runs(execution_app, tmp_path, with_read):
    app, blueprints = execution_app
    data = payload(content="VALUE = 1\n")
    if with_read:
        data["execution_plan"]["operations"].append({
            "agent": "engineer", "action": "read_file", "path": "feature.py",
        })
    data["execution_plan"]["operations"].append({
        "agent": "engineer", "action": "replace_text", "path": "feature.py",
        "old_text": "1", "content": "2", "expected_sha256": hashlib.sha256(b"VALUE = 1\n").hexdigest(),
    })
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "completed", result
    assert (tmp_path / "feature.py").read_text() == "VALUE = 2\n"
    assert len(blueprints["fixture-session"]["steps"][0]["result"]["operation_results"]) == (3 if with_read else 2)


@pytest.mark.asyncio
async def test_later_backend_error_blocks_frontend_write(execution_app, tmp_path):
    app, _ = execution_app
    (tmp_path / "existing.py").write_text("VALUE = 1\n")
    data = {
        "task_description": "Implemente frontend e backend", "requirements": {"scope": "fullstack"},
        "execution_plan": {"operations": [
            {"agent": "frontend", "action": "create_file", "path": "Login.tsx", "content": "export const Login = () => <form />;"},
            {"agent": "backend", "action": "replace_text", "path": "existing.py", "old_text": "1", "content": "2", "expected_sha256": "0" * 64},
        ]},
    }
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert not (tmp_path / "Login.tsx").exists()
    assert (tmp_path / "existing.py").read_text() == "VALUE = 1\n"


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "content"), [("login.py", "VALUE = 42\n"), ("login.json", '{"label": "Login"}')])
async def test_frontend_extension_cannot_bypass_functional_qa(execution_app, path, content):
    app, blueprints = execution_app
    data = payload(agent="frontend", path=path, content=content)
    data["requirements"]["scope"] = "frontend"
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "partial"
    qa = blueprints["fixture-session"]["steps"][-1]["result"]
    assert qa["status"] == "failed"
    assert "funcional de frontend não configurado" in str(qa["checks_failed"])
    assert result["production_ready"] is False


@pytest.mark.asyncio
async def test_authentication_cannot_pass_qa_with_only_python_syntax(execution_app):
    app, blueprints = execution_app
    data = payload(agent="backend", path="login.py", content="def login(email, password):\n    return True\n")
    data.update(task_description="Implemente autenticação real no backend", requirements={"scope": "backend"})
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "partial"
    qa = blueprints["fixture-session"]["steps"][-1]["result"]
    assert "funcional de autenticação não configurado" in str(qa["checks_failed"])
    assert result["production_ready"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("paths", [("parent.py", "parent.py/child.py"), ("parent.py/child.py", "parent.py")])
async def test_virtual_file_directory_conflict_blocks_entire_plan(execution_app, tmp_path, paths):
    app, _ = execution_app
    data = payload()
    data["execution_plan"]["operations"] = [
        {"agent": "engineer", "action": "create_file", "path": path, "content": "VALUE = 1\n"}
        for path in paths
    ]
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert "diretório" in result["error"]
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize("prefix", ["", "import typing\n\n", "from __future__ import annotations\n\n"])
@pytest.mark.parametrize("body", [
    "raise NotImplementedError", "raise NotImplementedError('TODO')", "return NotImplemented",
    "return None", "...", "if True:\n        pass",
    "try:\n        pass\n    except Exception:\n        pass",
    "match 1:\n        case 1:\n            pass",
    "import json\n    pass",
])
async def test_python_placeholder_function_cannot_implement_feature(execution_app, tmp_path, body, prefix):
    app, _ = execution_app
    await request(app, "/api/orchestrate/start", payload(content=f"{prefix}def feature():\n    {body}\n"))
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert "Artefato não verificável" in result["error"]
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["password", "senha", "token", "api_key", "chave", "secret"])
async def test_numeric_source_credentials_cannot_persist(execution_app, tmp_path, name):
    app, blueprints = execution_app
    response = await request(app, "/api/orchestrate/start", payload(content=f"{name} = 7\n"))
    assert response.status_code == 422
    assert not blueprints
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "expression"), [
    ("feature.py", 'f"{os.getenv(\'APP_PASSWORD\', \'x\')}"'),
    ("feature.py", 'f"{\'x\' if True else configured_password}"'),
    ("feature.js", '`${"x" || ""}`'),
    ("feature.js", '`${process.env.ACCESS_TOKEN || "x"}`'),
    ("feature.js", '`${process.env.ACCESS_TOKEN && "x"}`'),
    ("feature.js", '`${process.env.ACCESS_TOKEN ?? "x"}`'),
    ("feature.js", '`${condition ? process.env.APP_VALUE : "x"}`'),
])
async def test_literal_interpolation_fallback_cannot_persist(execution_app, tmp_path, path, expression):
    app, blueprints = execution_app
    response = await request(app, "/api/orchestrate/start", payload(
        path=path, content=" = ".join(("password", expression)) + "\n"))
    assert response.status_code == 422
    assert not blueprints
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "expression", "status"), [
    ("feature.py", 'f"{os.getenv(\'APP_PASSWORD\')}"', "completed"),
    ("feature.py", 'f"{os.environ[\'APP_PASSWORD\']}"', "completed"),
    ("feature.js", '`${process.env.ACCESS_TOKEN}`', "partial"),
])
async def test_pure_dynamic_credential_reference_is_preserved(execution_app, tmp_path, path, expression, status):
    app, _ = execution_app
    content = " = ".join(("password", expression)) + "\n"
    start = await request(app, "/api/orchestrate/start", payload(path=path, content=content))
    assert start.status_code == 200
    execution = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert execution["status"] == status
    assert execution["production_ready"] is False
    assert (tmp_path / path).read_text() == content
