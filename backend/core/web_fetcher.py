"""
=============================================================
 KOTHAR v6.0 — Web Fetcher (Internet Access)
 Faz scraping simples de URLs via requests + BeautifulSoup
 Fallback se o scrapling MCP não responder
=============================================================
"""
import re
import asyncio
import logging
import httpx
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("kothar.web_fetcher")

# User-Agent para evitar bloqueios
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Kothar/6.0 (Local AI Agent)"
}

# Whitelist de domínios seguros para o agente acessar
SAFE_DOMAINS = [
    "github.com", "raw.githubusercontent.com",
    "stackoverflow.com", "docs.python.org",
    "developer.mozilla.org", "mdn.io",
    "pt.wikipedia.org", "en.wikipedia.org",
    "kothar.local", "kothar_api",
]


def is_safe_url(url: str) -> bool:
    """Verifica se URL é segura para o agente acessar."""
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            return False
        domain = (parsed.hostname or "").lower().rstrip(".")
        return any(domain == allowed or domain.endswith("." + allowed) for allowed in SAFE_DOMAINS)
    except Exception:
        return False


async def fetch_url(url: str, max_chars: int = 8000, timeout: int = 15) -> Dict:
    """
    Faz fetch de uma URL e retorna texto limpo + metadata.
    Tenta primeiro via scrapling MCP, depois fallback httpx + BeautifulSoup.
    """
    if not is_safe_url(url):
        return {"ok": False, "error": f"URL não permitida: {urlparse(url).netloc}", "content": ""}

    # 1) Tenta scrapling MCP (init session + tools/call)
    try:
        scrapling_result = await _fetch_via_scrapling(url, timeout)
        if scrapling_result.get("ok"):
            return scrapling_result
    except Exception as e:
        logger.debug(f"Scrapling MCP falhou para {url}: {e}")

    # 2) Fallback: httpx + BeautifulSoup
    try:
        return await _fetch_via_httpx(url, max_chars, timeout)
    except Exception as e:
        logger.warning(f"httpx falhou para {url}: {e}")
        return {"ok": False, "error": str(e), "content": ""}


async def _fetch_via_scrapling(url: str, timeout: int) -> Dict:
    """Tenta usar o scrapling MCP server."""
    SCRAPLING_URL = "http://kothar_scrapling_mcp:8000/mcp"
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1. Init session
        init_resp = await client.post(
            SCRAPLING_URL,
            json={"jsonrpc": "2.0", "method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "kothar", "version": "6.0"},
            }, "id": 1},
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        )
        session_id = init_resp.headers.get("mcp-session-id") or init_resp.headers.get("x-session-id")
        if not session_id:
            return {"ok": False, "error": "Scrapling MCP sem session_id"}

        # 2. List tools to find the right name
        tools_resp = await client.post(
            SCRAPLING_URL,
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                     "mcp-session-id": session_id},
        )
        # Find first scraping tool
        tool_name = "scrape"  # default
        try:
            import json
            text = tools_resp.text
            # SSE format
            for line in text.split("\n"):
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    tools = data.get("result", {}).get("tools", [])
                    for t in tools:
                        if "scrape" in t.get("name", "").lower() or "fetch" in t.get("name", "").lower():
                            tool_name = t["name"]
                            break
                    break
        except Exception:
            pass

        # 3. Call the tool
        call_resp = await client.post(
            SCRAPLING_URL,
            json={"jsonrpc": "2.0", "method": "tools/call", "params": {
                "name": tool_name,
                "arguments": {"url": url},
            }, "id": 3},
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                     "mcp-session-id": session_id},
        )

        text = call_resp.text
        for line in text.split("\n"):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                content = data.get("result", {}).get("content", [])
                if isinstance(content, list) and content:
                    text_content = "".join(c.get("text", "") for c in content if c.get("type") == "text")
                else:
                    text_content = str(content) if content else ""
                return {"ok": True, "content": text_content[:8000], "method": "scrapling"}

    return {"ok": False, "error": "Scrapling MCP no usable response"}


async def _fetch_via_httpx(url: str, max_chars: int, timeout: int) -> Dict:
    """Fetch via httpx + extração de texto."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=HEADERS) as client:
        resp = await client.get(url)
        if resp.is_redirect:
            return {"ok": False, "error": "Redirecionamento externo bloqueado", "content": ""}
        resp.raise_for_status()
        html = resp.text

    # Tenta BeautifulSoup, fallback para regex
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()

        # Extrai texto
        text = soup.get_text(separator="\n", strip=True)

        # Limpa whitespace excessivo
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
    except ImportError:
        # Fallback regex
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

    return {
        "ok": True,
        "content": text[:max_chars],
        "truncated": len(text) > max_chars,
        "method": "httpx",
        "url": url,
    }


async def web_search(query: str, max_results: int = 5, timeout: int = 15) -> List[Dict]:
    """
    Faz busca web via DuckDuckGo HTML (sem API key).
    Retorna lista de {title, url, snippet}.
    """
    search_url = f"https://html.duckduckgo.com/html/?q={query}"
    results = []
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.get(search_url)
            resp.raise_for_status()
            html = resp.text

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for result in soup.select(".result")[:max_results]:
                title_el = result.select_one(".result__title")
                url_el = result.select_one(".result__url")
                snippet_el = result.select_one(".result__snippet")
                if title_el and url_el:
                    href = url_el.get("href", "")
                    # DDG redirect URL extraction
                    if "uddg=" in href:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(href)
                        params = urllib.parse.parse_qs(parsed.query)
                        href = params.get("uddg", [href])[0]
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": href,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
        except Exception as e:
            logger.debug(f"Falha no parse DDG: {e}")

    except Exception as e:
        logger.warning(f"web_search falhou: {e}")

    return results


def extract_urls(text: str) -> List[str]:
    """Extrai URLs de um texto (para detectar quando o usuário cita uma URL)."""
    url_pattern = r"https?://[^\s\)\]\}\,\"']+"
    urls = re.findall(url_pattern, text)
    # Limpa trailing punctuation
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:!?")
        cleaned.append(url)
    return cleaned
