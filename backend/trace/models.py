"""
=============================================================
 KOTHAR v4.0 — Modelos SQLAlchemy (Data Lake)
 Engenheiro Kothar | Ugarit Digital
=============================================================
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    """Sessão de trabalho do agente."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_model: Mapped[str | None] = mapped_column(String(100))
    task_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active")
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relacionamentos
    traces: Mapped[list["Trace"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    blueprints: Mapped[list["Blueprint"]] = relationship(back_populates="session")


class Trace(Base):
    """Registro granular de cada ação do agente."""

    __tablename__ = "traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(200))
    tool_input: Mapped[dict | None] = mapped_column(JSONB)
    tool_output: Mapped[dict | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[Session] = relationship(back_populates="traces")


class Skill(Base):
    """Skill cristalizada pelo Maestro."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    chroma_doc_id: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=100.0)
    forged_by: Mapped[str | None] = mapped_column(String(100))
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sessions.id"), name="source_session"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utc_now
    )


class Lock(Base):
    """Trava criada pelo Trace Analyser para evitar erros repetidos."""

    __tablename__ = "locks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    alternative: Mapped[str | None] = mapped_column(Text)
    chroma_doc_id: Mapped[str | None] = mapped_column(String(200))
    trigger_count: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str | None] = mapped_column(String(100))
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sessions.id"), name="source_session"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Blueprint(Base):
    """Plano de tarefa gerenciado pelo Maestro."""

    __tablename__ = "blueprints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sessions.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    steps: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    assigned_agent: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[Session | None] = relationship(back_populates="blueprints")


class FlowExecution(Base):
    """
    Registro de execução de um blueprint completo.
    Mantém histórico de todas as execuções de fluxo.
    """

    __tablename__ = "flow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sessions.id"))
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("blueprints.id"))
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, completed, failed, partial
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    completed_steps: Mapped[int] = mapped_column(Integer, default=0)
    failed_steps: Mapped[int] = mapped_column(Integer, default=0)
    skipped_steps: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    checkpoint_recovered: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    session: Mapped[Session | None] = relationship("Session")
    blueprint: Mapped[Blueprint | None] = relationship("Blueprint")
