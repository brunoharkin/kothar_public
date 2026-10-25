"""
=============================================================
 KOTHAR v4.0 — Blueprint Executor (Motor de Execução)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Executor do fluxo de passos do blueprint.
 Responsável por:
 - Executar passos em ordem com validação
 - Gerenciar dependências e locks
 - Tratar falhas com retry e circuit breaker
 - Salvar checkpoints a cada passo
 - Reportar progresso em tempo real
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from backend.core.logger import get_logger
from backend.memory.cache.redis_client import RedisMemory
from backend.memory.semantic.hyde_search import HyDESearch
from backend.memory.semantic.chroma_client import chroma_memory
from backend.trace.trace_recorder import trace_recorder
from backend.trace.metrics import record_agent

from .circuit_breaker import CircuitBreakerRegistry, CircuitBreakerOpen
from .step_validator import StepValidator
from .checkpoint import checkpoint_manager, CheckpointData

log = get_logger("harness.executor")


@dataclass
class StepResult:
    """Resultado da execução de um passo."""
    step_id: float
    step_title: str
    agent_name: str
    status: str  # "done", "failed", "skipped", "locked", "timeout"
    output: Any = None
    error: str = None
    duration_ms: int = 0
    retries: int = 0
    checkpoint: CheckpointData = None


@dataclass
class FlowResult:
    """Resultado completo da execução do blueprint."""
    session_id: str
    status: str  # "completed", "failed", "partial", "blocked"
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    step_results: list[StepResult] = field(default_factory=list)
    total_duration_ms: int = 0
    error: str = None
    checkpoint_recovered: bool = False


class BlueprintExecutor:
    """
    Executor de blueprints do Kothar.

    Fluxo de execução:
    1. Carrega blueprint do Redis
    2. Valida estado inicial
    3. Para cada passo:
       a. Verifica dependências
       b. Verifica locks
       c. Verifica circuit breaker
       d. Executa com timeout
       e. Salva checkpoint
       f. Atualiza status no Redis
    4. Retorna resultado consolidado
    """

    # Timeout padrão por passo (5 minutos)
    DEFAULT_STEP_TIMEOUT = 300

    # Retry config
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # segundos

    def __init__(self):
        self.redis = RedisMemory()
        self.hyde = HyDESearch(chroma_memory)
        self._locks: list[dict] = []

    async def execute(
        self,
        session_id: str,
        task_handler: Callable = None,
        task_context: dict = None,
    ) -> FlowResult:
        """
        Executa o blueprint completo.

        Args:
            session_id: ID da sessão
            task_handler: Função que executa cada passo (recebe step, session_id, context)
                        Se None, usa execução simulada
            task_context: Contexto adicional para os handlers
        """
        start_time = time.time()
        blueprint = await self.redis.get_blueprint(session_id)

        if not blueprint:
            log.error("Blueprint não encontrado", session_id=session_id)
            return FlowResult(
                session_id=session_id,
                status="failed",
                total_steps=0,
                completed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error="Blueprint não encontrado no Redis",
            )

        # Recupera locks ativos
        await self._load_locks(session_id)

        # Cria validador
        validator = StepValidator(session_id, blueprint, self._locks)

        # Verifica se pode retomar de checkpoint
        can_resume, resume_reason = await checkpoint_manager.can_resume_from_checkpoint(session_id)
        recovered = False

        if can_resume:
            last_checkpoint = await checkpoint_manager.get_last_checkpoint(session_id)
            if last_checkpoint and last_checkpoint.status == "failed":
                log.info(f"Retomando de checkpoint: {last_checkpoint.step_title}")
                recovered = True
                # Marca passos já feitos como "done" no blueprint
                await self._restore_from_checkpoint(session_id, blueprint, last_checkpoint)
                validator._completed_steps.add(last_checkpoint.step_title)

        # Inicia trace do fluxo
        await trace_recorder.record(
            session_id=session_id,
            event_type="flow_start",
            agent_name="blueprint_executor",
            content=f"Iniciando execução do blueprint com {len(blueprint.get('steps', []))} passos",
            tool_name="blueprint_executor",
            metadata={
                "total_steps": len(blueprint.get("steps", [])),
                "recovered_from_checkpoint": recovered,
                "resume_reason": resume_reason if recovered else None,
            },
        )

        step_results: list[StepResult] = []
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0

        # Executa cada passo
        for step in blueprint.get("steps", []):
            step_result = await self._execute_step(
                step=step,
                session_id=session_id,
                validator=validator,
                task_handler=task_handler,
                task_context=task_context,
            )

            step_results.append(step_result)

            if step_result.status == "done":
                completed_steps += 1
                # Marca como concluído no validador
                validator._completed_steps.add(step.get("title", ""))
            elif step_result.status == "failed":
                failed_steps += 1
                # Verifica se deve parar (circuit breaker)
                if step_result.error and "Circuit Breaker" in step_result.error:
                    log.error("Circuit breaker aberto, parando fluxo", session_id=session_id)
                    break
            else:
                skipped_steps += 1

        total_duration = int((time.time() - start_time) * 1000)

        # Determina status final
        if failed_steps == 0 and skipped_steps == 0:
            status = "completed"
        elif failed_steps > 0:
            status = "failed" if completed_steps == 0 else "partial"
        else:
            status = "partial"

        # Finaliza trace
        await trace_recorder.record(
            session_id=session_id,
            event_type="flow_end",
            agent_name="blueprint_executor",
            content=f"Fluxo finalizado: {status}",
            metadata={
                "status": status,
                "completed": completed_steps,
                "failed": failed_steps,
                "skipped": skipped_steps,
                "total_duration_ms": total_duration,
            },
        )

        return FlowResult(
            session_id=session_id,
            status=status,
            total_steps=len(blueprint.get("steps", [])),
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            step_results=step_results,
            total_duration_ms=total_duration,
            checkpoint_recovered=recovered,
        )

    async def _execute_step(
        self,
        step: dict,
        session_id: str,
        validator: StepValidator,
        task_handler: Callable = None,
        task_context: dict = None,
    ) -> StepResult:
        """Executa um passo individual."""
        step_id = step.get("id")
        step_title = step.get("title", "")
        agent_name = step.get("agent", "unknown")
        timeout = step.get("timeout_seconds", self.DEFAULT_STEP_TIMEOUT)

        log.info(f"Executando passo: {step_title}", session_id=session_id, agent=agent_name)

        # 1. Valida o passo
        validation = validator.validate(step, agent_name)

        if not validation.can_execute:
            reason = validation.reason
            log.warn(f"Passo bloqueado: {reason}", session_id=session_id, step=step_title)

            # Salva checkpoint de bloqueio
            checkpoint = await checkpoint_manager.save_checkpoint(
                session_id=session_id,
                step_id=step_id,
                step_title=step_title,
                status="locked",
                metadata={"reason": reason, "blocked_by": validation.blocked_by},
            )

            await trace_recorder.record(
                session_id=session_id,
                event_type="step_locked",
                agent_name=agent_name,
                content=f"Passo bloqueado: {reason}",
                tool_name="step_validator",
                metadata={"step_id": step_id, "blocked_by": validation.blocked_by},
            )

            return StepResult(
                step_id=step_id,
                step_title=step_title,
                agent_name=agent_name,
                status="locked",
                error=reason,
                checkpoint=checkpoint,
            )

        # 2. Verifica circuit breaker
        try:
            circuit_breaker = await CircuitBreakerRegistry.get(agent_name)
            if not circuit_breaker.is_available():
                raise CircuitBreakerOpen(
                    f"Agent {agent_name} está bloqueado pelo circuit breaker"
                )
        except CircuitBreakerOpen as e:
            log.error(f"Circuit breaker aberto: {agent_name}", session_id=session_id)

            checkpoint = await checkpoint_manager.save_checkpoint(
                session_id=session_id,
                step_id=step_id,
                step_title=step_title,
                status="failed",
                error=str(e),
                metadata={"circuit_breaker": True},
            )

            return StepResult(
                step_id=step_id,
                step_title=step_title,
                agent_name=agent_name,
                status="failed",
                error=str(e),
                checkpoint=checkpoint,
            )

        # 3. Marca como em progresso
        await self._update_step_status(session_id, step_id, "in_progress")

        await trace_recorder.record(
            session_id=session_id,
            event_type="step_start",
            agent_name=agent_name,
            content=f"Iniciando passo: {step_title}",
            tool_name="blueprint_executor",
            metadata={"step_id": step_id, "timeout": timeout},
        )
        await trace_recorder.record(
            session_id=session_id,
            event_type="delegation_started",
            agent_name=agent_name,
            content=f"Delegação iniciada para {agent_name}: {step_title}",
            tool_name="blueprint_executor",
            metadata={"step_id": step_id, "delegation_mode": "sequential"},
        )

        # 4. Salva checkpoint de início
        await checkpoint_manager.save_checkpoint(
            session_id=session_id,
            step_id=step_id,
            step_title=step_title,
            status="started",
        )

        # 5. Executa com retry
        result = await self._execute_with_retry(
            step=step,
            session_id=session_id,
            agent_name=agent_name,
            timeout=timeout,
            task_handler=task_handler,
            task_context=task_context,
        )

        # 6. Salva checkpoint final
        await checkpoint_manager.save_checkpoint(
            session_id=session_id,
            step_id=step_id,
            step_title=step_title,
            status=result.status,
            result=result.output,
            error=result.error,
        )

        # 7. Atualiza status no blueprint
        await self._update_step_status(session_id, step_id, result.status, result.output)

        # 8. Registra métrica
        record_agent(agent_name, result.status, result.duration_ms)

        # 9. Atualiza circuit breaker
        if result.status == "done":
            cb = await CircuitBreakerRegistry.get(agent_name)
            cb._on_success()
        else:
            cb = await CircuitBreakerRegistry.get(agent_name)
            cb._on_failure()

        await trace_recorder.record(
            session_id=session_id,
            event_type="delegation_completed",
            agent_name=agent_name,
            content=f"Delegação concluída para {agent_name}: {result.status}",
            tool_name="blueprint_executor",
            metadata={
                "step_id": step_id,
                "status": result.status,
                "retries": result.retries,
                "delegation_mode": "sequential",
            },
            is_error=result.status != "done",
            error_message=result.error if result.status != "done" else None,
        )

        return result

    async def _execute_with_retry(
        self,
        step: dict,
        session_id: str,
        agent_name: str,
        timeout: int,
        task_handler: Callable = None,
        task_context: dict = None,
    ) -> StepResult:
        """Executa passo com retry em caso de falha."""
        step_id = step.get("id")
        step_title = step.get("title", "")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                start = time.time()

                # Executa com timeout
                result = await asyncio.wait_for(
                    self._run_step_handler(step, session_id, agent_name, task_handler, task_context),
                    timeout=timeout,
                )

                duration = int((time.time() - start) * 1000)

                return StepResult(
                    step_id=step_id,
                    step_title=step_title,
                    agent_name=agent_name,
                    status="done",
                    output=result,
                    duration_ms=duration,
                    retries=attempt - 1,
                )

            except asyncio.TimeoutError:
                log.error(f"Timeout no passo: {step_title}", session_id=session_id, timeout=timeout)

                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * attempt)
                    continue

                return StepResult(
                    step_id=step_id,
                    step_title=step_title,
                    agent_name=agent_name,
                    status="timeout",
                    error=f"Timeout após {self.MAX_RETRIES} tentativas",
                    duration_ms=timeout * 1000,
                    retries=attempt,
                )

            except Exception as e:
                log.error(f"Erro no passo: {step_title}", session_id=session_id, error=str(e))

                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * attempt)
                    continue

                return StepResult(
                    step_id=step_id,
                    step_title=step_title,
                    agent_name=agent_name,
                    status="failed",
                    error=str(e),
                    retries=attempt,
                )

        # Não deveria chegar aqui
        return StepResult(
            step_id=step_id,
            step_title=step_title,
            agent_name=agent_name,
            status="failed",
            error="Loop de retry inesperado",
        )

    async def _run_step_handler(
        self,
        step: dict,
        session_id: str,
        agent_name: str,
        task_handler: Callable = None,
        task_context: dict = None,
    ) -> Any:
        """Executa o handler do passo ou simula."""
        if task_handler:
            return await task_handler(step, session_id, task_context or {})

        # Simulação para testes
        await asyncio.sleep(0.5)

        return {
            "simulated": True,
            "step_id": step.get("id"),
            "agent": agent_name,
            "output": f"Resultado simulado do passo: {step.get('title', '')}",
        }

    async def _load_locks(self, session_id: str) -> None:
        """Carrega locks ativos."""
        # Busca locks do HyDE
        try:
            locks = await self.hyde.search_locks(f"session:{session_id}")
            self._locks = locks if locks else []
        except Exception as e:
            log.warn(f"Erro ao carregar locks: {e}")
            self._locks = []

    async def _update_step_status(
        self,
        session_id: str,
        step_id: float,
        status: str,
        result: Any = None,
    ) -> None:
        """Atualiza status de um passo no Redis."""
        await self.redis.update_blueprint_step(session_id, step_id, status, result)

    async def _restore_from_checkpoint(
        self,
        session_id: str,
        blueprint: dict,
        checkpoint: CheckpointData,
    ) -> None:
        """Restaura estado do blueprint a partir de um checkpoint."""
        # Encontra e marca passos até o checkpoint como "done"
        for step in blueprint.get("steps", []):
            if step.get("id") < checkpoint.step_id:
                step["status"] = "done"
            elif step.get("id") == checkpoint.step_id:
                step["status"] = checkpoint.status

        # Salva blueprint restaurado
        await self.redis.set_blueprint(session_id, blueprint)

        await trace_recorder.record(
            session_id=session_id,
            event_type="checkpoint_recovered",
            agent_name="blueprint_executor",
            content=f"Recuperado de checkpoint: {checkpoint.step_title}",
            metadata={"checkpoint_step_id": checkpoint.step_id},
        )


# Instância singleton
blueprint_executor = BlueprintExecutor()
