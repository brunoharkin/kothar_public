"""Seleção determinística de skills e recibos de evidência, sem aprovação autorreferente."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field

from backend.servicos.evolucao.avaliacoes import (
    Artifact,
    Contract,
    EvalResult,
    ExecutionResult,
    artifact_digest,
)

SECURITY_POLICY_SHA256 = "03556482c7fd06a11f0f31d3e7ae691912eaae47e4d6d7c941ec2f61e07e88a6"


class SkillError(ValueError):
    """Falha segura de seleção ou evidência; não divulga caminho do host."""


class SkillRecord(Contract):
    name: str
    description: str
    version: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    estimated_tokens: int = Field(ge=1)
    instructions: str


class SkillSelection(Contract):
    selection_id: str
    project_id: str
    catalog_version: str
    routing_sha256: str
    budget_tokens: int
    estimated_tokens: int
    token_accounting: Literal["conservative_utf8_estimate"] = "conservative_utf8_estimate"
    selected: tuple[SkillRecord, ...]
    omitted: tuple[str, ...] = ()


class SkillReceipt(Contract):
    receipt_id: str
    selection_id: str
    project_id: str
    skill_name: str
    skill_version: str
    skill_sha256: str
    catalog_version: str
    evidence: tuple[Artifact, ...]
    execution_id: str
    trace_ids: tuple[str, ...]
    # O recibo comprova vínculo/hashes; não atesta que todos os controles da skill passaram.
    status: Literal["evidence_recorded"] = "evidence_recorded"


def _normalized(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(char))


def _words(text: str) -> set[str]:
    stopwords = {"a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
                 "um", "uma", "para", "por", "com", "sem", "que", "quando", "ao", "se", "ou", "sobre",
                 "skill", "kothar", "ativar", "necessario", "necessaria", "execucao", "habilidade", "versao"}
    return set(re.findall(r"[a-z0-9]+", _normalized(text))) - stopwords


def _read_record(path: Path, root: Path) -> SkillRecord:
    if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root):
        raise SkillError("Skill fora do catálogo autorizado.")
    if path.stat().st_size > 128_000:
        raise SkillError("Skill acima do limite.")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        raise SkillError("Skill sem metadados canônicos.")
    front = text.split("\n---", 1)[0][4:]
    name_match = re.search(r"(?m)^name:\s*(['\"]?)([a-z0-9][a-z0-9-]{0,99})\1\s*$", front)
    if name_match is None or name_match.group(2) != path.parent.name:
        raise SkillError("Identidade da skill diverge do diretório.")
    description_match = re.search(r"(?ms)^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", front)
    description = " ".join(description_match.group(1).strip().lstrip(">|-").split()) if description_match else ""
    version_match = re.search(r"(?m)^version:\s*['\"]?([\w.-]+)", front)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return SkillRecord(name=name_match.group(2), description=description[:2000],
                       version=version_match.group(1) if version_match else f"sha256:{digest[:16]}",
                       sha256=digest, estimated_tokens=max(1, math.ceil(len(text.encode("utf-8")) / 3)),
                       instructions=text)


class SkillCatalog:
    """Raiz e roteamento são configuração do operador, nunca entrada arbitrária de uma rota."""

    def __init__(self, root: Path, routing_path: Path | None = None):
        if root.is_symlink() or not root.is_dir():
            raise SkillError("Catálogo de skills indisponível.")
        self.root = root.resolve(strict=True)
        self.routing_path = routing_path

    def _records(self) -> dict[str, SkillRecord]:
        records = {}
        try:
            for path in sorted(self.root.glob("*/SKILL.md")):
                record = _read_record(path, self.root)
                records[record.name] = record
                if len(records) > 500:
                    raise SkillError("Catálogo acima do limite.")
        except (OSError, UnicodeError) as exc:
            raise SkillError("Catálogo de skills ilegível.") from exc
        if not records:
            raise SkillError("Catálogo de skills vazio.")
        return records

    def _routing(self) -> tuple[dict, str]:
        if self.routing_path is None:
            return {"rules": []}, hashlib.sha256(b"{}").hexdigest()
        try:
            if self.routing_path.stat().st_size > 64_000:
                raise ValueError("size")
            raw = self.routing_path.read_bytes()
            routing = json.loads(raw)
            if routing.get("schema_version") != 1 or not isinstance(routing.get("rules"), list) or len(routing["rules"]) > 100:
                raise ValueError("schema")
            security_policy = None
            if self.routing_path.name == "kothar-skill-routing.json" or any(
                isinstance(rule, dict) and "security_surface" in rule for rule in routing["rules"]
            ):
                policy_raw = self.routing_path.with_name("kothar-security-policy.json").read_bytes()
                if hashlib.sha256(policy_raw).hexdigest() != SECURITY_POLICY_SHA256:
                    raise ValueError("security policy identity")
                security_policy = json.loads(policy_raw)
                if security_policy.get("fail_closed") is not True:
                    raise ValueError("security policy mode")
            for rule in routing["rules"]:
                if not isinstance(rule, dict) or set(rule) not in (
                    {"keywords", "skills", "required"}, {"keywords", "skills", "required", "security_surface"},
                ):
                    raise ValueError("rule")
                if type(rule["required"]) is not bool or any(
                    not isinstance(rule[key], list) or not rule[key] or len(rule[key]) > 50
                    or any(not isinstance(item, str) or not item.strip() or len(item) > 100 for item in rule[key])
                    for key in ("keywords", "skills")
                ):
                    raise ValueError("rule types")
                if "security_surface" in rule:
                    surface = rule["security_surface"]
                    if not isinstance(surface, str) or surface not in security_policy["surfaces"]:
                        raise ValueError("unknown security surface")
                    if rule["required"] is not True or sorted(rule["skills"]) != sorted(security_policy["surfaces"][surface]):
                        raise ValueError("security routing drift")
            if security_policy is not None and {rule.get("security_surface") for rule in routing["rules"]
                                               if "security_surface" in rule} != set(security_policy["surfaces"]):
                raise ValueError("incomplete security routing")
            return routing, hashlib.sha256(raw).hexdigest()
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            raise SkillError("Roteamento de skills inválido.") from exc

    def list_metadata(self) -> tuple[dict, ...]:
        """Não carrega instruções completas no contexto do consumidor."""
        return tuple(record.model_dump(exclude={"instructions"}) for record in self._records().values())

    def audit(self) -> dict:
        """Relata duplicações para revisão; não remove nem reescreve skills."""
        records = self._records()
        duplicates, overlaps = [], []
        items = sorted(records.items())
        for index, (left_name, left) in enumerate(items):
            left_body = left.instructions.split("\n---", 1)[-1].strip()
            left_words = _words(left.description)
            for right_name, right in items[index + 1:]:
                right_body = right.instructions.split("\n---", 1)[-1].strip()
                if left_body == right_body:
                    duplicates.append((left_name, right_name))
                right_words = _words(right.description)
                union = left_words | right_words
                similarity = len(left_words & right_words) / len(union) if union else 0
                if similarity >= .6:
                    overlaps.append({"skills": (left_name, right_name), "description_jaccard": round(similarity, 3)})
        return {"skill_count": len(records), "duplicate_bodies": tuple(duplicates),
                "description_overlaps": tuple(overlaps), "automatic_changes": False}

    def select(self, context: str, project_id: str, requested: tuple[str, ...] = (),
               budget_tokens: int = 1500) -> SkillSelection:
        if not context.strip() or len(context) > 32_000 or not re.fullmatch(r"[\w.-]{1,100}", project_id):
            raise SkillError("Contexto ou projeto inválido.")
        if type(budget_tokens) is not int or not 100 <= budget_tokens <= 32_000 or len(requested) > 30:
            raise SkillError("Orçamento de contexto inválido.")
        records = self._records()
        routing, routing_hash = self._routing()
        words = _words(context)
        scores: dict[str, int] = {}
        mandatory = set(requested)
        if not mandatory.issubset(records):
            raise SkillError("Skill solicitada não existe no catálogo.")
        for rule in routing["rules"]:
            if any(_words(keyword).issubset(words) for keyword in rule["keywords"]):
                for name in rule["skills"]:
                    if name not in records:
                        raise SkillError("Roteamento aponta para skill indisponível.")
                    scores[name] = scores.get(name, 0) + 100
                    if rule["required"]:
                        mandatory.add(name)
        for record in records.values():
            overlap = len(words & _words(f"{record.name} {record.description}"))
            name_words = _words(record.name)
            named = bool(name_words) and name_words.issubset(words)
            if overlap >= 3 or named:
                scores[record.name] = scores.get(record.name, 0) + overlap
        for name in mandatory:
            scores[name] = scores.get(name, 0) + 1000
        selected, omitted, used = [], [], 0
        for name in sorted(scores, key=lambda name: (name not in mandatory, -scores[name], name)):
            record = records[name]
            if used + record.estimated_tokens > budget_tokens:
                if name in mandatory:
                    raise SkillError("Skills obrigatórias excedem orçamento; amplie o orçamento ou particione a tarefa.")
                omitted.append(name)
                continue
            selected.append(record)
            used += record.estimated_tokens
        catalog_version = hashlib.sha256("\n".join(f"{name}:{record.sha256}" for name, record in sorted(records.items())).encode()).hexdigest()
        return SkillSelection(selection_id=str(uuid4()), project_id=project_id, catalog_version=catalog_version,
                              routing_sha256=routing_hash, budget_tokens=budget_tokens, estimated_tokens=used,
                              selected=tuple(selected), omitted=tuple(omitted))

    def receipt(self, selection: SkillSelection, skill_name: str, evidence: tuple[Artifact, ...],
                *, artifact_root: Path, execution: ExecutionResult | EvalResult) -> SkillReceipt:
        """execution deve vir do store do servidor; o cliente não é autoridade para traces."""
        if not evidence or len(evidence) > 30 or len({item.path for item in evidence}) != len(evidence):
            raise SkillError("Recibo exige evidências distintas e limitadas.")
        if execution.executor_kind == "test_double" or not execution.execution_id:
            raise SkillError("Recibo exige identidade de execução real.")
        traces = tuple(trace.id for trace in execution.tools if trace.status == "completed")
        declared = {(item.path, item.sha256) for item in execution.artifacts}
        if not traces or any((item.path, item.sha256) not in declared for item in evidence):
            raise SkillError("Evidências exigem traces concluídos e artefatos vinculados à execução.")
        selected = next((record for record in selection.selected if record.name == skill_name), None)
        records = self._records()
        current = records.get(skill_name)
        current_catalog = hashlib.sha256("\n".join(f"{name}:{record.sha256}" for name, record in sorted(records.items())).encode()).hexdigest()
        if selected is None or current is None or selected != current or selection.catalog_version != current_catalog:
            raise SkillError("Skill ou catálogo mudou; selecione novamente antes de registrar evidências.")
        if selection.routing_sha256 != self._routing()[1]:
            raise SkillError("Roteamento mudou; selecione novamente.")
        try:
            if any(artifact_digest(artifact_root, item.path) != item.sha256 for item in evidence):
                raise SkillError("Hash de evidência divergente.")
        except ValueError as exc:
            raise SkillError("Evidência inválida ou indisponível.") from exc
        return SkillReceipt(receipt_id=str(uuid4()), selection_id=selection.selection_id,
                            project_id=selection.project_id, skill_name=current.name,
                            skill_version=current.version, skill_sha256=current.sha256,
                            catalog_version=selection.catalog_version, evidence=evidence,
                            execution_id=execution.execution_id, trace_ids=traces)
