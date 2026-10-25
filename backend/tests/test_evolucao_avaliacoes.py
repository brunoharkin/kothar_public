"""Contratos do avaliador + execução local real; teste de modelo é separado e opt-in."""

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.servicos.evolucao.avaliacoes import (
    Artifact,
    BehaviorVerdict,
    EvalCase,
    EvaluationError,
    ExecutionResult,
    JudgeResult,
    OllamaExecutor,
    ToolTrace,
    artifact_digest,
    evaluate_case,
    load_cases,
    run_evaluations,
)
from backend.servicos.evolucao.feedback import FeedbackSubmission, propose_feedback


def case(**updates):
    return EvalCase(id="case-1", prompt="Devolva o canal oficial.", expected_contains=("canal oficial",), **updates)


async def test_local_workflow_executes_tools_and_verifies_real_artifact(tmp_path):
    content = b'{"canal": "atendimento"}'
    artifact = Artifact(path="result.json", sha256=hashlib.sha256(content).hexdigest())

    async def actual_workflow(request):
        # Operação real em workspace de teste; sem modelo e sem imitar uma chamada de LLM.
        target = tmp_path / artifact.path
        target.write_bytes(content)
        response = json.loads(target.read_text())["canal"]
        return ExecutionResult(execution_id=str(uuid4()), executor_kind="local_workflow",
                               response=f"canal oficial: {response}", artifacts=(artifact,),
                               tools=(ToolTrace(id="write-1", name="write_json", status="completed"),))

    result = await run_evaluations((case(required_tools=("write_json",), expected_artifacts=(artifact,)),),
                                   actual_workflow, artifact_root=tmp_path)
    assert result.all_passed
    assert result.passed == 1 and result.failed == result.blocked == 0
    assert result.tokens_input is result.tokens_output is None
    assert result.p50_ms >= 0 and result.contains_test_doubles is False
    assert (tmp_path / artifact.path).read_bytes() == content
    assert result.results[0].tools[0].id == "write-1"


async def test_response_is_evaluated_instead_of_input():
    async def wrong_output(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="desconheço")

    result = await evaluate_case(case(), wrong_output)
    assert result.status == "failed"
    assert result.checks[0].passed is False


async def test_no_executor_fails_closed():
    with pytest.raises(EvaluationError, match="Executor"):
        await run_evaluations((case(),), None)


async def test_semantic_case_requires_judge_without_spending_execution():
    called = False

    async def executor(_):
        nonlocal called
        called = True

    result = await evaluate_case(case(required_behaviors=("responde corretamente",)), executor)
    assert result.status == "blocked" and result.error_code == "semantic_evaluator_required"
    assert called is False


async def test_judge_cannot_approve_with_invented_quote():
    async def executor(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="canal oficial")

    async def judge(request, output):
        return JudgeResult(evaluator="fixture-judge", verdicts=(
            BehaviorVerdict(criterion=request.required_behaviors[0], passed=True, response_quote="texto inventado"),
        ))

    result = await evaluate_case(case(required_behaviors=("responde corretamente",)), executor, judge=judge)
    assert result.status == "failed"
    assert result.checks[-1].criterion == "behavior.0" and not result.checks[-1].passed


async def test_malformed_judge_blocks_and_does_not_leak_content():
    async def executor(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="canal oficial")

    async def judge(*_):
        return {"secret": "untrusted payload"}

    result = await evaluate_case(case(required_behaviors=("critério",)), executor, judge=judge)
    assert result.status == "blocked" and result.error_code == "invalid_semantic_verdict"
    assert "untrusted" not in result.model_dump_json()


async def test_invalid_executor_contract_is_blocked():
    async def executor(_):
        return {"response": "canal oficial"}

    result = await evaluate_case(case(), executor)
    assert result.status == "blocked" and result.error_code == "invalid_executor_contract"
    assert result.execution_id is None


async def test_provider_error_and_timeout_are_safe():
    async def broken(_):
        raise RuntimeError("sensitive provider details")

    async def slow(_):
        await asyncio.sleep(.2)

    errored = await evaluate_case(case(), broken)
    timed = await evaluate_case(case(), slow, timeout_seconds=.001)
    assert errored.error_code == "executor_or_judge_error"
    assert "sensitive" not in errored.model_dump_json()
    assert timed.status == "blocked" and timed.error_code == "execution_timeout"


async def test_forbidden_tool_is_failure_even_when_it_was_blocked():
    async def executor(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="canal oficial",
                               tools=(ToolTrace(id="1", name="send_email", status="blocked"),))

    result = await evaluate_case(case(forbidden_tools=("send_email",)), executor)
    assert result.status == "failed"


async def test_tampered_artifact_and_missing_root_fail(tmp_path):
    artifact = Artifact(path="result.json", sha256=hashlib.sha256(b"original").hexdigest())
    (tmp_path / artifact.path).write_bytes(b"tampered")

    async def executor(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="canal oficial", artifacts=(artifact,))

    for root in (tmp_path, None):
        result = await evaluate_case(case(expected_artifacts=(artifact,)), executor, artifact_root=root)
        assert result.status == "failed"


@pytest.mark.parametrize("path", ["../secret", "/tmp/secret", "folder/../secret", "a//file", ".env", "a\\file",
                                  ".git/config", ".agents/other/SKILL.md", ".agents/skills/debug/.env",
                                  ".agents/skills/.hidden/SKILL.md", ".agents/skills/debug/nested/SKILL.md",
                                  ".agents/skills/debug/SKILL.md/../.env"])
def test_artifact_path_validation(tmp_path, path):
    with pytest.raises(EvaluationError):
        artifact_digest(tmp_path, path)


def test_exact_server_skill_artifact_allowed_with_symlink_protection(tmp_path):
    folder = tmp_path / ".agents/skills/debug"
    folder.mkdir(parents=True)
    skill = folder / "SKILL.md"
    skill.write_bytes(b"instruction")
    assert artifact_digest(tmp_path, ".agents/skills/debug/SKILL.md") == hashlib.sha256(b"instruction").hexdigest()
    skill.unlink()
    skill.symlink_to(tmp_path / ".env")
    (tmp_path / ".env").write_text("sensitive")
    with pytest.raises(EvaluationError):
        artifact_digest(tmp_path, ".agents/skills/debug/SKILL.md")


def test_artifact_symlink_and_hardlink_fail(tmp_path):
    target = tmp_path / "real.json"
    target.write_text("{}")
    (tmp_path / "link.json").symlink_to(target)
    with pytest.raises(EvaluationError):
        artifact_digest(tmp_path, "link.json")
    os.link(target, tmp_path / "hard.json")
    with pytest.raises(EvaluationError):
        artifact_digest(tmp_path, "hard.json")


def test_dataset_missing_never_creates_fixture(tmp_path):
    dataset = tmp_path / "missing.jsonl"
    with pytest.raises(EvaluationError):
        load_cases(dataset)
    assert not dataset.exists()


def test_canonical_dataset_has_explicit_semantic_contract():
    dataset = Path(__file__).resolve().parents[2] / "datasets/harness-whatsapp-avaliacao-v1.jsonl"
    cases = load_cases(dataset)
    assert cases and all(item.required_behaviors for item in cases)


def test_dataset_invalid_or_duplicate_rejected(tmp_path):
    path = tmp_path / "cases.jsonl"
    for data in ("{}\n", '{"id":"old","entrada":"oi"}\n', case().model_dump_json() + "\n" + case().model_dump_json()):
        path.write_text(data)
        with pytest.raises(EvaluationError):
            load_cases(path)


async def test_test_double_is_explicit_and_missing_tokens_are_not_zero():
    async def executor(_):
        return ExecutionResult(execution_id="fixture", executor_kind="test_double", response="canal oficial")

    report = await run_evaluations((case(),), executor)
    assert report.all_passed and report.contains_test_doubles
    assert report.tokens_input is report.tokens_output is None


def test_cli_missing_config_exits_nonzero_and_keeps_dataset(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/kothar-evals.py"
    missing = tmp_path / "absent.jsonl"
    completed = subprocess.run([sys.executable, str(script), "--dataset", str(missing)],
                               capture_output=True, text=True, timeout=10)
    assert completed.returncode != 0
    assert not missing.exists()
    assert "--provider" in completed.stderr


@pytest.mark.parametrize("url", ["https://example.com", "http://169.254.169.254", "http://localhost@remote.test", "http://localhost/a", "http://localhost?x=1"])
def test_ollama_rejects_external_endpoints(url):
    with pytest.raises(EvaluationError):
        OllamaExecutor("model", url)


def test_feedback_produces_immutable_reviewable_regression_with_version_chain():
    submission = FeedbackSubmission(id="feedback-1", project_id="kothar", prompt="Como salvar?",
                                    observed_response="Está pronto.", correction="Exigir evidência de execução antes de afirmar conclusão.")
    proposal = propose_feedback(submission)
    second = propose_feedback(submission, previous_version=proposal.version, previous_sha256=proposal.content_sha256)
    assert proposal.status == "draft" and proposal.automatic_application is False
    assert proposal.regression.case.required_behaviors == (submission.correction,)
    assert proposal.regression.status == "draft_requires_review"
    assert second.version == 2 and second.previous_sha256 == proposal.content_sha256
    assert second.proposal_id != proposal.proposal_id
    with pytest.raises(ValidationError):
        proposal.status = "approved"
    with pytest.raises(ValueError):
        propose_feedback(submission, previous_version=2)


@pytest.mark.skipif(os.environ.get("KOTHAR_RUN_LIVE_EVALS") != "1", reason="Integração real de modelo exige opt-in e modelo configurado.")
async def test_live_ollama_evaluation_explicitly_separated():
    model = os.environ.get("KOTHAR_EVAL_MODEL")
    assert model, "Configure KOTHAR_EVAL_MODEL para rodar a integração real."
    executor = OllamaExecutor(model, os.environ.get("KOTHAR_EVAL_OLLAMA_URL", "http://127.0.0.1:11434"))
    request = EvalCase(id="live-arithmetic", prompt="Responda somente o número que resulta de 2 + 2.", expected_contains=("4",))
    result = await evaluate_case(request, executor)
    assert result.status == "passed", result.model_dump()
    assert result.executor_kind == "live_model" and result.model == model
