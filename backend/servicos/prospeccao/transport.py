"""HTTP mínimo com HTTPS, allowlist exata, pinning de DNS e limites de resposta."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from .schemas import public_hostname

MAX_RESPONSE_BYTES = 1_000_000
FETCH_TIMEOUT_SECONDS = 16
_TRANSLATION_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32",
))


def _is_public_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return address.is_global and not any(address in network for network in _TRANSLATION_NETWORKS)


class ProspeccaoError(ValueError):
    """Código público estável; nunca carrega HTML, e-mail, credenciais ou resposta remota."""


@dataclass(frozen=True)
class FetchResult:
    text: str
    content_type: str


async def public_ips(host: str) -> list[str]:
    try:
        records = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM), timeout=3
        )
        ips = sorted({record[4][0] for record in records})
        if not ips or any(not _is_public_ip(ip) for ip in ips):
            raise ProspeccaoError("destination_not_public")
        return ips
    except (OSError, TimeoutError, ValueError) as exc:
        if isinstance(exc, ProspeccaoError):
            raise
        raise ProspeccaoError("destination_unavailable") from None


class SecureTransport:
    """Resolve uma vez e conecta ao IP validado; TLS continua verificando o host original.

    Os domínios são exclusivamente configuração server-side. A allowlist global
    do web_fetcher permanece intacta.
    """

    def __init__(
        self,
        allowed_domains: set[str],
        *,
        user_agent: str,
        resolver: Callable[[str], Awaitable[list[str]]] = public_ips,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.allowed_domains = frozenset(host.lower().rstrip(".") for host in allowed_domains)
        self.user_agent = user_agent
        self.resolver = resolver
        self.http_transport = http_transport

    async def request(self, method: str, url: str, *, params=None, data=None) -> FetchResult:
        try:
            async with asyncio.timeout(FETCH_TIMEOUT_SECONDS):
                return await self._request(method, url, params=params, data=data)
        except TimeoutError:
            raise ProspeccaoError("provider_unavailable") from None

    async def _request(self, method: str, url: str, *, params=None, data=None) -> FetchResult:
        try:
            if any(ord(c) < 33 or ord(c) == 127 for c in url) or "\\" in url:
                raise ProspeccaoError("destination_not_allowed")
            parsed = urlsplit(url)
            try:
                host = public_hostname(parsed.hostname or "")
            except (ValueError, UnicodeError):
                raise ProspeccaoError("destination_not_allowed") from None
            if (
                parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.port not in {None, 443} or method not in {"GET", "POST"}
                or host not in self.allowed_domains
            ):
                raise ProspeccaoError("destination_not_allowed")
            ips = await self.resolver(host)
            # Validação repetida também para resolvers injetados pelo servidor.
            if not ips or any(not _is_public_ip(ip) for ip in ips):
                raise ProspeccaoError("destination_not_public")
            pinned = httpx.URL(url).copy_with(host=ips[0])
            async with httpx.AsyncClient(  # noqa: SIM117 — client precisa existir antes de stream
                timeout=httpx.Timeout(12, connect=4), follow_redirects=False,
                trust_env=False, transport=self.http_transport,
                headers={"Host": host, "User-Agent": self.user_agent, "Accept-Encoding": "identity"},
            ) as client:
                async with client.stream(
                    method, pinned, params=params, data=data,
                    extensions={"sni_hostname": host},
                ) as response:
                    if response.is_redirect:
                        raise ProspeccaoError("redirect_blocked")
                    if response.status_code != 200:
                        raise ProspeccaoError("provider_unavailable")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if content_type not in {"text/html", "application/xhtml+xml", "application/json", "application/geo+json"}:
                        raise ProspeccaoError("unsupported_content_type")
                    # Não confiar em Accept-Encoding: uma bomba comprimida pode alocar
                    # muita memória no decodificador antes de o limite de chunks agir.
                    if response.headers.get("content-encoding", "identity").lower().strip() not in {"", "identity"}:
                        raise ProspeccaoError("encoded_response_blocked")
                    length = response.headers.get("content-length")
                    if length and int(length) > MAX_RESPONSE_BYTES:
                        raise ProspeccaoError("response_too_large")
                    content = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=16384):
                        content.extend(chunk)
                        if len(content) > MAX_RESPONSE_BYTES:
                            raise ProspeccaoError("response_too_large")
                    return FetchResult(bytes(content).decode("utf-8", errors="replace"), content_type)
        except ProspeccaoError:
            raise
        except (httpx.HTTPError, ValueError, OSError):
            raise ProspeccaoError("provider_unavailable") from None
