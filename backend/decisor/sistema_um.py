"""
=============================================================
 KOTHAR v4.0 — Sistema Um (System One Controller Local)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Inspirado na arquitetura Jev / Jev-Mem da TypeSafe AI.
 Implementação 100% local via Ollama — zero API paga.

 Princípio:
   Não use LLM pesado para decisões simples.
   Use um modelo leve (7B) com output tipado e schema fixo
   para routing, scoring e gates de segurança.
   O LLM principal só entra quando realmente necessário.

 Fluxo:
   query → Sistema Um (Ollama 7B, 3s timeout)
         → DecisaoRouting tipada
         → banco correto
         → LLM principal recebe contexto focado

 Fallback garantido:
   Se Ollama indisponível ou timeout → keyword matching
   (comportamento atual do rag_preload.py)
=============================================================
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import httpx

from backend.decisor.tipos import (
    Escolha,
    DecisaoRouting,
    FonteMemoria,
    Noul,
    Pontuacao,
)

log = logging.getLogger("kothar.decisor.sistema_um")

# Config
OLLAMA_URL = "http://kothar_ollama:11434"  # dentro do docker
OLLAMA_URL_LOCAL = "http://localhost:11434"  # fallback para dev
MODELO_DECISOR = "llama3.2:1b"  # modelo leve para decisões
TIMEOUT_DECISOR = 3.0  # segundos — se passar, usa fallback

# Palavras-chave para routing por banco (fallback sem Ollama)
_KEYWORDS_NEO4J = {
    "depende", "importa", "usa", "chama", "arquivo", "modulo",
    "funcao", "classe", "dependencia", "grafo", "relacao",
    "impacto", "quebra", "remove", "deleta",
}
_KEYWORDS_POSTGRES = {
    "historico", "log", "trace", "sessao", "auditoria",
    "quando", "aconteceu", "custo", "token", "erro",
}
_KEYWORDS_CHROMA = {
    "como", "o que", "explica", "parecido", "similar",
    "busca", "encontra", "semantico", "contexto",
}


def _routing_por_keywords(query: str) -> DecisaoRouting:
    """Fallback: routing por keywords quando Ollama indisponível."""
    q = query.lower()
    words = set(re.findall(r"\b\w+\b", q))

    neo4j_score = len(words & _KEYWORDS_NEO4J)
    postgres_score = len(words & _KEYWORDS_POSTGRES)
    chroma_score = len(words & _KEYWORDS_CHROMA) + 1  # tiebreaker

    scores = {
        FonteMemoria.NEO4J_GRAFO: neo4j_score,
        FonteMemoria.POSTGRES_AUDITORIA: postgres_score,
        FonteMemoria.CHROMA_SEMANTICO: chroma_score,
    }
    melhor = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confianca = scores[melhor] / total

    return DecisaoRouting(
        fonte=melhor,
        confianca=round(confianca, 2),
        razao="fallback_keywords",
    )


async def _chamar_ollama(prompt: str, ollama_url: str = OLLAMA_URL) -> str | None:
    """Chama Ollama com timeout agressivo. Retorna string JSON ou None."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_DECISOR) as client:
            resp = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": MODELO_DECISOR,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150,
                        "top_p": 0.9,
                    },
                },
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except (httpx.TimeoutException, httpx.ConnectError):
        log.debug("Ollama indisponível em %s — usando fallback", ollama_url)
    except Exception as e:
        log.warning("Erro ao chamar Ollama: %s", e)
    return None


async def routing(query: str) -> DecisaoRouting:
    """
    Decide para qual banco rotear a query.
    
    System One: decisão rápida com Ollama 7B.
    Fallback: keyword matching (zero dependência).
    """
    prompt = f"""Você é um roteador de memória de agente. Decida APENAS qual banco de dados usar.

Query: \"{query}\"

Bancos disponíveis:
- "chroma": busca semântica — para perguntas conceituais, "o que é X", contexto similar
- "neo4j": grafo de dependências — para arquivos, imports, impacto de mudanças, "o que usa Y"
- "postgres": auditoria — para histórico, logs, sessões, erros passados

Responda SOMENTE com JSON válido, sem texto antes ou depois:
{{"banco": "chroma|neo4j|postgres", "confianca": 0.0-1.0, "razao": "string curta"}}"""

    t0 = time.monotonic()
    
    # Tenta Ollama no Docker primeiro, depois localhost
    resposta = await _chamar_ollama(prompt, OLLAMA_URL)
    if resposta is None:
        resposta = await _chamar_ollama(prompt, OLLAMA_URL_LOCAL)
    
    elapsed = time.monotonic() - t0
    
    if resposta:
        try:
            match = re.search(r"\{[^{}]+\}", resposta, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                banco_str = data.get("banco", "chroma")
                confianca = float(data.get("confianca", 0.5))
                razao = data.get("razao", "")
                
                mapa = {
                    "chroma": FonteMemoria.CHROMA_SEMANTICO,
                    "neo4j": FonteMemoria.NEO4J_GRAFO,
                    "postgres": FonteMemoria.POSTGRES_AUDITORIA,
                }
                fonte = mapa.get(banco_str, FonteMemoria.CHROMA_SEMANTICO)
                
                log.debug(
                    "Routing via Ollama: %s (%.2fs, conf=%.2f)",
                    fonte.value, elapsed, confianca
                )
                return DecisaoRouting(
                    fonte=fonte,
                    confianca=round(confianca, 2),
                    razao=razao or "ollama",
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            log.debug("Parse JSON falhou: %s — usando fallback", e)
    
    # Fallback por keywords
    decisao = _routing_por_keywords(query)
    log.debug("Routing via fallback keywords: %s", decisao.fonte.value)
    return decisao


async def pontuar_relevancia(query: str, conteudo: str) -> Pontuacao:
    """
    Score de relevância entre query e conteúdo (0.0 a 1.0).
    Substitui a heurística de re-ranking do rag_v2.py.
    Fallback: TF-IDF simples.
    """
    prompt = f"""Pontue a relevância do conteúdo para a query de 0.0 a 1.0.

Query: \"{query[:200]}\"
Conteúdo: \"{conteudo[:400]}\"

Responda SOMENTE com JSON:
{{"score": 0.0-1.0, "motivo": "string curta"}}"""

    resposta = await _chamar_ollama(prompt)
    if resposta:
        try:
            match = re.search(r"\{[^{}]+\}", resposta, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return Pontuacao(
                    valor=float(data.get("score", 0.5)),
                    confianca=0.85,
                    motivo=data.get("motivo", ""),
                )
        except Exception:
            pass
    
    # Fallback: interseção de tokens normalizados
    q_tokens = set(re.findall(r"\b\w{4,}\b", query.lower()))
    c_tokens = set(re.findall(r"\b\w{4,}\b", conteudo.lower()))
    intersecao = q_tokens & c_tokens
    score = len(intersecao) / max(len(q_tokens), 1)
    return Pontuacao(
        valor=round(min(score, 1.0), 2),
        confianca=0.5,
        motivo="fallback_tfidf",
    )


async def gate_seguranca(conteudo: str) -> Noul:
    """
    Verifica se o conteúdo contém credenciais ou dados sensíveis.
    Substitui o hook agy-credential-scanner para verificações inline.
    Fallback: regex patterns (comportamento atual).
    """
    # Patterns de alta confiança — detectados por regex sempre
    PATTERNS_CRITICOS = [
        r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*[\w\-]{16,}',
        r'(?i)password\s*[=:]\s*[^$\s"]{8,}',
        r'sk-[a-zA-Z0-9]{20,}',
        r'AIzaSy[a-zA-Z0-9\-_]{33}',
        r'(?i)bearer\s+[a-zA-Z0-9\-_.]{20,}',
    ]
    
    for pattern in PATTERNS_CRITICOS:
        if re.search(pattern, conteudo):
            return Noul(
                resultado=True,
                confianca=0.99,
                motivo="regex_critico_detectado",
            )
    
    # Para casos ambíguos, usa Ollama
    amostra = conteudo[:500]
    prompt = f"""Este conteúdo contém credenciais, API keys, senhas ou tokens secretos?

Conteúdo: \"{amostra}\"

Responda SOMENTE com JSON:
{{"tem_credencial": true/false, "confianca": 0.0-1.0, "motivo": "string"}}"""

    resposta = await _chamar_ollama(prompt)
    if resposta:
        try:
            match = re.search(r"\{[^{}]+\}", resposta, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return Noul(
                    resultado=bool(data.get("tem_credencial", False)),
                    confianca=float(data.get("confianca", 0.5)),
                    motivo=data.get("motivo", ""),
                )
        except Exception:
            pass
    
    # Fallback conservador: assume sem credencial se não detectou por regex
    return Noul(resultado=False, confianca=0.7, motivo="fallback_sem_deteccao")


async def classificar_impacto(caminho_arquivo: str, dependentes: list[str]) -> Escolha:
    """
    Classifica o impacto de modificar/deletar um arquivo.
    Retorna: low / medium / high
    """
    n = len(dependentes)
    if n == 0:
        return Escolha(valor="low", confianca=0.95, alternativas=["medium", "high"])
    elif n <= 3:
        return Escolha(valor="medium", confianca=0.90, alternativas=["low", "high"])
    else:
        return Escolha(valor="high", confianca=0.95, alternativas=["medium", "low"])


# Instância singleton para reuso
class SistemaUm:
    """Singleton do Sistema Um para uso via injeção de dependência."""
    
    async def rotear(self, query: str) -> DecisaoRouting:
        return await routing(query)
    
    async def pontuar(self, query: str, conteudo: str) -> Pontuacao:
        return await pontuar_relevancia(query, conteudo)
    
    async def gate(self, conteudo: str) -> Noul:
        return await gate_seguranca(conteudo)
    
    async def impacto(self, caminho: str, dependentes: list[str]) -> Escolha:
        return await classificar_impacto(caminho, dependentes)


sistema_um = SistemaUm()
