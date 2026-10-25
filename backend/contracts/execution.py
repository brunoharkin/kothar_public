"""Contratos tipados para estado, handoff e revisão de execuções."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ExecutionMode = Literal["discovery", "design", "build", "verify", "ship", "debug", "change"]
ExecutionPhase = Literal[
    "triage", "blueprint", "execution", "review", "security", "qa", "evaluator", "checkpoint", "done"
]
ExecutionStatus = Literal["pending", "running", "blocked", "completed", "failed", "partial"]


class Handoff(BaseModel):
    """Passagem de contexto entre agentes sem campos livres obrigatórios."""

    model_config = ConfigDict(extra="forbid")

    agent: str = Field(min_length=1)
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    files: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    acceptance: list[str] = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_agent: str | None = None


class ReviewAttempt(BaseModel):
    """Resultado de uma tentativa de revisão independente."""

    model_config = ConfigDict(extra="forbid")

    attempt: int = Field(ge=1, le=3)
    reviewer: str = Field(min_length=1)
    status: Literal["approved", "changes_requested", "blocked"]
    findings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    """Contrato final do reviewer, com limite explícito de tentativas."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["approved", "changes_requested", "blocked"]
    attempts: list[ReviewAttempt] = Field(min_length=1, max_length=3)
    risks: list[str] = Field(min_length=3, max_length=5)
    metric: str = Field(min_length=1)
    tradeoffs: list[str] = Field(min_length=1)
    scope_out: list[str] = Field(min_length=1)
    dod: list[str] = Field(min_length=1)
    recommendation: Literal["vai", "não vai", "vai com ressalvas"]


class ExecutionState(BaseModel):
    """Estado serializável compartilhado pelo Core e pelos agentes."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    mode: ExecutionMode
    phase: ExecutionPhase = "triage"
    status: ExecutionStatus = "pending"
    objective: str = Field(min_length=1)
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)
    active_agent: str | None = None
    completed_agents: list[str] = Field(default_factory=list)
    pending_agents: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0, le=3)
    blockers: list[str] = Field(default_factory=list)
    next_agent: str | None = None

    def apply_handoff(self, handoff: Handoff) -> "ExecutionState":
        """Atualiza estado sem apagar evidências ou contexto anterior."""
        self.active_agent = handoff.agent
        self.artifacts = sorted(set(self.artifacts + handoff.files))
        self.evidence = sorted(set(self.evidence + handoff.evidence))
        self.blockers = list(handoff.blockers)
        self.next_agent = handoff.next_agent
        if handoff.status == "completed" and handoff.agent not in self.completed_agents:
            self.completed_agents.append(handoff.agent)
        if handoff.next_agent:
            self.pending_agents = [
                agent for agent in self.pending_agents if agent != handoff.next_agent
            ]
            if handoff.next_agent not in self.completed_agents:
                self.pending_agents.append(handoff.next_agent)
        self.status = "blocked" if handoff.blockers else "running"
        return self
