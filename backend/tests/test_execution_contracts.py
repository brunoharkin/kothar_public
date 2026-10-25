"""Testes unitários dos contratos de execução multiagente."""

import pytest
from pydantic import ValidationError

from backend.contracts.execution import ExecutionState, Handoff, ReviewResult


def test_handoff_updates_state_without_losing_evidence():
    state = ExecutionState(
        execution_id="exec-1",
        project="kothar",
        mode="build",
        objective="implementar fluxo",
        evidence=["triage concluído"],
    )

    state.apply_handoff(
        Handoff(
            agent="engineer",
            status="completed",
            files=["backend/contracts/execution.py"],
            acceptance=["testes passam"],
            evidence=["pytest"],
            next_agent="code-reviewer",
        )
    )

    assert state.completed_agents == ["engineer"]
    assert state.next_agent == "code-reviewer"
    assert set(state.evidence) == {"triage concluído", "pytest"}


def test_review_result_requires_at_least_three_risks():
    with pytest.raises(ValidationError):
        ReviewResult(
            status="approved",
            attempts=[
                {
                    "attempt": 1,
                    "reviewer": "code-reviewer",
                    "status": "approved",
                }
            ],
            risks=["only-two", "risk"],
            metric="metric",
            tradeoffs=["tradeoff"],
            scope_out=["out"],
            dod=["done"],
            recommendation="vai",
        )


def test_review_result_limits_attempts_to_three():
    attempts = [
        {
            "attempt": index,
            "reviewer": "code-reviewer",
            "status": "changes_requested",
        }
        for index in range(1, 4)
    ]
    result = ReviewResult(
        status="blocked",
        attempts=attempts,
        risks=["r1", "r2", "r3"],
        metric="3 tentativas",
        tradeoffs=["bloquear após limite"],
        scope_out=["nova arquitetura"],
        dod=["bloqueio registrado"],
        recommendation="vai com ressalvas",
    )
    assert len(result.attempts) == 3
