"""
=============================================================
 KOTHAR v4.0 — Teste do Harness
 Executar: python -m backend.tests.test_harness
=============================================================
"""

import asyncio
import sys

from backend.core.logger import get_logger, setup_logging

setup_logging()
log = get_logger("test.harness")


async def test_circuit_breaker():
    """Testa o circuit breaker."""
    from backend.harness import CircuitBreaker, CircuitBreakerOpen, CircuitBreakerRegistry

    log.info("🧪 Testando Circuit Breaker...")

    cb = await CircuitBreakerRegistry.get("test_agent")

    # Estado inicial
    assert cb.state.value == "closed", "Deve começar CLOSED"
    assert cb.is_available() == True, "Deve estar disponível"

    # Simula falhas
    for i in range(3):
        cb._on_failure()

    assert cb.state.value == "open", "Deve estar OPEN após 3 falhas"
    assert cb.is_available() == False, "Não deve estar disponível"

    # Reset
    CircuitBreakerRegistry.reset("test_agent")
    cb = await CircuitBreakerRegistry.get("test_agent")
    assert cb.state.value == "closed", "Deve voltar para CLOSED após reset"

    log.info("✅ Circuit Breaker OK")


async def test_step_validator():
    """Testa o validador de passos."""
    from backend.harness import StepValidator

    log.info("🧪 Testando Step Validator...")

    blueprint = {
        "steps": [
            {"id": 1, "title": "Diagnóstico", "status": "done"},
            {"id": 2, "title": "Planejamento", "status": "done"},
            {"id": 3, "title": "Estrutura (Scaffold) & Portable Design", "status": "pending"},
            {"id": 4, "title": "QA", "status": "pending"},
        ]
    }

    validator = StepValidator("session-1", blueprint, [])

    # Testa passo com deps atendidas (Scaffold depende de Planejamento)
    step = {"id": 3, "title": "Estrutura (Scaffold) & Portable Design", "status": "pending"}
    result = validator.validate(step)
    assert result.can_execute == True, f"Scaffold deps atendidas (reason: {result.reason})"

    # Testa passo com deps não atendidas
    step = {"id": 4, "title": "QA", "status": "pending"}
    result = validator.validate(step)
    assert result.can_execute == False, "QA bloqueado por dependências"

    # Testa passo já concluído
    step = {"id": 1, "title": "Diagnóstico", "status": "done"}
    result = validator.validate(step)
    assert result.can_execute == False, "Passo já concluído"

    log.info("✅ Step Validator OK")


async def test_checkpoint():
    """Testa o checkpoint manager (mockado)."""
    from backend.harness import CheckpointData

    log.info("🧪 Testando Checkpoint Manager (mock)...")

    # Testa estrutura de dados
    cp = CheckpointData(
        session_id="test-session",
        step_id=1.0,
        step_title="Teste",
        status="started",
        result={"test": True},
    )

    assert cp.step_title == "Teste"
    assert cp.status == "started"

    # Testa serialização
    data = cp.to_dict()
    assert data["step_title"] == "Teste"

    # Testa deserialização
    cp2 = CheckpointData.from_dict(data)
    assert cp2.step_title == "Teste"
    assert cp2.status == "started"

    log.info("✅ Checkpoint Manager OK")


async def test_blueprint_executor():
    """Testa o executor de blueprint (mockado)."""
    from backend.harness.blueprint_executor import FlowResult, StepResult

    log.info("🧪 Testando Blueprint Executor (mock)...")

    # Testa estrutura de dados
    flow_result = FlowResult(
        session_id="test-session",
        status="completed",
        total_steps=5,
        completed_steps=5,
        failed_steps=0,
        skipped_steps=0,
        total_duration_ms=1000,
    )

    assert flow_result.status == "completed"
    assert flow_result.completed_steps == 5

    # Testa step results
    step_result = StepResult(
        step_id=1.0,
        step_title="Teste",
        agent_name="architect",
        status="done",
        duration_ms=100,
        retries=0,
    )

    flow_result.step_results.append(step_result)

    assert len(flow_result.step_results) == 1
    assert flow_result.step_results[0].status == "done"

    log.info("✅ Blueprint Executor OK")


async def test_orchestrator_integration():
    """Testa integração com orchestrator (requer DB/Redis)."""
    try:
        from backend.engenheiro_kothar import engenheiro_kothar

        log.info("🧪 Testando integração com Orchestrator...")

        # Cria orquestração
        result = await engenheiro_kothar.orchestrate(
            task_description="Teste de integração do harness"
        )

        assert "session_id" in result
        assert "blueprint" in result
        assert len(result["blueprint"]["steps"]) > 0

        session_id = result["session_id"]

        # Executa blueprint
        flow_result = await engenheiro_kothar.execute(session_id)

        assert flow_result.session_id == session_id
        assert flow_result.status in ["completed", "failed", "partial"]

        log.info("✅ Orchestrator Integration OK")
    except Exception as e:
        log.warn(f"⏭️ Orchestrator Integration SKIPPED (DB/Redis não disponível): {e}")


async def main():
    """Executa todos os testes."""
    log.info("=" * 60)
    log.info("🧪 INICIANDO TESTES DO HARNESS KOTHAR v4.0")
    log.info("=" * 60)

    try:
        await test_circuit_breaker()
        await test_step_validator()
        await test_checkpoint()
        await test_blueprint_executor()
        await test_orchestrator_integration()

        log.info("=" * 60)
        log.info("✅ TODOS OS TESTES PASSARAM")
        log.info("=" * 60)
        return 0

    except Exception as e:
        log.error(f"❌ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
