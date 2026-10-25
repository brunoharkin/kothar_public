"""
=============================================================
 KOTHAR v4.0 — Testes de Integração
 Engenheiro Kothar | Ugarit Digital
=============================================================
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.api.main import app
from backend.core.config import settings


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP assíncrono para testar a API."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


# =============================================================
# Health
# =============================================================

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["alive"] is True


# =============================================================
# Sessions
# =============================================================

@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    resp = await client.post("/api/sessions/", json={
        "agent_name": "test_agent",
        "llm_model": "test_model",
        "task_summary": "Teste de criação de sessão",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_name"] == "test_agent"
    assert data["status"] == "active"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient):
    resp = await client.get("/api/sessions/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# =============================================================
# Traces
# =============================================================

@pytest.mark.asyncio
async def test_record_trace(client: AsyncClient):
    # Primeiro cria uma sessão
    sess_resp = await client.post("/api/sessions/", json={
        "agent_name": "test_agent",
        "task_summary": "Teste de trace",
    })
    session_id = sess_resp.json()["id"]

    # Grava um trace
    resp = await client.post("/api/traces/", json={
        "session_id": session_id,
        "sequence": 1,
        "event_type": "tool_call",
        "agent_name": "test_agent",
        "tool_name": "write_file",
        "tool_input": {"path": "/tmp/test.py"},
        "tokens_used": 42,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "tool_call"
    assert data["tokens_used"] == 42


@pytest.mark.asyncio
async def test_list_traces_by_session(client: AsyncClient):
    sess_resp = await client.post("/api/sessions/", json={
        "agent_name": "test_agent",
        "task_summary": "Teste filtro trace",
    })
    session_id = sess_resp.json()["id"]

    # Grava trace
    await client.post("/api/traces/", json={
        "session_id": session_id,
        "sequence": 1,
        "event_type": "decision",
        "agent_name": "test_agent",
    })

    # Busca por sessão
    resp = await client.get(f"/api/traces/?session_id={session_id}")
    assert resp.status_code == 200
    traces = resp.json()
    assert len(traces) >= 1
    assert all(t["session_id"] == session_id for t in traces)


# =============================================================
# Skills
# =============================================================

@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient):
    resp = await client.post("/api/skills/", json={
        "name": "test_skill_fastapi_route",
        "description": "Como criar uma rota FastAPI",
        "yaml_content": "metadata:\n  name: test_skill",
        "category": "backend",
        "tags": ["fastapi", "python"],
        "forged_by": "test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test_skill_fastapi_route"
    assert data["category"] == "backend"
