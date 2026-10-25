"""Endpoint → mapa → harness → agentes reais → arquivos em workspace isolado."""

import copy
import hashlib
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from backend.agents.base_agent import BaseAgent
from backend.agents.engineer_agent import EngineerAgent
from backend.api.routers.orchestrate import router
from backend.engenheiro_kothar.handoff import Handoff, handoff
from backend.engenheiro_kothar.orchestrator import engenheiro_kothar
from backend.engenheiro_kothar.routing import route_task
from backend.harness.blueprint_executor import blueprint_executor
from backend.harness.checkpoint import checkpoint_manager
from backend.harness.circuit_breaker import CircuitBreakerRegistry
from backend.harness.step_validator import StepValidator
from backend.memory.cache.redis_client import RedisMemory
from backend.memory.graph.graph_rag import graph_rag
from backend.trace.trace_recorder import trace_recorder


@pytest.fixture
def execution_app(monkeypatch, tmp_path):
    monkeypatch.setenv("KOTHAR_EXECUTION_ROOT", str(tmp_path))
    blueprints, contexts = {}, {}

    async def get_blueprint(self, session_id):
        return copy.deepcopy(blueprints.get(session_id))

    async def set_blueprint(self, session_id, blueprint):
        blueprints[session_id] = copy.deepcopy(blueprint)

    async def update_step(self, session_id, step_id, status, result=None):
        for step in blueprints[session_id]["steps"]:
            if step["id"] == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result

    async def get_context(self, session_id):
        return copy.deepcopy(contexts.get(session_id))

    async def set_context(self, session_id, context):
        contexts[session_id] = copy.deepcopy(context)

    monkeypatch.setattr(RedisMemory, "get_blueprint", get_blueprint)
    monkeypatch.setattr(RedisMemory, "set_blueprint", set_blueprint)
    monkeypatch.setattr(RedisMemory, "update_blueprint_step", update_step)
    monkeypatch.setattr(RedisMemory, "get_context", get_context)
    monkeypatch.setattr(RedisMemory, "set_context", set_context)
    monkeypatch.setattr(trace_recorder, "start_session", AsyncMock(return_value="fixture-session"))
    monkeypatch.setattr(trace_recorder, "record", AsyncMock())
    monkeypatch.setattr(graph_rag, "register_session", AsyncMock())
    monkeypatch.setattr(graph_rag, "register_file", AsyncMock())
    monkeypatch.setattr(engenheiro_kothar, "_check_locks", AsyncMock())
    monkeypatch.setattr(engenheiro_kothar, "_vault_search", AsyncMock())
    monkeypatch.setattr(blueprint_executor, "_load_locks", AsyncMock())
    monkeypatch.setattr(checkpoint_manager, "can_resume_from_checkpoint", AsyncMock(return_value=(False, "fixture")))
    monkeypatch.setattr(checkpoint_manager, "save_checkpoint", AsyncMock())
    monkeypatch.setattr(BaseAgent, "_rag_preload", AsyncMock())
    monkeypatch.setattr(BaseAgent, "_cbm_preload", AsyncMock())
    monkeypatch.setattr(BaseAgent, "check_locks", AsyncMock(return_value=[]))
    monkeypatch.setattr(BaseAgent, "search_skill", AsyncMock(return_value=[]))
    for agent in ("frontend", "backend", "engineer", "security", "qa"):
        CircuitBreakerRegistry.reset(agent)
    app = FastAPI()
    app.include_router(router, prefix="/api/orchestrate")
    return app, blueprints


async def request(app, path, payload=None):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://fixture.test") as client:
        return await client.post(path, json=payload)


def payload(**operation_changes):
    operation = {"agent": "engineer", "action": "create_file", "path": "feature.py", "content": "VALUE = 42\n"}
    operation.update(operation_changes)
    return {"task_description": "Crie uma alteração delimitada", "requirements": {"scope": "general"},
            "execution_plan": {"operations": [operation]}}


@pytest.mark.asyncio
async def test_http_execution_writes_file_and_runs_real_security_and_qa(execution_app, tmp_path):
    app, blueprints = execution_app
    start = await request(app, "/api/orchestrate/start", payload())
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    response = await request(app, f"/api/orchestrate/{session_id}/execute")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed", result
    assert result["completed_steps"] == 3
    assert result["production_ready"] is False
    assert (tmp_path / "feature.py").read_text() == "VALUE = 42\n"
    steps = blueprints[session_id]["steps"]
    assert [step["agent"] for step in steps] == ["engineer", "security", "qa"]
    assert steps[1]["result"]["files_scanned"] == 1
    assert steps[1]["result"]["coverage_complete"] is True
    assert "sintaxe_python" in steps[2]["result"]["checks_passed"]
    assert steps[0]["result"]["skills_loaded"]
    assert "skills_applied" not in steps[0]["result"]


@pytest.mark.asyncio
async def test_http_exact_edit_preserves_other_functions(execution_app, tmp_path):
    app, _ = execution_app
    before = "def first():\n    return 1\n\ndef second():\n    return 2\n"
    target = tmp_path / "feature.py"
    target.write_text(before)
    data = payload(action="replace_text", content="return 3", old_text="return 1",
                   expected_sha256=hashlib.sha256(before.encode()).hexdigest())
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "completed", result
    assert target.read_text() == before.replace("return 1", "return 3")


@pytest.mark.asyncio
async def test_stale_edit_stops_before_security_or_qa(execution_app, tmp_path):
    app, blueprints = execution_app
    target = tmp_path / "feature.py"
    target.write_text("VALUE = 1\n")
    await request(app, "/api/orchestrate/start", payload(action="replace_text", old_text="1", content="2",
                                                       expected_sha256="0" * 64))
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert result["completed_steps"] == 0
    assert "SHA-256 divergente" in result["error"]
    assert target.read_text() == "VALUE = 1\n"
    assert blueprints["fixture-session"]["steps"][1]["status"] == "pending"


@pytest.mark.asyncio
async def test_prompt_only_keeps_planning_but_reports_missing_operations(execution_app, tmp_path):
    app, blueprints = execution_app
    response = await request(app, "/api/orchestrate/start", {"task_description": "Crie página simples de login e testar formulário"})
    assert [step["agent"] for step in response.json()["blueprint"]["steps"]] == ["frontend", "security", "qa"]
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert "operações" in result["error"]
    assert blueprints["fixture-session"]["execution_status"] == "blocked"
    status = await engenheiro_kothar.get_session_status("fixture-session")
    assert status["status"] == "blocked"
    assert status["error"] == result["error"]
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["../escape.py", "/tmp/escape.py", ".env", ".git/config", "AGENTS.md", "a/../../escape.py"])
async def test_invalid_paths_are_rejected_at_ingress(execution_app, path):
    app, blueprints = execution_app
    result = await request(app, "/api/orchestrate/start", payload(path=path))
    assert result.status_code == 422
    assert not blueprints


@pytest.mark.asyncio
async def test_symlink_is_blocked_before_any_write(execution_app, tmp_path):
    app, _ = execution_app
    (tmp_path / "link").symlink_to(tmp_path.parent, target_is_directory=True)
    await request(app, "/api/orchestrate/start", payload(path="link/escape.py"))
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert not (tmp_path.parent / "escape.py").exists()


@pytest.mark.asyncio
async def test_missing_workspace_cannot_default_to_server_repository(execution_app, monkeypatch):
    app, _ = execution_app
    monkeypatch.delenv("KOTHAR_EXECUTION_ROOT")
    await request(app, "/api/orchestrate/start", payload())
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert "Workspace" in result["error"]


@pytest.mark.asyncio
async def test_tampered_capability_does_not_execute(execution_app, tmp_path):
    app, blueprints = execution_app
    await request(app, "/api/orchestrate/start", payload())
    blueprints["fixture-session"]["steps"][0]["capability"] = "arbitrary_shell"
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "blocked"
    assert not (tmp_path / "feature.py").exists()


@pytest.mark.asyncio
async def test_unknown_engineer_action_never_reports_files_written():
    agent = EngineerAgent("engineer", "fixture")
    result = await agent._dispatch_action("invented", ["missing.py"], "", {})
    assert result["status"] == "blocked"
    assert result["files_written"] == []


@pytest.mark.asyncio
async def test_fake_agent_success_without_artifact_cannot_complete(execution_app, tmp_path, monkeypatch):
    app, _ = execution_app
    monkeypatch.setattr(handoff, "delegate", AsyncMock(return_value={"status": "done"}))
    await request(app, "/api/orchestrate/start", payload())
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "failed"
    assert result["completed_steps"] == 0
    assert not (tmp_path / "feature.py").exists()


@pytest.mark.asyncio
async def test_fake_edit_with_original_digest_cannot_complete(execution_app, tmp_path, monkeypatch):
    app, _ = execution_app
    target = tmp_path / "feature.py"
    original = "VALUE = 1\n"
    target.write_text(original)
    digest = hashlib.sha256(original.encode()).hexdigest()
    monkeypatch.setattr(handoff, "delegate", AsyncMock(return_value={
        "status": "done", "files_written": [str(target)], "sha256": digest,
    }))
    await request(app, "/api/orchestrate/start", payload(action="replace_text", old_text="1", content="2", expected_sha256=digest))
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "failed"
    assert result["completed_steps"] == 0
    assert target.read_text() == original


@pytest.mark.asyncio
async def test_frontend_without_real_verifier_cannot_be_approved(execution_app):
    app, blueprints = execution_app
    data = payload(agent="frontend", path="Login.tsx", content="export default function Login( { return <form>")
    data["requirements"]["scope"] = "frontend"
    await request(app, "/api/orchestrate/start", data)
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "partial"
    qa = blueprints["fixture-session"]["steps"][-1]["result"]
    assert qa["status"] == "failed"
    assert "não configurado" in str(qa["checks_failed"])
    assert result["production_ready"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["password", "api_key", "jwt_secret"])
async def test_json_credentials_are_rejected_before_persistence_and_redacted(execution_app, field):
    import json

    app, blueprints = execution_app
    synthetic = "credential_fixture_value_123456"
    response = await request(app, "/api/orchestrate/start", payload(path="config.json", content=json.dumps({field: synthetic})))
    assert response.status_code == 422
    assert synthetic not in response.text
    assert not blueprints


@pytest.mark.asyncio
async def test_invalid_json_fails_real_qa(execution_app):
    app, blueprints = execution_app
    await request(app, "/api/orchestrate/start", payload(path="config.json", content="{invalid}"))
    result = (await request(app, "/api/orchestrate/fixture-session/execute")).json()
    assert result["status"] == "partial"
    assert blueprints["fixture-session"]["steps"][-1]["result"]["status"] == "failed"


def test_explicit_dependencies_override_legacy_title_matching():
    steps = route_task("Crie página simples de login")["steps"]
    validator = StepValidator("fixture", {"steps": steps}, [])
    assert not validator.validate(steps[-1]).can_execute
    validator._completed_steps.update(step["title"] for step in steps[:-1])
    assert validator.validate(steps[-1]).can_execute


@pytest.mark.asyncio
async def test_legacy_pipeline_does_not_silently_skip_canonical_frontend():
    runner = Handoff()
    runner.delegate = AsyncMock(side_effect=[
        {"status": "done", "blueprint_steps": [{"id": 1, "agent": "frontend"}]},
        {"status": "blocked"},
    ])
    result = await runner.run_pipeline("fixture", "frontend", ["page.tsx"])
    assert result["status"] == "failed"
    assert result["failed_at"] == "frontend"
    assert [call.kwargs["agent_name"] for call in runner.delegate.await_args_list] == ["architect", "frontend"]
