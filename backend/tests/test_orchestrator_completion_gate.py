"""Finalização não pode ignorar falta de blueprint, segurança ou QA."""
from unittest.mock import AsyncMock

import pytest

from backend.engenheiro_kothar.orchestrator import EngenheiroKothar
from backend.trace.trace_recorder import trace_recorder
from backend.trace.session_compiler import session_compiler


@pytest.mark.asyncio
@pytest.mark.parametrize("blueprint", [
    None, {}, {"steps": []}, {"steps": [None]},
    {"steps": [{"agent": "qa", "status": "done", "result": {"status": "passed"}}]},
    {"steps": [{"agent": "security", "status": "done", "result": {"status": "failed"}},
               {"agent": "qa", "status": "done", "result": {"status": "passed"}}]},
    {"steps": [{"agent": "security", "status": "done", "result": {"status": "passed"}},
               {"agent": "qa", "status": "done", "result": {"status": "passed"}}]},
])
async def test_incomplete_evidence_cannot_finalize_or_delete_session(monkeypatch, blueprint):
    orchestrator = EngenheiroKothar()
    monkeypatch.setattr(orchestrator.redis, "get_blueprint", AsyncMock(return_value=blueprint))
    delete = AsyncMock()
    compile_session = AsyncMock()
    end = AsyncMock()
    monkeypatch.setattr(orchestrator.redis, "delete_session", delete)
    monkeypatch.setattr(session_compiler, "compile", compile_session)
    monkeypatch.setattr(trace_recorder, "end_session", end)
    monkeypatch.setattr(trace_recorder, "record_decision", AsyncMock())
    with pytest.raises(ValueError, match="bloqueada"):
        await orchestrator.complete_session("fixture")
    compile_session.assert_not_awaited()
    end.assert_not_awaited()
    delete.assert_not_awaited()

