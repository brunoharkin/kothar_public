"""O executor nunca transforma simulação, falha ou ausência de handler em sucesso."""
from unittest.mock import AsyncMock

import pytest

from backend.harness.blueprint_executor import BlueprintExecutor, StepResult
from backend.harness.checkpoint import checkpoint_manager
from backend.trace.trace_recorder import trace_recorder


@pytest.mark.asyncio
async def test_no_real_handler_blocks_before_any_step(monkeypatch):
    executor = BlueprintExecutor()
    monkeypatch.setattr(executor.redis, "get_blueprint", AsyncMock(return_value={
        "steps": [{"id": 1, "agent": "engineer", "title": "corrigir"}]
    }))
    run_step = AsyncMock()
    monkeypatch.setattr(executor, "_execute_step", run_step)
    result = await executor.execute("fixture")
    assert result.status == "blocked"
    assert result.completed_steps == 0
    assert result.production_ready is False
    run_step.assert_not_awaited()


@pytest.mark.asyncio
async def test_direct_step_without_handler_cannot_simulate_success():
    executor = BlueprintExecutor()
    with pytest.raises(RuntimeError, match="Executor real"):
        await executor._run_step_handler({"id": 1}, "fixture", "engineer")


@pytest.mark.asyncio
@pytest.mark.parametrize("output", [
    None, {}, {"status": "failed"}, {"status": "skipped"},
    {"status": "done", "error": "synthetic"},
    {"status": "done", "simulated": True},
    {"status": "done", "returncode": 1},
])
async def test_failed_handler_output_is_not_marked_done(output):
    executor = BlueprintExecutor()
    result = await executor._execute_with_retry(
        {"id": 1, "title": "fixture"}, "fixture", "engineer", 1,
        task_handler=AsyncMock(return_value=output),
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_security_pass_without_coverage_is_rejected():
    executor = BlueprintExecutor()
    result = await executor._execute_with_retry(
        {"id": 1, "title": "fixture"}, "fixture", "security", 1,
        task_handler=AsyncMock(return_value={"status": "passed"}),
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_real_handler_with_explicit_success_runs_once():
    executor = BlueprintExecutor()
    handler = AsyncMock(return_value={"status": "done"})
    result = await executor._execute_with_retry(
        {"id": 1, "title": "fixture"}, "fixture", "engineer", 1, task_handler=handler,
    )
    assert result.status == "done"
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_step_prevents_later_deploy(monkeypatch):
    executor = BlueprintExecutor()
    steps = [{"id": 1, "agent": "engineer", "title": "implementar"},
             {"id": 2, "agent": "devops", "title": "publicar"}]
    monkeypatch.setattr(executor.redis, "get_blueprint", AsyncMock(return_value={"steps": steps}))
    monkeypatch.setattr(executor, "_load_locks", AsyncMock())
    monkeypatch.setattr(checkpoint_manager, "can_resume_from_checkpoint",
                        AsyncMock(return_value=(False, "fixture")))
    monkeypatch.setattr(trace_recorder, "record", AsyncMock())
    run_step = AsyncMock(return_value=StepResult(1, "implementar", "engineer", "failed"))
    monkeypatch.setattr(executor, "_execute_step", run_step)
    result = await executor.execute("fixture", task_handler=AsyncMock())
    assert result.status == "failed"
    assert result.skipped_steps == 1
    run_step.assert_awaited_once()

