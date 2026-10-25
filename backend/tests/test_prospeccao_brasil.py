"""Fixtures sintéticas: nenhuma consulta a empresas, contatos ou serviços reais."""

import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from backend.servicos.prospeccao import (
    BANTAnswer,
    BANTRequest,
    Business,
    DiscoveryRequest,
    DraftRequest,
    Evidence,
    ICPRequest,
    ProfileRequest,
    ProspeccaoError,
    ProspeccaoService,
    PublishedContact,
    category_tags,
    draft_outreach,
    qualify_bant,
    score_icp,
)
from backend.servicos.prospeccao.schemas import public_website
from backend.servicos.prospeccao.transport import FetchResult, SecureTransport


async def permit(_caller, _provider):
    return True


class FakeTransport:
    def __init__(self, *results):
        self.results = list(results)
        self.requests = []

    async def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return self.results.pop(0)


def business(**kwargs):
    return Business(source_id="node/123", name="Negócio Sintético", category="Clínica odontológica", city="São Paulo", state="SP", website_url="https://negocio.example/", **kwargs)


def discovery(**updates):
    return DiscoveryRequest.model_validate({"category": "Clínica odontológica", "city": "São Paulo", "state": "SP", "latitude": -23.55, "longitude": -46.63, **updates})


def service(transport, **kwargs):
    return ProspeccaoService(transport=transport, enabled=True, allowed_domains={"negocio.example"}, quota_guard=permit, **kwargs)


@pytest.mark.parametrize(("category", "expected"), [
    ("CLÍNICA ODONTOLÓGICA", ("amenity", "dentist")),
    ("Salão de Beleza", ("shop", "beauty")),
    ("Agência de Marketing", ("office", "advertising_agency")),
    ("SaaS", ("office", "it")),
])
def test_portuguese_categories_are_explicit_and_accent_insensitive(category, expected):
    assert category_tags(category) == expected


def test_unknown_category_does_not_generate_arbitrary_overpass_syntax():
    with pytest.raises(ProspeccaoError, match="unsupported_category"):
        category_tags('dentista"];out;node["x')


@pytest.mark.parametrize("updates", [{"limit": 26}, {"radius_m": 10001}, {"city": "SP];out;"}, {"latitude": float("nan")}, {"longitude": None}, {"state": "XX"}, {"arbitrary_url": "https://negocio.example"}])
def test_discovery_schema_bounds_volume_and_rejects_extra_input(updates):
    with pytest.raises(ValidationError):
        discovery(**updates)


@pytest.mark.parametrize("url", ["https://name:password@negocio.example/", "https://127.0.0.1/", "https://localhost/", "https://negocio.internal/", "https://negocio.example:8443/", "javascript:alert(1)", "https://nego\ncio.example/", "https://negocio.example\t/", "https://negocio.home.arpa/", "https://negocio.corp/", "https://negocio%2eexample/", "https://negocio.example\\@attacker.example/"])
def test_site_canonicalization_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        public_website(url)


def test_site_canonicalization_minimizes_path_query_and_fragment():
    assert public_website("http://NEGOCIO.example/path?tracking=1#x") == "https://negocio.example/"


@pytest.mark.asyncio
async def test_discovery_normalizes_dedupes_and_preserves_provenance():
    elements = [
        {"type": "node", "id": 1, "tags": {"name": "Empresa A", "website": "http://www.negocio.example/path?x=1"}},
        {"type": "way", "id": 2, "tags": {"name": "Empresa A filial", "website": "https://negocio.example"}},
        {"type": "node", "id": 3, "tags": {"name": "Empresa B", "website": "https://name:password@negocio.example"}},
        {"type": "node", "id": 4, "tags": {"name": "Empresa C", "website": "https://instagram.com/fixture"}},
        {"type": "node", "id": 5, "tags": {"name": "  Empresa B  "}},
    ]
    transport = FakeTransport(FetchResult(json.dumps({"elements": elements}), "application/json"))
    result = await service(transport).discover(discovery(limit=4), "owner/project")
    assert len(result.businesses) == 3
    assert result.businesses[0].website_url == "https://www.negocio.example/"
    assert result.businesses[1].website_url is None
    assert result.businesses[2].website_url is None
    assert result.businesses[0].evidence[0].source_url == "https://www.openstreetmap.org/node/1"
    assert result.attribution.startswith("© OpenStreetMap")
    assert "não comprovam" in result.coverage
    query = transport.requests[0][2]["data"]["data"]
    assert '["amenity"="dentist"]' in query
    assert "São Paulo" not in query
    assert result.expires_at.tzinfo is not None


@pytest.mark.asyncio
async def test_discovery_disabled_and_missing_quota_fail_closed():
    transport = FakeTransport()
    with pytest.raises(ProspeccaoError, match="prospeccao_disabled"):
        await ProspeccaoService(transport=transport, enabled=False, quota_guard=permit).discover(discovery(), "owner")
    with pytest.raises(ProspeccaoError, match="external_quota_unavailable"):
        await ProspeccaoService(transport=transport, enabled=True).discover(discovery(), "owner")
    assert transport.requests == []


@pytest.mark.asyncio
async def test_geocoder_is_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("KOTHAR_PROSPECCAO_GEOCODER", raising=False)
    transport = FakeTransport()
    with pytest.raises(ProspeccaoError, match="geocoder_not_configured"):
        await service(transport).discover(discovery(latitude=None, longitude=None), "owner")
    assert not transport.requests


@pytest.mark.asyncio
async def test_geocoder_cache_is_scoped_by_caller_and_checks_state(monkeypatch):
    monkeypatch.setenv("KOTHAR_PROSPECCAO_GEOCODER", "photon")
    geo = FetchResult(json.dumps({"features": [{"properties": {"name": "São Paulo", "state": "São Paulo", "countrycode": "BR", "osm_value": "city"}, "geometry": {"coordinates": [-46.63, -23.55]}}]}), "application/json")
    empty = FetchResult('{"elements":[]}', "application/json")
    transport = FakeTransport(geo, empty, empty, geo, empty)
    svc = service(transport)
    req = discovery(latitude=None, longitude=None)
    await svc.discover(req, "owner-a")
    await svc.discover(req, "owner-a")
    await svc.discover(req, "owner-b")
    assert sum("photon" in entry[1] for entry in transport.requests) == 2
    wrong_state = json.loads(geo.text)
    wrong_state["features"][0]["properties"]["state"] = "Paraná"
    invalid_transport = FakeTransport(FetchResult(json.dumps(wrong_state), "application/json"))
    with pytest.raises(ProspeccaoError, match="municipality_not_resolved"):
        await service(invalid_transport).discover(req, "owner")


HTML = """<!doctype html><html><head><script src='/wp-content/script.js'></script>
<script src='https://connect.facebook.net/fixture.js'></script>
<script>gtag('fixture'); secret@negocio.example;</script></head>
<body><a href='/trabalhe-conosco'>Equipe</a>
<a href='mailto:contato@negocio.example?subject=teste'>Contato</a>
<p>COMERCIAL@NEGOCIO.EXAMPLE; contato@negocio.example;
ana@negocio.example; contato@terceiro.example; info@gmail.example</p>
</body></html>"""


@pytest.mark.asyncio
async def test_profile_reports_heuristics_and_only_general_published_owned_contacts():
    async def mx(_domain):
        return True
    transport = FakeTransport(FetchResult(HTML, "text/html"))
    result = await service(transport, mx_lookup=mx).profile(ProfileRequest(business=business(), check_mx=True), "owner")
    assert {contact.email for contact in result.contacts} == {"contato@negocio.example", "comercial@negocio.example"}
    assert all(contact.status == "published_unverified" and contact.mx_status == "present" for contact in result.contacts)
    signals = {signal.code: signal for signal in result.signals}
    assert signals["meta_pixel"].confidence == "heuristic"
    assert "não comprova anúncios ativos" in signals["meta_pixel"].limitation
    assert "não prova ausência" in signals["booking_not_observed"].limitation
    assert signals["wordpress"].evidence.method == "html_heuristic"
    assert "wp-content" not in result.model_dump_json()  # HTML bruto não é retido


@pytest.mark.asyncio
async def test_profile_booking_link_and_unconfigured_verifier_remain_honest():
    transport = FakeTransport(FetchResult(HTML + "<a href='https://calendly.com/synthetic'>Agendar</a>", "text/html"))
    result = await service(transport).profile(ProfileRequest(business=business(), verify_contacts=True), "owner")
    assert "booking_link" in {signal.code for signal in result.signals}
    assert "booking_not_observed" not in {signal.code for signal in result.signals}
    assert all(contact.status == "published_unverified" for contact in result.contacts)


@pytest.mark.asyncio
async def test_profile_requires_server_side_domain_authorization():
    transport = FakeTransport()
    svc = ProspeccaoService(transport=transport, allowed_domains=set(), enabled=True, quota_guard=permit)
    with pytest.raises(ProspeccaoError, match="website_not_authorized"):
        await svc.profile(ProfileRequest(business=business()), "owner")
    assert not transport.requests


@pytest.mark.asyncio
async def test_provider_verification_requires_real_structured_evidence():
    class Verifier:
        name = "reoon"
        async def verify(self, _email):
            return "provider_verified", Evidence(source_url="https://emailverifier.reoon.com/", observation="Provedor retornou status positivo no teste sintético", method="provider_response")
    transport = FakeTransport(FetchResult(HTML, "text/html"))
    result = await service(transport, verifier=Verifier()).profile(ProfileRequest(business=business(), verify_contacts=True), "owner")
    assert all(contact.status == "provider_verified" and contact.verification is not None for contact in result.contacts)
    with pytest.raises(ValidationError):
        PublishedContact(email="contato@negocio.example", source_url="https://negocio.example/", status="provider_verified")


@pytest.mark.asyncio
async def test_icp_bant_and_drafts_are_explainable_and_do_not_send():
    profile = await service(FakeTransport(FetchResult(HTML, "text/html"))).profile(ProfileRequest(business=business()), "owner")
    score = score_icp(profile, ICPRequest(target_categories=["Dentista"], target_states=["SP"], desired_signals=["wordpress"]))
    assert score.score == 100
    assert any("+50" in reason for reason in score.reasons)
    assert "Intenção de compra" in score.unknowns
    unknown = qualify_bant(BANTRequest())
    assert not unknown.qualified and unknown.confirmed_count == 0 and len(unknown.next_questions) == 4
    answers = {key: BANTAnswer(status="confirmed", evidence="Declarado na conversa sintética") for key in ["budget", "authority", "need", "timing"]}
    assert qualify_bant(BANTRequest(**answers)).qualified
    with pytest.raises(ValidationError):
        BANTAnswer(status="confirmed")
    draft = draft_outreach(DraftRequest(profile=profile, offer="automação de atendimento", signal_code="meta_pixel", objection="existing_supplier"))
    assert draft.sent is False and draft.status == "draft" and draft.requires_review
    assert "não comprova anúncios ativos" in draft.body
    assert len(draft.followups) == 2 and len(draft.objection_steps) == 5
    assert draft.evidence.source_url == "https://negocio.example/"
    with pytest.raises(ProspeccaoError, match="signal_not_observed"):
        draft_outreach(DraftRequest(profile=profile, offer="automação de atendimento", signal_code="booking_link"))


@pytest.mark.asyncio
async def test_secure_transport_pins_public_ip_and_preserves_tls_hostname():
    seen = []
    async def resolver(_host):
        return ["93.184.216.34"]
    def reply(request):
        seen.append(request)
        return httpx.Response(200, text="<html>fixture</html>", headers={"content-type": "text/html"})
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(reply))
    result = await transport.request("GET", "https://negocio.example/")
    assert result.content_type == "text/html"
    assert seen[0].url.host == "93.184.216.34"
    assert seen[0].headers["host"] == "negocio.example"
    assert seen[0].extensions["sni_hostname"] == "negocio.example"


@pytest.mark.asyncio
@pytest.mark.parametrize("ips", [["127.0.0.1"], ["169.254.169.254"], ["::1"], ["::ffff:127.0.0.1"], ["64:ff9b::7f00:1"], ["2002:7f00:1::"], ["100.64.0.1"], ["93.184.216.34", "10.0.0.1"], []])
async def test_secure_transport_rejects_private_or_mixed_dns_answers(ips):
    async def resolver(_host):
        return ips
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver)
    with pytest.raises(ProspeccaoError, match="destination_not_public"):
        await transport.request("GET", "https://negocio.example/")


@pytest.mark.asyncio
async def test_secure_transport_blocks_redirects_and_oversized_responses():
    async def resolver(_host):
        return ["93.184.216.34"]
    for response, error in [
        (httpx.Response(302, headers={"location": "http://169.254.169.254/"}), "redirect_blocked"),
        (httpx.Response(200, headers={"content-type": "text/html"}, content=b"x" * 1_000_001), "response_too_large"),
    ]:
        transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(lambda _request, response=response: response))
        with pytest.raises(ProspeccaoError, match=error):
            await transport.request("GET", "https://negocio.example/")


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["https://unlisted.example/", "http://negocio.example/", "https://a:b@negocio.example/", "https://negocio.example:8443/"])
async def test_secure_transport_does_not_resolve_unapproved_targets(url):
    async def resolver(_host):
        raise AssertionError("DNS must not be consulted")
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver)
    with pytest.raises(ProspeccaoError, match="destination_not_allowed"):
        await transport.request("GET", url)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["https://nego\ncio.example/", "https://negocio%2eexample/", "https://negocio.example\\@other.example/", "https://negocio.internal/", "https://negocio.home.arpa/", "https://negocio.example:443@127.0.0.1/", "https://2130706433/", "https://0x7f000001/"])
async def test_transport_rejects_ambiguous_and_internal_hosts_even_if_misconfigured(url):
    async def resolver(_host):
        raise AssertionError("DNS must not be consulted")
    transport = SecureTransport({"negocio.example", "negocio.internal", "negocio.home.arpa"}, user_agent="KotharTest/1.0", resolver=resolver)
    with pytest.raises(ProspeccaoError, match="destination_not_allowed"):
        await transport.request("GET", url)


@pytest.mark.asyncio
async def test_transport_does_not_resolve_again_after_pinning_or_follow_redirects():
    resolved, sent = [], []
    async def resolver(host):
        resolved.append(host)
        return ["93.184.216.34"] if len(resolved) == 1 else ["127.0.0.1"]
    def reply(request):
        sent.append(request)
        return httpx.Response(307, headers={"location": "https://negocio.example/internal"})
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(reply))
    with pytest.raises(ProspeccaoError, match="redirect_blocked"):
        await transport.request("GET", "https://negocio.example/")
    assert resolved == ["negocio.example"] and len(sent) == 1
    assert sent[0].url.host == "93.184.216.34"


class SyntheticStream(httpx.AsyncByteStream):
    def __init__(self, chunks, delay=0):
        self.chunks, self.delay = chunks, delay

    async def __aiter__(self):
        for chunk in self.chunks:
            await asyncio.sleep(self.delay)
            yield chunk


@pytest.mark.asyncio
@pytest.mark.parametrize(("headers", "chunks", "expected"), [
    ({"content-type": "text/html", "content-encoding": "gzip"}, [b"unread"], "encoded_response_blocked"),
    ({"content-type": "text/html"}, [b"x" * 600000, b"x" * 600000], "response_too_large"),
    ({"content-type": "application/octet-stream"}, [b"unread"], "unsupported_content_type"),
    ({"content-type": "text/html", "content-length": "not-a-number"}, [b"unread"], "provider_unavailable"),
])
async def test_stream_limits_are_enforced_without_trusting_headers(headers, chunks, expected):
    async def resolver(_host):
        return ["93.184.216.34"]
    def reply(_request):
        return httpx.Response(200, headers=headers, stream=SyntheticStream(chunks))
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(reply))
    with pytest.raises(ProspeccaoError, match=expected):
        await transport.request("GET", "https://negocio.example/")


@pytest.mark.asyncio
async def test_total_deadline_includes_slow_streams(monkeypatch):
    monkeypatch.setattr("backend.servicos.prospeccao.transport.FETCH_TIMEOUT_SECONDS", 0.01)
    async def resolver(_host):
        return ["93.184.216.34"]
    def reply(_request):
        return httpx.Response(200, headers={"content-type": "text/html"}, stream=SyntheticStream([b"x"], delay=1))
    transport = SecureTransport({"negocio.example"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(reply))
    with pytest.raises(ProspeccaoError, match="provider_unavailable"):
        await transport.request("GET", "https://negocio.example/")


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [{"features": {}}, {"features": [None, "invalid", {"properties": []}]}, {"features": [{"properties": {"name": "São Paulo", "state": "São Paulo", "countrycode": "US", "osm_value": "city"}}]}])
async def test_malformed_or_foreign_geocoder_results_do_not_become_businesses(monkeypatch, response):
    monkeypatch.setenv("KOTHAR_PROSPECCAO_GEOCODER", "photon")
    transport = FakeTransport(FetchResult(json.dumps(response), "application/json"))
    with pytest.raises(ProspeccaoError, match="municipality_not_resolved"):
        await service(transport).discover(discovery(latitude=None, longitude=None), "owner")
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_unavailable_quota_fails_closed_before_network_and_never_leaks_backend_error():
    async def unavailable(_caller, _provider):
        raise RuntimeError("private database details")
    transport = FakeTransport()
    svc = ProspeccaoService(transport=transport, enabled=True, quota_guard=unavailable)
    with pytest.raises(ProspeccaoError, match="^external_quota_unavailable$"):
        await svc.discover(discovery(), "owner")
    assert not transport.requests


@pytest.mark.asyncio
async def test_optional_mx_uses_persistent_quota_and_does_not_upgrade_contact_verification():
    providers, mx_queries = [], []
    async def quota(_caller, provider):
        providers.append(provider)
        return provider == "website"
    async def mx(domain):
        mx_queries.append(domain)
        return True
    transport = FakeTransport(FetchResult(HTML, "text/html"))
    svc = ProspeccaoService(transport=transport, enabled=True, allowed_domains={"negocio.example"}, quota_guard=quota, mx_lookup=mx)
    with pytest.raises(ProspeccaoError, match="external_quota_unavailable"):
        await svc.profile(ProfileRequest(business=business(), check_mx=True), "owner")
    assert providers == ["website", "email_verifier"] and not mx_queries


@pytest.mark.asyncio
async def test_refusal_generates_closure_without_solicitation_or_followups():
    profile = await service(FakeTransport(FetchResult(HTML, "text/html"))).profile(ProfileRequest(business=business()), "owner")
    draft = draft_outreach(DraftRequest(profile=profile, offer="automação de atendimento", objection="not_interested"))
    assert draft.followups == [] and draft.cadence_days == []
    assert draft.sent is False and draft.requires_review is True
    assert "não faremos novos acompanhamentos" in draft.body
    assert "prioridade" not in draft.body


@pytest.mark.asyncio
async def test_discover_profile_score_and_draft_through_controlled_secure_transport():
    """Exercita os coletores reais; somente o transporte externo é substituído."""
    requests, reservations = [], []
    async def resolver(_host):
        return ["93.184.216.34"]
    async def quota(caller, provider):
        reservations.append((caller, provider))
        return True
    def reply(request):
        requests.append(request)
        if request.headers["host"] == "overpass-api.de":
            return httpx.Response(200, json={"elements": [{"type": "node", "id": 123, "tags": {"name": "Negócio Sintético", "website": "https://negocio.example/"}}]})
        assert request.headers["host"] == "negocio.example"
        return httpx.Response(200, text=HTML, headers={"content-type": "text/html"})
    transport = SecureTransport({"negocio.example", "overpass-api.de"}, user_agent="KotharTest/1.0", resolver=resolver, http_transport=httpx.MockTransport(reply))
    svc = ProspeccaoService(enabled=True, allowed_domains={"negocio.example"}, quota_guard=quota, transport=transport)
    found = await svc.discover(discovery(), "owner/project")
    profile = await svc.profile(ProfileRequest(business=found.businesses[0]), "owner/project")
    assert score_icp(profile, ICPRequest(target_categories=["Dentista"], target_states=["SP"], desired_signals=["wordpress"])).score == 100
    draft = draft_outreach(DraftRequest(profile=profile, offer="automação de atendimento", signal_code="wordpress"))
    assert not draft.sent and draft.evidence.source_url == "https://negocio.example/"
    assert reservations == [("owner/project", "overpass"), ("owner/project", "website")]
    assert all(request.url.host == "93.184.216.34" for request in requests)
    assert [request.extensions["sni_hostname"] for request in requests] == ["overpass-api.de", "negocio.example"]
    assert {contact.status for contact in profile.contacts} == {"published_unverified"}


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", ["", "owner\n", "owner@outside", None])
async def test_invalid_caller_never_starts_collection(caller):
    transport = FakeTransport()
    with pytest.raises(ProspeccaoError, match="invalid_caller"):
        await service(transport).discover(discovery(), caller)
    assert not transport.requests


@pytest.mark.asyncio
async def test_disabled_service_stops_before_geocoder_configuration_or_cache(monkeypatch):
    monkeypatch.delenv("KOTHAR_PROSPECCAO_GEOCODER", raising=False)
    transport = FakeTransport()
    svc = ProspeccaoService(transport=transport, enabled=False, quota_guard=permit)
    with pytest.raises(ProspeccaoError, match="prospeccao_disabled"):
        await svc.discover(discovery(latitude=None, longitude=None), "owner")
    assert not transport.requests
