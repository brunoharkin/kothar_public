"""
=============================================================
 KOTHAR v4.0 — Trace Recorder (Gravação de Eventos)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Grava TODOS os eventos de agentes no PostgreSQL (Data Lake).
 Ponto de entrada único para qualquer evento que precisa ser auditado.

 EVENTOS REGISTRADOS:
 - flow_start / flow_end: Início/fim do blueprint
 - step_start / step_done / step_failed / step_locked: Ciclo de passo
 - agent_start / agent_complete / agent_retry: Ciclo de agente
 - decision: Decisões estratégicas
 - thinking: Pensamento completo do modelo
 - lock_check: Verificação de locks
 - vault_search: Busca no cofre
 - blueprint_created: Blueprint gerado
 - checkpoint: Checkpoint de recuperação
 - circuit_breaker: Abertura/fechamento de circuit breaker
"""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.models import Session, Trace
from backend.trace.metrics import record_trace, record_session, record_agent

log = get_logger("trace.recorder")


class TraceRecorder:
    """
    Gravador central de traces do Engenheiro Kothar.
    
    Uso padrão:
        recorder = TraceRecorder()
        session_id = await recorder.start_session("engineer", "claude-3-5-sonnet", "Criar login")
        
        async with recorder.trace_tool(session_id, "engineer", "write_file") as span:
            # executa a ferramenta
            pass
        
        await recorder.end_session(session_id)
    """

    def __init__(self):
        self._sequence_counters: dict[str, int] = {}

    def _next_sequence(self, session_id: str) -> int:
        self._sequence_counters[session_id] = self._sequence_counters.get(session_id, 0) + 1
        return self._sequence_counters[session_id]

    # ----------------------------------------------------------
    # Sessões
    # ----------------------------------------------------------

    async def start_session(
        self,
        agent_name: str,
        llm_model: str = "",
        task_summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Inicia uma nova sessão e retorna o session_id."""
        session_id = str(uuid.uuid4())
        async with get_db_session() as db:
            session = Session(
                id=uuid.UUID(session_id),
                agent_name=agent_name,
                llm_model=llm_model,
                task_summary=task_summary,
                status="active",
                metadata_=metadata or {},
            )
            db.add(session)

        self._sequence_counters[session_id] = 0
        # Métrica Prometheus
        record_session("started")
        log.info(
            "🟢 Sessão iniciada",
            session_id=session_id,
            agent=agent_name,
            task=task_summary[:60] if task_summary else "",
        )
        return session_id

    async def end_session(
        self,
        session_id: str,
        status: str = "completed",
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Finaliza a sessão com métricas de consumo."""
        async with get_db_session() as db:
            from sqlalchemy import select
            result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
            session = result.scalar_one_or_none()
            if session:
                session.ended_at = datetime.now(timezone.utc)
                session.status = status
                session.tokens_input = tokens_input
                session.tokens_output = tokens_output
                session.total_cost_usd = cost_usd

        self._sequence_counters.pop(session_id, None)
        # Métrica Prometheus
        record_session(status)
        log.info(
            "🔴 Sessão encerrada",
            session_id=session_id,
            status=status,
            tokens_total=tokens_input + tokens_output,
            cost_usd=cost_usd,
        )

    # ----------------------------------------------------------
    # Eventos de Trace
    # ----------------------------------------------------------

    async def record(
        self,
        session_id: str,
        event_type: str,
        agent_name: str,
        content: str = "",
        tool_name: str | None = None,
        tool_input: dict | None = None,
        tool_output: dict | None = None,
        duration_ms: int | None = None,
        tokens_used: int = 0,
        is_error: bool = False,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Grava um evento de trace. Retorna o trace_id."""
        trace_id = str(uuid.uuid4())
        seq = self._next_sequence(session_id)

        async with get_db_session() as db:
            trace = Trace(
                id=uuid.UUID(trace_id),
                session_id=uuid.UUID(session_id),
                sequence=seq,
                event_type=event_type,
                agent_name=agent_name,
                content=content[:10000] if content else None,  # limita conteúdo
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                is_error=is_error,
                error_message=error_message,
                metadata_=metadata or {},
            )
            db.add(trace)

        # Métrica Prometheus
        record_trace(event_type, agent_name, duration_ms)

        if is_error:
            log.error(
                "⛔ Erro traced",
                session_id=session_id,
                seq=seq,
                agent=agent_name,
                event_type=event_type,
                error=error_message,
            )
        else:
            log.debug(
                "📍 Evento traced",
                session_id=session_id,
                seq=seq,
                agent=agent_name,
                event_type=event_type,
                tool=tool_name,
            )
        return trace_id

    @asynccontextmanager
    async def trace_tool(
        self,
        session_id: str,
        agent_name: str,
        tool_name: str,
        tool_input: dict | None = None,
        tokens_used: int = 0,
    ):
        """
        Context manager que mede tempo de execução e grava trace automaticamente.
        
        Uso:
            async with recorder.trace_tool(session_id, "engineer", "write_file", {"path": "..."}) as span:
                result = await write_file(...)
                span["output"] = {"bytes_written": 1024}
        """
        span: dict[str, Any] = {"output": None, "error": None}
        start = time.monotonic()

        try:
            yield span
            duration = int((time.monotonic() - start) * 1000)
            await self.record(
                session_id=session_id,
                event_type="tool_call",
                agent_name=agent_name,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=span.get("output"),
                duration_ms=duration,
                tokens_used=tokens_used,
            )
        except Exception as e:
            duration = int((time.monotonic() - start) * 1000)
            await self.record(
                session_id=session_id,
                event_type="tool_call",
                agent_name=agent_name,
                tool_name=tool_name,
                tool_input=tool_input,
                duration_ms=duration,
                is_error=True,
                error_message=str(e)[:500],
            )
            raise

    async def record_llm_call(
        self,
        session_id: str,
        agent_name: str,
        prompt_summary: str,
        response_summary: str,
        tokens_input: int,
        tokens_output: int,
        model: str = "",
        duration_ms: int | None = None,
    ) -> str:
        """Atalho para gravar chamadas LLM."""
        return await self.record(
            session_id=session_id,
            event_type="llm_response",
            agent_name=agent_name,
            content=f"PROMPT: {prompt_summary[:500]}\n\nRESPOSTA: {response_summary[:500]}",
            tokens_used=tokens_input + tokens_output,
            duration_ms=duration_ms,
            metadata={"model": model, "tokens_in": tokens_input, "tokens_out": tokens_output},
        )

    async def record_decision(
        self,
        session_id: str,
        agent_name: str,
        decision: str,
        reasoning: str = "",
    ) -> str:
        """Grava uma decisão estratégica do agente."""
        return await self.record(
            session_id=session_id,
            event_type="decision",
            agent_name=agent_name,
            content=f"DECISÃO: {decision}\n\nRAZÃO: {reasoning}",
        )

    async def record_thinking(
        self,
        session_id: str,
        agent_name: str,
        thinking_content: str,
        tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Grava conteúdo completo de thinking do agente (sem truncar).

        O thinking pode ser muito longo, então NÃO é truncado como outros eventos.
        Returns trace_id of the thinking event.
        """
        trace_id = str(uuid.uuid4())
        seq = self._next_sequence(session_id)

        extra_meta = metadata or {}
        extra_meta["thinking_length_chars"] = len(thinking_content)
        extra_meta["thinking_length_tokens_est"] = max(1, int(len(thinking_content) / 3.5))

        async with get_db_session() as db:
            trace = Trace(
                id=uuid.UUID(trace_id),
                session_id=uuid.UUID(session_id),
                sequence=seq,
                event_type="thinking",
                agent_name=agent_name,
                content=thinking_content,  # SEM TRUNCAMENTO - thinking pode ser longo
                tool_name="Claude:thinking",
                tool_input={"thinking": thinking_content},
                tokens_used=tokens,
                metadata_=extra_meta,
            )
            db.add(trace)

        record_trace("thinking", agent_name, None)
        log.debug(
            "🧠 Thinking gravado",
            session_id=session_id,
            seq=seq,
            agent=agent_name,
            chars=len(thinking_content),
            tokens_est=extra_meta["thinking_length_tokens_est"],
        )
        return trace_id

    # ----------------------------------------------------------
    # Eventos de Fluxo (BlueprintExecutor)
    # ----------------------------------------------------------

    async def record_flow_start(
        self,
        session_id: str,
        total_steps: int,
        recovered_from: str = None,
    ) -> str:
        """Grava início da execução do blueprint."""
        return await self.record(
            session_id=session_id,
            event_type="flow_start",
            agent_name="blueprint_executor",
            content=f"Iniciando execução de blueprint com {total_steps} passos",
            metadata={
                "total_steps": total_steps,
                "recovered_from_checkpoint": recovered_from is not None,
                "recovered_from": recovered_from,
            },
        )

    async def record_flow_end(
        self,
        session_id: str,
        status: str,
        completed_steps: int,
        failed_steps: int,
        skipped_steps: int,
        total_duration_ms: int,
    ) -> str:
        """Grava fim da execução do blueprint."""
        return await self.record(
            session_id=session_id,
            event_type="flow_end",
            agent_name="blueprint_executor",
            content=f"Fluxo finalizado: {status} ({completed_steps}/{completed_steps + failed_steps + skipped_steps} concluídos)",
            metadata={
                "status": status,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "skipped_steps": skipped_steps,
                "total_duration_ms": total_duration_ms,
            },
        )

    async def record_step_start(
        self,
        session_id: str,
        agent_name: str,
        step_id: float,
        step_title: str,
        timeout_seconds: int,
    ) -> str:
        """Grava início de um passo."""
        return await self.record(
            session_id=session_id,
            event_type="step_start",
            agent_name=agent_name,
            content=f"Iniciando passo: {step_title}",
            metadata={
                "step_id": step_id,
                "step_title": step_title,
                "timeout_seconds": timeout_seconds,
            },
        )

    async def record_step_done(
        self,
        session_id: str,
        agent_name: str,
        step_id: float,
        step_title: str,
        duration_ms: int,
        retries: int,
    ) -> str:
        """Grava conclusão de um passo."""
        return await self.record(
            session_id=session_id,
            event_type="step_done",
            agent_name=agent_name,
            content=f"Passo concluído: {step_title}",
            duration_ms=duration_ms,
            metadata={
                "step_id": step_id,
                "step_title": step_title,
                "retries": retries,
            },
        )

    async def record_step_failed(
        self,
        session_id: str,
        agent_name: str,
        step_id: float,
        step_title: str,
        error: str,
        retries: int,
    ) -> str:
        """Grava falha de um passo."""
        return await self.record(
            session_id=session_id,
            event_type="step_failed",
            agent_name=agent_name,
            content=f"Passo falhou: {step_title}",
            is_error=True,
            error_message=error[:500],
            metadata={
                "step_id": step_id,
                "step_title": step_title,
                "retries": retries,
            },
        )

    async def record_step_locked(
        self,
        session_id: str,
        step_id: float,
        step_title: str,
        reason: str,
        blocked_by: list = None,
    ) -> str:
        """Grava passo bloqueado (dependência ou lock)."""
        return await self.record(
            session_id=session_id,
            event_type="step_locked",
            agent_name="blueprint_executor",
            content=f"Passo bloqueado: {step_title} - {reason}",
            metadata={
                "step_id": step_id,
                "step_title": step_title,
                "reason": reason,
                "blocked_by": blocked_by or [],
            },
        )

    async def record_circuit_breaker(
        self,
        session_id: str,
        agent_name: str,
        action: str,  # "opened", "closed", "half_open"
        failures: int,
        threshold: int,
    ) -> str:
        """Grava evento de circuit breaker."""
        return await self.record(
            session_id=session_id,
            event_type="circuit_breaker",
            agent_name=agent_name,
            content=f"Circuit Breaker {action}: {agent_name} (falhas: {failures}/{threshold})",
            metadata={
                "action": action,
                "failures": failures,
                "threshold": threshold,
            },
        )

    async def record_checkpoint(
        self,
        session_id: str,
        step_id: float,
        step_title: str,
        status: str,
        recovered: bool = False,
    ) -> str:
        """Grava checkpoint de recuperação."""
        return await self.record(
            session_id=session_id,
            event_type="checkpoint",
            agent_name="blueprint_executor",
            content=f"Checkpoint: {step_title} -> {status}",
            metadata={
                "step_id": step_id,
                "step_title": step_title,
                "checkpoint_status": status,
                "recovered": recovered,
            },
        )


# Instância singleton
trace_recorder = TraceRecorder()
