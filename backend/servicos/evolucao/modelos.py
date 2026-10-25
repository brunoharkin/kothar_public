"""Contratos estritos do núcleo durável; identidade vem da sessão do servidor."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("*", mode="after")
    @classmethod
    def bounded_json(cls, value: Any) -> Any:
        if isinstance(value, (dict, list)):
            try:
                serialized = json.dumps(value, allow_nan=False, ensure_ascii=False)
            except (TypeError, ValueError) as exc:
                raise ValueError("valor JSON inválido") from exc
            if len(serialized.encode()) > 65536:
                raise ValueError("payload excede 64 KiB")
        return value


class FactInput(StrictInput):
    content: str = Field(min_length=1, max_length=8000)
    source: str = Field(min_length=1, max_length=2048)
    observed_at: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    expires_at: int | None = Field(default=None, ge=0)
    category: str = Field(default="decision", min_length=1, max_length=80)


class TaskInput(StrictInput):
    title: str = Field(min_length=1, max_length=300)
    dedupe_key: str = Field(min_length=1, max_length=160)
    category: Literal["repair", "resume", "new"] = "new"
    priority: int = Field(default=50, ge=0, le=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list, max_length=30)
    max_attempts: int = Field(default=3, ge=1, le=5)
    retry_safe: bool = False


class BudgetUsageInput(StrictInput):
    tokens: int = Field(default=0, ge=0, le=1_000_000_000)
    calls: int = Field(default=0, ge=0, le=1_000_000)
    cost_microunits: int = Field(default=0, ge=0, le=1_000_000_000_000)


class BudgetLimitInput(BudgetUsageInput):
    pass


class ActionInput(StrictInput):
    tool: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_.-]*$")
    scope: str = Field(min_length=1, max_length=160)
    payload: dict[str, Any]
    dedupe_key: str = Field(min_length=1, max_length=160)
    expires_at: int = Field(ge=0)
    review: str = Field(min_length=1, max_length=4000)


class ApprovalInput(StrictInput):
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope: str = Field(min_length=1, max_length=160)
    expires_at: int = Field(ge=0)
    decision: Literal["approve", "reject"] = "approve"


class FeedbackInput(StrictInput):
    task_id: str | None = Field(default=None, max_length=100)
    correction: str = Field(min_length=1, max_length=8000)
    evidence: str = Field(min_length=1, max_length=8000)
    proposal: str = Field(min_length=1, max_length=8000)


class ProspectInput(StrictInput):
    company: str = Field(min_length=1, max_length=300)
    domain: str = Field(min_length=1, max_length=253)
    source: str = Field(min_length=1, max_length=2048)
    signal: str = Field(min_length=1, max_length=2000)
    observed_at: int = Field(ge=0)
    contact: str | None = Field(default=None, max_length=320)
    contact_verified: bool = False
    next_step: str = Field(min_length=1, max_length=2000)


class EvolutionError(ValueError):
    """Erro de domínio com código seguro para API; não inclui payloads."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
