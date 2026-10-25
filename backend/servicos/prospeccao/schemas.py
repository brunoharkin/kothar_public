"""Contratos estritos para prospecção: evidência não equivale a venda ou consentimento."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_text(value: str) -> str:
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c)).split()
    )


def public_website(value: str) -> str:
    """Canonicalização sintática; transporte ainda valida DNS e autorização do domínio."""
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or "\\" in value:
        raise ValueError("Site inválido")
    value = value.strip()
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise ValueError("Site inválido")
    host = public_hostname(parsed.hostname or "")
    if parsed.port not in {None, 443, 80}:
        raise ValueError("Domínio inválido")
    return urlunsplit(("https", host, "/", "", ""))


def public_hostname(value: str) -> str:
    host = value.encode("idna").decode("ascii").lower().rstrip(".")
    if len(host) > 253 or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host):
        raise ValueError("Domínio inválido")
    if host.endswith((".localhost", ".local", ".internal", ".home.arpa", ".lan", ".corp", ".onion", ".invalid")):
        raise ValueError("Domínio interno bloqueado")
    return host


def utcnow() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    @field_validator("*", mode="after")
    @classmethod
    def no_controls(cls, value):
        if isinstance(value, str) and any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("Caracteres de controle não permitidos")
        return value


UF = Literal["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
SignalCode = Literal["wordpress", "meta_pixel", "google_tag", "booking_link", "booking_not_observed", "hiring_page"]


class DiscoveryRequest(StrictModel):
    category: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=100)
    state: UF
    latitude: float | None = Field(default=None, ge=-34, le=6, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-74, le=-34, allow_inf_nan=False)
    radius_m: int = Field(default=3000, ge=100, le=10000)
    limit: int = Field(default=10, ge=1, le=25)

    @field_validator("city")
    @classmethod
    def city_is_name(cls, value: str) -> str:
        if not all(c.isalpha() or c in " -'." for c in value):
            raise ValueError("Informe o nome do município")
        return value

    @model_validator(mode="after")
    def coordinates_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude e longitude devem ser informadas juntas")
        return self


class Evidence(StrictModel):
    source_url: str = Field(max_length=2048)
    observation: str = Field(min_length=1, max_length=300)
    method: Literal["osm_tag", "html_heuristic", "provider_response", "user_report"]
    observed_at: datetime = Field(default_factory=utcnow)


class Business(StrictModel):
    source_id: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(max_length=80)
    city: str = Field(max_length=100)
    state: UF
    website_url: str | None = Field(default=None, max_length=2048)
    evidence: list[Evidence] = Field(default_factory=list, max_length=3)

    @field_validator("website_url")
    @classmethod
    def validate_site(cls, value):
        return public_website(value) if value else None


class DiscoveryResult(StrictModel):
    businesses: list[Business] = Field(max_length=25)
    attribution: str = "© OpenStreetMap contributors — ODbL 1.0"
    coverage: str = "Amostra limitada aos registros disponíveis no OpenStreetMap; não é lista completa nem cadastro oficial de empresas."
    truncated: bool = False
    expires_at: datetime = Field(default_factory=lambda: utcnow() + timedelta(days=7))


class Signal(StrictModel):
    code: SignalCode
    label: str = Field(max_length=160)
    confidence: Literal["heuristic"] = "heuristic"
    limitation: str = Field(max_length=300)
    evidence: Evidence


class PublishedContact(StrictModel):
    email: str = Field(min_length=5, max_length=254)
    status: Literal["published_unverified", "provider_verified", "provider_rejected", "provider_unknown"] = "published_unverified"
    mx_status: Literal["not_checked", "present", "absent", "unknown"] = "not_checked"
    source_url: str = Field(max_length=2048)
    verification: Evidence | None = None

    @field_validator("email")
    @classmethod
    def email_syntax(cls, value):
        if not re.fullmatch(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}", value):
            raise ValueError("E-mail inválido")
        return value.casefold()

    @model_validator(mode="after")
    def verification_evidence_required(self):
        if self.status == "provider_verified" and (not self.verification or self.verification.method != "provider_response"):
            raise ValueError("Verificação requer evidência do provedor")
        return self


class ProfileRequest(StrictModel):
    business: Business
    check_mx: bool = False
    verify_contacts: bool = False


class Profile(StrictModel):
    business: Business
    signals: list[Signal] = Field(default_factory=list, max_length=6)
    contacts: list[PublishedContact] = Field(default_factory=list, max_length=5)
    coverage: str = "Uma página HTML, sem executar JavaScript; sinais são heurísticos e contatos públicos não representam consentimento."
    expires_at: datetime = Field(default_factory=lambda: utcnow() + timedelta(days=7))


class ICPRequest(StrictModel):
    target_categories: list[str] = Field(min_length=1, max_length=15)
    target_states: list[UF] = Field(default_factory=list, max_length=27)
    desired_signals: list[SignalCode] = Field(default_factory=list, max_length=6)

    @field_validator("target_categories")
    @classmethod
    def bounded_categories(cls, values):
        if any(not 2 <= len(value) <= 80 for value in values):
            raise ValueError("Categoria inválida")
        return values


class ScoreResult(StrictModel):
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(max_length=10)
    unknowns: list[str] = Field(default_factory=lambda: ["Tamanho da empresa", "Faturamento", "Intenção de compra"])


class BANTAnswer(StrictModel):
    status: Literal["unknown", "confirmed", "negative"] = "unknown"
    evidence: str | None = Field(default=None, min_length=1, max_length=500)

    @model_validator(mode="after")
    def requires_evidence(self):
        if self.status != "unknown" and not self.evidence:
            raise ValueError("Resposta BANT conhecida requer evidência informada")
        return self


class BANTRequest(StrictModel):
    budget: BANTAnswer = Field(default_factory=BANTAnswer)
    authority: BANTAnswer = Field(default_factory=BANTAnswer)
    need: BANTAnswer = Field(default_factory=BANTAnswer)
    timing: BANTAnswer = Field(default_factory=BANTAnswer)


class BANTResult(StrictModel):
    answers: BANTRequest
    confirmed_count: int = Field(ge=0, le=4)
    qualified: bool
    next_questions: list[str] = Field(max_length=4)
    limitation: str = "Evidências são declarações fornecidas pelo usuário; qualificação não foi inferida do site."


class DraftRequest(StrictModel):
    profile: Profile
    offer: str = Field(min_length=3, max_length=240)
    signal_code: SignalCode | None = None
    objection: Literal["price", "timing", "existing_supplier", "not_interested"] | None = None


class Draft(StrictModel):
    status: Literal["draft"] = "draft"
    sent: Literal[False] = False
    subject: str = Field(max_length=250)
    body: str = Field(max_length=2000)
    followups: list[str] = Field(max_length=2)
    objection_steps: dict[str, str] = Field(default_factory=dict)
    evidence: Evidence | None = None
    requires_review: Literal[True] = True
    cadence_days: list[int] = Field(default_factory=lambda: [3, 7], max_length=2)
