"""Correções viram propostas imutáveis e regressões; nunca alteram regras automaticamente."""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import Field, model_validator

from backend.servicos.evolucao.avaliacoes import Artifact, Contract, EvalCase


class FeedbackSubmission(Contract):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[\w.:-]+$")
    project_id: str = Field(min_length=1, max_length=100, pattern=r"^[\w.-]+$")
    prompt: str = Field(min_length=1, max_length=32_000)
    observed_response: str = Field(min_length=1, max_length=32_000)
    correction: str = Field(min_length=1, max_length=4000)
    evidence: tuple[Artifact, ...] = Field(default=(), max_length=30)
    # Predicados são uma opção explícita do revisor, não extraídos de texto pelo modelo.
    expected_contains: tuple[str, ...] = Field(default=(), max_length=30)
    forbidden_contains: tuple[str, ...] = Field(default=(), max_length=30)

    @model_validator(mode="after")
    def distinct_correction(self):
        if not self.prompt.strip() or not self.correction.strip() or not self.observed_response.strip():
            raise ValueError("Feedback exige conteúdo concreto.")
        if self.correction.strip() == self.observed_response.strip():
            raise ValueError("Correção deve diferir da resposta observada.")
        return self


class RegressionCase(Contract):
    source_feedback_id: str
    case: EvalCase
    status: Literal["draft_requires_review"] = "draft_requires_review"


class FeedbackProposal(Contract):
    proposal_id: str
    project_id: str
    source_feedback_id: str
    version: int = Field(ge=1)
    previous_sha256: str | None
    content_sha256: str
    proposed_instruction: str
    regression: RegressionCase
    evidence: tuple[Artifact, ...]
    status: Literal["draft"] = "draft"
    automatic_application: Literal[False] = False


def propose_feedback(submission: FeedbackSubmission, previous_version: int = 0,
                     previous_sha256: str | None = None) -> FeedbackProposal:
    """Função pura. Persistência e concorrência/versionamento transacional pertencem ao store."""
    import re

    if type(previous_version) is not int or not 0 <= previous_version < 1_000_000:
        raise ValueError("Versão anterior inválida.")
    if (previous_version == 0) != (previous_sha256 is None) or previous_sha256 is not None and not re.fullmatch(r"[a-f0-9]{64}", previous_sha256):
        raise ValueError("Cadeia de versões inválida.")
    regression_id = "feedback-" + hashlib.sha256(f"{submission.project_id}:{submission.id}".encode()).hexdigest()[:32]
    case = EvalCase(id=regression_id, project_id=submission.project_id,
                    prompt=submission.prompt, expected_contains=submission.expected_contains,
                    forbidden_contains=submission.forbidden_contains,
                    required_behaviors=(submission.correction,))
    content_hash = hashlib.sha256(submission.model_dump_json().encode("utf-8")).hexdigest()
    proposal_id = hashlib.sha256(f"{submission.project_id}:{submission.id}:{previous_version + 1}:{previous_sha256}:{content_hash}".encode()).hexdigest()
    return FeedbackProposal(proposal_id=proposal_id, project_id=submission.project_id,
                            source_feedback_id=submission.id, version=previous_version + 1,
                            previous_sha256=previous_sha256, content_sha256=content_hash,
                            proposed_instruction=submission.correction,
                            regression=RegressionCase(source_feedback_id=submission.id, case=case),
                            evidence=submission.evidence)
