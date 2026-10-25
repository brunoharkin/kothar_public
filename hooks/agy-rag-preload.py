#!/usr/bin/env python3
"""
KOTHAR — Hook: RAG Preload (PreInvocation)
A cada invocação do modelo, busca skills relevantes e contexto de memória.
Ativa a partir da invocação 2+.

Camada 1 (sempre): keyword matching local nas skills
Camada 2 (se ChromaDB disponível): busca vetorial semântica
Fallback garantido: se tudo falhar, entrega keyword matching simples.
"""
import json
import sys
import os
import re
import urllib.parse
from pathlib import Path

KOTHAR_DIR = Path(
    os.environ.get(
        "CLAUDE_PROJECT_DIR",
        os.environ.get("KOTHAR_PROJECT_DIR", os.getcwd()),
    )
).resolve()
SKILLS_DIR = KOTHAR_DIR / ".agents" / "skills"

# ChromaDB local (dentro do container é 8000, fora é 8000 mapeado)
CHROMA_URL = os.environ.get("CHROMA_URL", "http://localhost:8000").rstrip("/")
CHROMA_COLECOES = (
    "kothar_core",
    "kothar_manuais",
    "kothar_planos",
    "kothar_sessoes",
)

STOPWORDS = {
    'a', 'o', 'e', 'de', 'do', 'da', 'em', 'no', 'na', 'um', 'uma',
    'para', 'com', 'por', 'que', 'se', 'ao', 'os', 'as', 'é', 'são',
    'foi', 'ser', 'ter', 'não', 'mais', 'ou', 'mas', 'como', 'the',
    'and', 'or', 'in', 'to', 'of', 'a', 'an', 'is', 'it', 'for',
    'vamos', 'quero', 'preciso', 'pode', 'fazer', 'isso', 'este',
}


def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', ' ', texto)
    return {w for w in texto.split() if len(w) > 2 and w not in STOPWORDS}


def carregar_skills():
    skills = []
    if not SKILLS_DIR.exists():
        return skills
    for pasta in SKILLS_DIR.iterdir():
        skill_file = pasta / "SKILL.md"
        if not skill_file.exists():
            continue
        conteudo = skill_file.read_text(encoding='utf-8', errors='ignore')
        nome = pasta.name
        desc = ""
        fm_match = re.match(r'^---\n(.*?)\n---', conteudo, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            n = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
            d = re.search(r'^description:\s*>?-?\s*\n?\s*(.+?)(?=\n\w|\Z)', fm, re.DOTALL | re.MULTILINE)
            if n: nome = n.group(1).strip().strip('"\'')
            if d: desc = re.sub(r'\s+', ' ', d.group(1).strip().strip('"\''))
        keywords = normalizar(f"{nome} {desc} {conteudo[:500]}")
        skills.append({"nome": nome, "desc": desc, "keywords": keywords, "pasta": pasta.name})
    return skills


def buscar_por_keywords(query, skills, max_results=4):
    query_kw = normalizar(query)
    if not query_kw:
        return []
    scored = []
    for s in skills:
        inter = query_kw & s["keywords"]
        if inter:
            score = len(inter) / max(len(query_kw), 1)
            if query_kw & normalizar(s["nome"]):
                score *= 1.5
            scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_results]]


def buscar_chroma(query, max_results=3):
    """Tenta busca vetorial no ChromaDB. Retorna lista de documentos ou []."""
    try:
        import chromadb

        endpoint = urllib.parse.urlparse(CHROMA_URL)
        client = chromadb.HttpClient(
            host=endpoint.hostname or "127.0.0.1",
            port=endpoint.port or 8000,
            ssl=endpoint.scheme == "https",
        )
        resultados = []
        for nome in CHROMA_COLECOES:
            colecao = client.get_collection(nome)
            dados = colecao.query(
                query_texts=[query[:200]],
                n_results=max_results,
                include=["documents", "metadatas", "distances"],
            )
            for doc, meta, dist in zip(
                dados.get("documents", [[]])[0],
                dados.get("metadatas", [[]])[0],
                dados.get("distances", [[]])[0],
            ):
                if dist < 1.5:
                    resultados.append({
                        "conteudo": str(doc)[:150],
                        "fonte": (meta or {}).get("source", nome),
                        "score": round(1 - dist / 2, 2),
                    })
        resultados.sort(key=lambda item: item["score"], reverse=True)
        return resultados[:max_results]
    except Exception:
        return []


def extrair_query_transcript(transcript_path):
    """Extrai a última mensagem do usuário do transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        with open(transcript_path, 'r') as f:
            linhas = f.readlines()
        for linha in reversed(linhas[-30:]):
            try:
                d = json.loads(linha)
                if d.get("source") == "USER_EXPLICIT":
                    conteudo = d.get("content", "")
                    if isinstance(conteudo, str):
                        return conteudo[:300]
                    elif isinstance(conteudo, list):
                        textos = [p.get("text", "") for p in conteudo if isinstance(p, dict)]
                        return " ".join(textos)[:300]
            except Exception:
                continue
    except Exception:
        pass
    return ""


def main():
    payload = {}
    raw = sys.stdin.read().strip()
    if raw:
        try:
            payload = json.loads(raw)
        except Exception:
            pass

    invocation_num = payload.get("invocationNum", 0)

    # Só ativa a partir da 2ª invocação
    if invocation_num < 1:
        print(json.dumps({}))
        return

    query = extrair_query_transcript(payload.get("transcriptPath", ""))

    if not query:
        print(json.dumps({}))
        return

    linhas = []

    # Camada 1 — ChromaDB vetorial (se disponível)
    chroma_results = buscar_chroma(query)
    if chroma_results:
        linhas.append("🧠 Memória ChromaDB:")
        for r in chroma_results:
            linhas.append(f"  [{r['score']:.2f}] {r['conteudo']} ({r['fonte']})")

    # Camada 2 — Skills por keyword matching (sempre disponível)
    skills = carregar_skills()
    relevantes = buscar_por_keywords(query, skills)

    if relevantes:
        linhas.append("🔍 Skills relevantes:")
        for s in relevantes:
            linhas.append(f"  • [{s['pasta']}] {s['desc'][:100]}")

    if not linhas:
        print(json.dumps({}))
        return

    linhas.insert(0, "📡 RAG Kothar preload:")
    print(json.dumps({
        "injectSteps": [{"ephemeralMessage": "\n".join(linhas)}]
    }))


if __name__ == "__main__":
    main()
