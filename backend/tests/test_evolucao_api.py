"""Rotas reais com principal só da fixture e persistência SQLite explicitamente isolada."""

import time

import httpx
import pytest_asyncio
from fastapi import FastAPI, Request

from backend.api.routers.evolucao import router
from backend.tests.test_evolucao_integracao import allow_budget
from backend.tests.test_evolucao_integracao import (
    integration_environment as integration_environment,
)


@pytest_asyncio.fixture
async def api(integration_environment, monkeypatch):
    environment = integration_environment
    monkeypatch.setattr("backend.api.routers.evolucao.ROOT", environment["root"])
    app = FastAPI()

    @app.middleware("http")
    async def fixture_principal(request: Request, call_next):
        # Apenas esta app de teste confia no header. Não existe no middleware real.
        if request.headers.get("x-fixture-principal"):
            request.state.principal = request.headers["x-fixture-principal"]
        return await call_next(request)

    app.state.evolution_factory = environment["make"]
    app.include_router(router, prefix="/api/evolucao")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://test.invalid",
                                 headers={"x-fixture-principal": "owner-a"}) as client:
        yield client, environment


def fact(**updates):
    return {"content": "Decisão com fonte", "source": "cofre://project-a/adr-1",
            "confidence": 0.9, "observed_at": int(time.time()) - 1, **updates}


async def test_api_requires_server_principal(api):
    client, _ = api
    client.headers.pop("x-fixture-principal")
    assert (await client.get("/api/evolucao/project-a/overview")).status_code == 401
    assert (await client.post("/api/evolucao/project-a/facts", json=fact())).status_code == 401


async def test_api_memory_crud_cas_and_owner_project_isolation(api):
    client, _ = api
    response = await client.post("/api/evolucao/project-a/facts", json=fact())
    assert response.status_code == 201
    saved = response.json()
    context = (await client.get("/api/evolucao/project-a/facts/context", params={"query": "Decisão"})).json()
    assert context["facts"][0]["id"] == saved["id"] and context["authority"] is False
    for project, owner in [("project-a", "owner-b"), ("other", "owner-a")]:
        response = await client.get(f"/api/evolucao/{project}/facts/context", headers={"x-fixture-principal": owner})
        assert response.json()["facts"] == []
        response = await client.delete(f"/api/evolucao/{project}/facts/{saved['id']}", params={"revision": 1}, headers={"x-fixture-principal": owner})
        assert response.status_code == 404
    corrected = await client.put(f"/api/evolucao/project-a/facts/{saved['id']}", params={"revision": 1}, json=fact(content="Decisão corrigida"))
    assert corrected.status_code == 200 and corrected.json()["supersedes"] == saved["id"]
    stale = await client.put(f"/api/evolucao/project-a/facts/{saved['id']}", params={"revision": 1}, json=fact())
    assert stale.status_code == 409
    updated = corrected.json()
    revoked = await client.delete(f"/api/evolucao/project-a/facts/{updated['id']}", params={"revision": updated["revision"]})
    assert revoked.status_code == 200 and revoked.json()["content"] == ""
    assert (await client.get("/api/evolucao/project-a/facts/context")).json()["facts"] == []


async def test_validation_does_not_echo_sensitive_payload_and_body_is_bounded(api):
    client, _ = api
    marker = "synthetic-private-data-do-not-echo"
    invalid = await client.post("/api/evolucao/project-a/facts", json=fact(content=marker, unexpected=marker))
    assert invalid.status_code == 422 and marker not in invalid.text
    malformed = await client.post("/api/evolucao/project-a/facts", content='{"content":"' + marker, headers={"content-type": "application/json"})
    assert malformed.status_code == 422 and marker not in malformed.text
    oversized = await client.post("/api/evolucao/project-a/facts", content=b"x" * 131073, headers={"content-type": "application/json"})
    assert oversized.status_code == 413
    invalid_path = await client.get("/api/evolucao/project%20invalid/overview")
    assert invalid_path.status_code == 422


async def test_api_task_validation_completion_and_idle(api):
    client, _ = api
    bad = await client.post("/api/evolucao/project-a/tasks", json={"title": "Rejeitar shell", "dedupe_key": "bad", "payload": {"operation": "shell", "command": "echo test"}})
    assert bad.status_code == 422
    created = await client.post("/api/evolucao/project-a/tasks", json={"title": "Selecionar skills", "dedupe_key": "skills-api", "payload": {"operation": "skills", "context": "eval", "budget_tokens": 1500}, "retry_safe": True})
    assert created.status_code == 201
    completed = await client.post("/api/evolucao/project-a/tasks/run")
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    assert completed.json()["checkpoint"]["result"]["selected"][0]["name"] == "eval-check"
    assert (await client.post("/api/evolucao/project-a/tasks/run")).json() == {"status": "idle"}


async def test_api_receipt_is_bound_to_run_case_and_server_selection(api):
    client, environment = api
    await allow_budget(environment["make"]())
    selected = await client.post("/api/evolucao/project-a/skills/select", json={"context": "eval"})
    independent_selection = selected.json()["selection_id"]
    evaluated = await client.post("/api/evolucao/project-a/evaluations", json={"cases": [{"id": "arithmetic", "project_id": "project-a", "prompt": "eval 2 + 2", "expected_contains": ["resultado: 4"], "required_tools": ["local_arithmetic"]}]})
    assert evaluated.status_code == 200
    report = evaluated.json()
    request = {"selection_id": report["selections"]["arithmetic"], "run_id": report["run_id"], "case_id": "arithmetic", "skill_name": "eval-check"}
    spoof = await client.post("/api/evolucao/project-a/skills/receipt", json={**request, "selection_id": independent_selection})
    assert spoof.status_code == 422 and spoof.json()["code"] == "invalid_execution_selection"
    receipt = await client.post("/api/evolucao/project-a/skills/receipt", json=request)
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "evidence_recorded"
    assert receipt.json()["execution_id"] == report["results"][0]["execution_id"]
    assert receipt.json()["selection_id"] == request["selection_id"]
    cross_owner = await client.post("/api/evolucao/project-a/skills/receipt", json=request, headers={"x-fixture-principal": "owner-b"})
    assert cross_owner.status_code == 404


async def test_api_feedback_versions_and_no_direct_external_dispatch(api):
    client, _ = api
    submission = {"id": "correction", "project_id": "project-a", "prompt": "eval 2 + 2", "observed_response": "resultado: 5", "correction": "Calcular corretamente"}
    first = await client.post("/api/evolucao/project-a/feedback", json=submission)
    second = await client.post("/api/evolucao/project-a/feedback", json={**submission, "correction": "Verificar resultado antes de responder"})
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["version"] == 1 and second.json()["version"] == 2
    assert not second.json()["automatic_application"]
    action = {"tool": "email_send", "scope": "test", "payload": {}, "dedupe_key": "no-send", "expires_at": int(time.time()) + 300, "review": "Este conector não está configurado"}
    assert (await client.post("/api/evolucao/project-a/actions", json=action)).status_code == 403
