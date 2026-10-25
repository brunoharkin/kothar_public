"""Regressões do portão de conclusão do pipeline, sem serviços externos."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from backend.engenheiro_kothar.handoff import Handoff


def test_security_failure_stops_pipeline_before_qa():
    handoff = Handoff()
    handoff.delegate = AsyncMock(side_effect=[
        {"status": "done", "blueprint_steps": [{"id": 1, "agent": "engineer"}]},
        {"status": "done"},
        {"status": "failed", "issues": [{"pattern": "synthetic"}]},
        {"status": "passed"},
    ])

    result = asyncio.run(handoff.run_pipeline("test-session", "corrigir", ["app.py"]))

    assert result["status"] == "failed"
    assert result["failed_at"] == "security"
    assert [call.kwargs["agent_name"] for call in handoff.delegate.await_args_list] == [
        "architect", "engineer", "security",
    ]


@pytest.mark.parametrize("security", [None, {}, {"status": "error"}, {"status": "skipped"},
                                     {"status": "passed"}, {"status": "unknown"}])
def test_unknown_or_uncovered_security_never_reaches_qa(security):
    handoff = Handoff()
    handoff.delegate = AsyncMock(side_effect=[
        {"status": "done", "blueprint_steps": [{"id": 1, "agent": "engineer"}]},
        {"status": "done"}, security,
    ])
    result = asyncio.run(handoff.run_pipeline("fixture", "fixture", ["app.py"]))
    assert result["status"] == "failed"
    assert result["failed_at"] == "security"
    assert handoff.delegate.await_count == 3


@pytest.mark.parametrize("engineer", [None, {"status": "failed"},
                                     {"status": "done", "returncode": 2},
                                     {"status": "done", "error": "synthetic"}])
def test_engineer_error_is_not_hidden(engineer):
    handoff = Handoff()
    handoff.delegate = AsyncMock(side_effect=[
        {"status": "done", "blueprint_steps": [{"id": 1, "agent": "engineer"}]}, engineer,
    ])
    result = asyncio.run(handoff.run_pipeline("fixture", "fixture", ["app.py"]))
    assert result["status"] == "failed"
    assert result["failed_at"] == "engineer"
    assert handoff.delegate.await_count == 2


@pytest.mark.parametrize("qa", [{"status": "passed"}, {"status": "failed"}, None])
def test_qa_failure_cannot_be_delivered_as_completed_with_warnings(qa):
    handoff = Handoff()
    handoff.delegate = AsyncMock(side_effect=[
        {"status": "done", "blueprint_steps": [{"id": 1, "agent": "engineer"}]},
        {"status": "done"},
        {"status": "passed", "coverage_complete": True, "files_requested": 1,
         "files_scanned": 1, "errors": [], "ignored_files": [], "issues": [],
         "scope": "credential_patterns_only"}, qa,
    ])
    result = asyncio.run(handoff.run_pipeline("fixture", "fixture", ["app.py"]))
    if qa and qa["status"] == "passed":
        assert result["status"] == "completed"
        assert result["production_ready"] is False
    else:
        assert result["status"] == "failed"
        assert result["failed_at"] == "qa"
