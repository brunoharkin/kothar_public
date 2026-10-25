"""Prospecção local determinística: descoberta, observações e rascunhos, sem envio."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from html import unescape
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urlsplit

from pydantic import ValidationError

from backend.core.web_fetcher import extract_urls

from .schemas import (
    BANTRequest,
    BANTResult,
    Business,
    DiscoveryRequest,
    DiscoveryResult,
    Draft,
    DraftRequest,
    Evidence,
    ICPRequest,
    Profile,
    ProfileRequest,
    PublishedContact,
    ScoreResult,
    Signal,
    normalize_text,
    public_website,
)
from .transport import FetchResult, ProspeccaoError, SecureTransport

# Valores usados na consulta são constantes; entrada humana nunca vira sintaxe Overpass.
CATEGORY_TAGS = {
    "restaurante": ("amenity", "restaurant"), "pizzaria": ("amenity", "restaurant"),
    "lanchonete": ("amenity", "fast_food"), "cafeteria": ("amenity", "cafe"),
    "padaria": ("shop", "bakery"), "dentista": ("amenity", "dentist"),
    "clinica odontologica": ("amenity", "dentist"), "clinica medica": ("amenity", "clinic"),
    "hospital": ("amenity", "hospital"), "farmacia": ("amenity", "pharmacy"),
    "academia": ("leisure", "fitness_centre"), "salao de beleza": ("shop", "beauty"),
    "cabeleireiro": ("shop", "hairdresser"), "barbearia": ("shop", "hairdresser"),
    "hotel": ("tourism", "hotel"), "pousada": ("tourism", "guest_house"),
    "pet shop": ("shop", "pet"), "veterinario": ("amenity", "veterinary"),
    "imobiliaria": ("office", "estate_agent"), "advocacia": ("office", "lawyer"),
    "contabilidade": ("office", "accountant"), "escola": ("amenity", "school"),
    "supermercado": ("shop", "supermarket"), "oficina mecanica": ("shop", "car_repair"),
    "agencia de marketing": ("office", "advertising_agency"), "saas": ("office", "it"),
}
CATEGORY_ALIASES = {"dentistas": "dentista", "clinicas odontologicas": "clinica odontologica", "restaurantes": "restaurante", "agencia marketing": "agencia de marketing", "marketing agency": "agencia de marketing", "clinica": "clinica medica", "hoteis": "hotel", "saloes de beleza": "salao de beleza"}
PROVIDER_HOSTS = {"overpass-api.de", "photon.komoot.io"}
GENERAL_MAILBOXES = frozenset({"contato", "comercial", "atendimento", "vendas", "info", "hello", "geral", "recepcao", "suporte"})
STATE_NAMES = dict(zip(
    ("AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"),
    ("Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", "Distrito Federal", "Espírito Santo", "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", "Roraima", "Santa Catarina", "São Paulo", "Sergipe", "Tocantins"),
    strict=True,
))
SHARED_DOMAINS = frozenset({"facebook.com", "instagram.com", "linkedin.com", "google.com", "wa.me", "linktr.ee"})
SIGNAL_TEXT = {
    "wordpress": ("Marcas de WordPress no HTML", "A marca pode estar desatualizada; não confirma versão nem vulnerabilidade."),
    "meta_pixel": ("Referência ao Meta Pixel no HTML", "Pixel não comprova anúncios ativos, investimento ou desempenho."),
    "google_tag": ("Referência a tag Google no HTML", "Tag não comprova campanha ativa nem investimento em anúncios."),
    "booking_link": ("Link com padrão de agendamento", "O link não comprova funcionamento ou utilização do agendamento."),
    "booking_not_observed": ("Padrão de agendamento não observado nesta página", "A ausência do padrão em uma página não prova ausência de agendamento."),
    "hiring_page": ("Link com padrão de página de vagas", "O link não comprova vaga aberta nem crescimento atual."),
}


def category_tags(category: str) -> tuple[str, str]:
    key = normalize_text(category)
    key = CATEGORY_ALIASES.get(key, key)
    if key not in CATEGORY_TAGS:
        raise ProspeccaoError("unsupported_category")
    return CATEGORY_TAGS[key]


class EmailVerifier(Protocol):
    """Adaptador server-side; status só pode vir de resposta real do provedor."""

    name: str

    async def verify(self, email: str) -> tuple[str, Evidence]: ...


class PageFacts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.visible: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if tag == "a":
            href = dict(attrs).get("href")
            if href and len(self.links) < 1000:
                self.links.append(href[:2048])

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


class ProspeccaoService:
    """Sem persistência de HTML ou contatos; a API salva resultados mínimos com TTL.

    `transport`, `allowed_domains`, `verifier` e `quota_guard` só são definidos
    no servidor, nunca desserializados do corpo enviado pelo usuário.
    """

    def __init__(
        self,
        *,
        allowed_domains: set[str] | None = None,
        transport=None,
        mx_lookup: Callable[[str], Awaitable[bool | None]] | None = None,
        verifier: EmailVerifier | None = None,
        quota_guard: Callable[[str, str], Awaitable[bool]] | None = None,
        clock: Callable[[], float] = time.monotonic,
        enabled: bool | None = None,
    ):
        configured = {host.strip().lower() for host in os.getenv("KOTHAR_PROSPECCAO_SITE_DOMAINS", "").split(",") if host.strip()}
        self.allowed_domains = frozenset(allowed_domains if allowed_domains is not None else configured)
        self.transport = transport or SecureTransport(
            set(self.allowed_domains) | PROVIDER_HOSTS,
            user_agent=os.getenv("KOTHAR_PROSPECCAO_USER_AGENT", "KotharProspeccao/1.0"),
        )
        self.enabled = os.getenv("KOTHAR_PROSPECCAO_ENABLED") == "1" if enabled is None else enabled
        self.mx_lookup = mx_lookup
        self.verifier = verifier
        self.quota_guard = quota_guard
        self.clock = clock
        self._geocache: OrderedDict[str, tuple[float, tuple[float, float]]] = OrderedDict()
        self._geolock = asyncio.Lock()

    def _ensure_enabled(self, caller_id: str) -> None:
        if not self.enabled:
            raise ProspeccaoError("prospeccao_disabled")
        if not isinstance(caller_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,128}", caller_id):
            raise ProspeccaoError("invalid_caller")

    async def _reserve_quota(self, caller_id: str, provider: str) -> None:
        # Autoridade de limite pertence ao store persistente da API, não a memória do processo.
        try:
            allowed = self.quota_guard is not None and await self.quota_guard(caller_id, provider)
        except Exception:
            raise ProspeccaoError("external_quota_unavailable") from None
        if allowed is not True:
            raise ProspeccaoError("external_quota_unavailable")

    async def _request(self, caller_id, provider, method, url, **kwargs) -> FetchResult:
        self._ensure_enabled(caller_id)
        await self._reserve_quota(caller_id, provider)
        return await self.transport.request(method, url, **kwargs)

    async def _geocode(self, request: DiscoveryRequest, caller_id: str) -> tuple[float, float]:
        if request.latitude is not None:
            return request.latitude, request.longitude
        if os.getenv("KOTHAR_PROSPECCAO_GEOCODER") != "photon":
            raise ProspeccaoError("geocoder_not_configured_supply_coordinates")
        cache_key = hashlib.sha256(f"{caller_id}:{normalize_text(request.city)}:{request.state}".encode()).hexdigest()
        async with self._geolock:
            cached = self._geocache.get(cache_key)
            if cached and self.clock() - cached[0] < 86400:
                self._geocache.move_to_end(cache_key)
                return cached[1]
            result = await self._request(caller_id, "geocoder", "GET", "https://photon.komoot.io/api/", params={"q": f"{request.city}, {request.state}, Brasil", "limit": 3, "lang": "default", "osm_tag": "place:city"})
            try:
                features = json.loads(result.text)["features"]
                if not isinstance(features, list):
                    raise ValueError
                for feature in features[:3]:
                    if not isinstance(feature, dict):
                        continue
                    properties = feature.get("properties", {})
                    if not isinstance(properties, dict):
                        continue
                    if str(properties.get("countrycode", "")).upper() != "BR":
                        continue
                    if normalize_text(str(properties.get("name", ""))) != normalize_text(request.city):
                        continue
                    if normalize_text(str(properties.get("state", ""))) != normalize_text(STATE_NAMES[request.state]):
                        continue
                    if properties.get("osm_value") not in {"city", "town", "village", "municipality"}:
                        continue
                    longitude, latitude = feature["geometry"]["coordinates"][:2]
                    validated = request.model_copy(update={"latitude": latitude, "longitude": longitude})
                    validated = DiscoveryRequest.model_validate(validated.model_dump())
                    coordinates = (validated.latitude, validated.longitude)
                    self._geocache[cache_key] = (self.clock(), coordinates)
                    while len(self._geocache) > 128:
                        self._geocache.popitem(last=False)
                    return coordinates
            except (ValueError, KeyError, TypeError, IndexError):
                pass
            raise ProspeccaoError("municipality_not_resolved")

    async def discover(self, request: DiscoveryRequest, caller_id: str) -> DiscoveryResult:
        self._ensure_enabled(caller_id)
        request = DiscoveryRequest.model_validate(request)
        key, value = category_tags(request.category)
        latitude, longitude = await self._geocode(request, caller_id)
        query = f'[out:json][timeout:12][maxsize:2000000];nwr(around:{request.radius_m},{latitude},{longitude})["{key}"="{value}"];out center tags {request.limit + 1};'
        result = await self._request(caller_id, "overpass", "POST", "https://overpass-api.de/api/interpreter", data={"data": query})
        try:
            elements = json.loads(result.text)["elements"]
            if not isinstance(elements, list):
                raise ValueError
        except (ValueError, KeyError, TypeError):
            raise ProspeccaoError("invalid_provider_response") from None
        businesses, seen = [], set()
        for element in elements[:100]:
            tags = element.get("tags", {}) if isinstance(element, dict) else {}
            if not isinstance(tags, dict) or not isinstance(tags.get("name"), str):
                continue
            name = " ".join(tags["name"].split())[:160]
            if not name:
                continue
            website = None
            try:
                raw_site = tags.get("website") or tags.get("contact:website")
                website = public_website(raw_site) if isinstance(raw_site, str) else None
                if website and any((urlsplit(website).hostname or "").removeprefix("www.") == domain for domain in SHARED_DOMAINS):
                    website = None
            except (ValueError, UnicodeError):
                pass
            identity = urlsplit(website).hostname.removeprefix("www.") if website else normalize_text(name)
            if identity in seen or not re.fullmatch(r"node|way|relation", str(element.get("type", ""))) or not str(element.get("id", "")).isdigit():
                continue
            source_id = f'{element["type"]}/{element["id"]}'
            source_url = f"https://www.openstreetmap.org/{source_id}"
            try:
                business = Business(source_id=source_id, name=name, category=request.category, city=request.city, state=request.state, website_url=website, evidence=[Evidence(source_url=source_url, observation=f"Registro OSM com tag {key}={value}; nome e site não foram verificados independentemente.", method="osm_tag")])
            except ValidationError:
                continue
            seen.add(identity)
            businesses.append(business)
            if len(businesses) == request.limit:
                break
        return DiscoveryResult(businesses=businesses, truncated=len(elements) > request.limit, coverage="Amostra limitada aos registros OSM no raio consultado; deduplicada por domínio ou nome. Cidade/UF identificam a busca, não comprovam endereço fiscal. Não é lista completa nem cadastro oficial. Categorias amplas podem incluir negócios diferentes, especialmente SaaS/IT, agências, pizzarias/restaurantes e barbearias/cabeleireiros.")

    async def profile(self, request: ProfileRequest, caller_id: str) -> Profile:
        self._ensure_enabled(caller_id)
        request = ProfileRequest.model_validate(request)
        website = request.business.website_url
        if not website:
            raise ProspeccaoError("business_has_no_website")
        domain = urlsplit(website).hostname
        if domain not in self.allowed_domains:
            raise ProspeccaoError("website_not_authorized")
        result = await self._request(caller_id, "website", "GET", website)
        if result.content_type not in {"text/html", "application/xhtml+xml"}:
            raise ProspeccaoError("unsupported_content_type")
        facts = PageFacts()
        facts.feed(result.text[:1_000_000])
        html = result.text.casefold()
        links = facts.links + extract_urls(result.text)
        booking = any(re.search(r"(?:^|[/.:_-])(?:calendly|cal\.com|agend(?:a|ar|amento)|reserv(?:a|ar)|booking)(?:[/.?_-]|$)", link.casefold()) for link in links)
        checks = {"wordpress": "wp-content/" in html or "wp-includes/" in html, "meta_pixel": "connect.facebook.net" in html or "fbq(" in html, "google_tag": "googletagmanager.com" in html or "gtag(" in html, "booking_link": booking, "booking_not_observed": not booking, "hiring_page": any(re.search(r"(?:carreiras|trabalhe-conosco|/vagas|/careers)", link.casefold()) for link in facts.links)}
        signals = [Signal(code=code, label=SIGNAL_TEXT[code][0], limitation=SIGNAL_TEXT[code][1], evidence=Evidence(source_url=website, observation=SIGNAL_TEXT[code][0], method="html_heuristic")) for code, detected in checks.items() if detected]
        # Apenas caixas gerais publicadas; nada de gerar padrões, nomes de pessoas ou SMTP.
        text = " ".join(facts.visible + [link[7:].split("?", 1)[0] for link in facts.links if link.casefold().startswith("mailto:")])
        emails = sorted({email.casefold() for email in re.findall(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", unescape(text))})
        owned_domains = {domain, domain.removeprefix("www.")}
        emails = [email for email in emails if email.rsplit("@", 1)[0] in GENERAL_MAILBOXES and email.rsplit("@", 1)[1] in owned_domains][:5]
        contacts = []
        mx_status = "not_checked"
        if request.check_mx and emails:
            if self.mx_lookup is None:
                mx_status = "unknown"
            else:
                # Resolver fornecido pelo servidor; sem consulta SMTP à caixa postal.
                await self._reserve_quota(caller_id, "email_verifier")
                try:
                    mx = await asyncio.wait_for(self.mx_lookup(domain.removeprefix("www.")), timeout=4)
                except (OSError, ValueError, TimeoutError):
                    mx = None
                mx_status = "present" if mx is True else "absent" if mx is False else "unknown"
        for email in emails:
            contact = PublishedContact(email=email, source_url=website, mx_status=mx_status)
            if request.verify_contacts and self.verifier is not None:
                if self.verifier.name not in {"reoon", "zerobounce", "hunter"}:
                    raise ProspeccaoError("email_provider_not_allowed")
                await self._reserve_quota(caller_id, "email_verifier")
                try:
                    status, evidence = await asyncio.wait_for(self.verifier.verify(email), timeout=12)
                except (OSError, ValueError, TimeoutError):
                    raise ProspeccaoError("email_provider_unavailable") from None
                if status not in {"provider_verified", "provider_rejected", "provider_unknown"}:
                    raise ProspeccaoError("invalid_verification_response")
                contact = PublishedContact(email=email, source_url=website, mx_status=mx_status, status=status, verification=evidence)
            contacts.append(contact)
        return Profile(business=request.business, signals=signals, contacts=contacts)


def score_icp(profile: Profile, request: ICPRequest) -> ScoreResult:
    profile, request = Profile.model_validate(profile), ICPRequest.model_validate(request)
    score, reasons = 0, []
    target_tags = {category_tags(category) for category in request.target_categories}
    if category_tags(profile.business.category) in target_tags:
        score += 50
        reasons.append("+50: categoria corresponde ao ICP pelas tags OSM")
    else:
        reasons.append("+0: categoria fora do ICP")
    if not request.target_states or profile.business.state in request.target_states:
        score += 20
        reasons.append("+20: região aceita pelo ICP")
    else:
        reasons.append("+0: região fora do ICP")
    if profile.business.website_url:
        score += 10
        reasons.append("+10: site disponível para pesquisa")
    desired = set(request.desired_signals)
    observed = {signal.code for signal in profile.signals}
    signal_points = round(20 * len(desired & observed) / len(desired)) if desired else 0
    score += signal_points
    reasons.append(f"+{signal_points}: {len(desired & observed)}/{len(desired)} sinais desejados observados; observação não comprova necessidade")
    return ScoreResult(score=score, reasons=reasons)


def qualify_bant(request: BANTRequest) -> BANTResult:
    request = BANTRequest.model_validate(request)
    questions = {"budget": "Há orçamento definido para esta iniciativa?", "authority": "Quem participa da decisão de contratação?", "need": "Qual problema foi confirmado pela empresa?", "timing": "Existe prazo definido para resolver o problema?"}
    answers = [getattr(request, field) for field in questions]
    confirmed = sum(answer.status == "confirmed" for answer in answers)
    return BANTResult(answers=request, confirmed_count=confirmed, qualified=confirmed == 4, next_questions=[question for field, question in questions.items() if getattr(request, field).status == "unknown"])


def draft_outreach(request: DraftRequest) -> Draft:
    request = DraftRequest.model_validate(request)
    signals = request.profile.signals
    chosen = next((signal for signal in signals if signal.code == request.signal_code), None) if request.signal_code else next((signal for signal in signals if signal.code != "booking_not_observed"), None)
    if request.signal_code and chosen is None:
        raise ProspeccaoError("signal_not_observed")
    name = request.profile.business.name
    observation = f"Ao consultar {chosen.evidence.source_url}, observei: {chosen.label.lower()}. {chosen.limitation}" if chosen else "Ainda não há sinal positivo suficiente para afirmar uma necessidade específica."
    body = f"Olá, equipe {name}. {observation} Trabalho com {request.offer}. Esse tema é uma prioridade para vocês? Se houver interesse, posso compartilhar uma ideia específica. Se preferirem não receber contato, basta informar."
    steps = {}
    if request.objection:
        questions = {"price": "Qual resultado e faixa de investimento fariam sentido avaliar?", "timing": "Em que momento esse tema poderia voltar à pauta?", "existing_supplier": "Há alguma necessidade que o fornecedor atual ainda não atende?", "not_interested": "Vou respeitar a preferência e encerrar o contato."}
        steps = {"listen": "Registrar a objeção sem presumir sua causa.", "acknowledge": "Entendo e respeito sua posição.", "assess": questions[request.objection], "respond": "Responder apenas com informações e condições comprovadas; não inventar descontos ou promessas.", "confirm": "Confirmar se a resposta ajudou; respeitar recusa e pedido de descadastramento."}
    if request.objection == "not_interested":
        return Draft(subject=f"Encerramento do contato com {name}"[:250], body=f"Olá, equipe {name}. Entendo e respeito sua preferência. Encerramos esta abordagem e não faremos novos acompanhamentos sobre ela.", followups=[], cadence_days=[], objection_steps=steps)
    return Draft(subject=f"Uma pergunta para {name}"[:250], body=body, followups=[f"Olá, equipe {name}. Esse tema tem relação com alguma prioridade atual? Posso detalhar se for útil.", "Encerrando este contato para respeitar seu tempo. Se fizer sentido no futuro, fico à disposição."], objection_steps=steps, evidence=chosen.evidence if chosen else None)
