"""
=============================================================
 KOTHAR v6.0 — RAG Avançado v2
 - Metadata filtering por categoria
 - Self-RAG: checa se resposta é suportada pelos chunks
 - Compressão de contexto (LLMLingua-style extractive)
=============================================================
"""
import re
import logging
import asyncio
import httpx
from typing import List, Tuple, Dict, Optional
from collections import Counter

logger = logging.getLogger("kothar.rag_v2")

OLLAMA_URL = "http://localhost:11434"


def filter_by_category(chunks: List[Tuple[str, str, float, Dict]],
                        query: str,
                        max_per_category: int = 8) -> List[Tuple[str, str, float, Dict]]:
    """
    Filtra chunks por categoria baseado no tipo de query.
    Prioriza categorias mais relevantes.

    chunks: [(content, source, score, metadata), ...]
    """
    q_lower = query.lower()

    # Mapeamento de keywords → categorias
    category_priority = []
    if any(w in q_lower for w in ["agente", "agent", "engineer", "architect", "qa"]):
        category_priority.append("kothar_core")
        category_priority.append("kothar_manuais")
    if any(w in q_lower for w in ["trace", "log", "auditoria", "session"]):
        category_priority.append("sessao")
        category_priority.append("kothar_manuais")
    if any(w in q_lower for w in ["rag", "embedding", "chromadb", "busca", "vetor"]):
        category_priority.append("kothar_manuais")
        category_priority.append("produtos")
    if any(w in q_lower for w in ["neo4j", "graph", "relacionamento"]):
        category_priority.append("kothar_manuais")
    if any(w in q_lower for w in ["plano", "planejamento", "roadmap"]):
        category_priority.append("planejamento")
    if any(w in q_lower for w in ["produto", "cliente", "empresa", "mercado"]):
        category_priority.append("produtos")
        category_priority.append("clientes")
        category_priority.append("empresa")

    if not category_priority:
        return chunks  # sem filtro, retorna tudo

    # Agrupa por categoria
    by_cat: Dict[str, List] = {}
    for chunk in chunks:
        meta = chunk[3] if len(chunk) > 3 else {}
        cat = meta.get("category", "outros")
        by_cat.setdefault(cat, []).append(chunk)

    # Pega top N por categoria prioritária
    filtered = []
    for cat in category_priority:
        if cat in by_cat:
            filtered.extend(by_cat[cat][:max_per_category])

    # Adiciona outras categorias até completar
    for cat, items in by_cat.items():
        if cat not in category_priority:
            filtered.extend(items[:3])  # poucas das outras

    return filtered


def extractive_compress(text: str, target_ratio: float = 0.5) -> str:
    """
    Compressão extractiva: mantém as sentenças mais importantes.
    LLMLingua-style simplificado — sem modelo extra.

    Estratégia: ranqueia sentenças por score de importância e mantém top N.
    """
    if not text or len(text) < 200:
        return text

    # Split em sentenças
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) <= 3:
        return text

    # Score cada sentença
    # Critérios:
    # 1. Tem keywords importantes (números, "sistema", "kothar", "importante")
    # 2. Posição (primeiras e últimas são mais importantes)
    # 3. Tamanho (prefere sentenças médias, descarta muito curtas)
    keywords = ["sistema", "kothar", "importante", "principal", "arquitetura",
                "componente", "função", "módulo", "banco", "trace", "rag",
                "1.", "2.", "3.", "##", "###"]

    scored = []
    for i, sent in enumerate(sentences):
        if len(sent) < 20:
            score = 0
        else:
            # Keyword score
            kw_score = sum(1 for kw in keywords if kw.lower() in sent.lower())
            # Position score
            pos_score = 1.0 if i < 3 or i >= len(sentences) - 3 else 0.3
            # Length score (prefere 50-200 chars)
            if 50 <= len(sent) <= 200:
                len_score = 1.0
            elif len(sent) > 200:
                len_score = 0.7
            else:
                len_score = 0.5

            score = (kw_score * 2) + pos_score + len_score

        scored.append((i, sent, score))

    # Mantém top N% baseado em target_ratio
    target_count = max(2, int(len(sentences) * target_ratio))
    scored.sort(key=lambda x: x[2], reverse=True)
    top_sentences = sorted(scored[:target_count], key=lambda x: x[0])  # reordena por posição

    return " ".join(s for _, s, _ in top_sentences)


async def self_check_answer(
    question: str,
    answer: str,
    rag_chunks: List[str],
    model: str = "kothar-claude",
    timeout: int = 30,
) -> Dict:
    """
    Self-RAG: pergunta ao modelo se a resposta é suportada pelos chunks.
    Retorna {is_supported: bool, confidence: 0-1, issues: [str]}.
    """
    if not rag_chunks:
        return {"is_supported": True, "confidence": 0.5, "issues": ["no_chunks"]}

    # Pega só primeiros 1500 chars de cada chunk (limita contexto)
    chunks_excerpt = "\n---\n".join(c[:1500] for c in rag_chunks[:5])

    prompt = f"""Analise se a resposta abaixo é suportada pelos chunks de contexto fornecidos.

PERGUNTA: {question}

RESPOSTA: {answer[:1500]}

CHUNKS DE CONTEXTO:
{chunks_excerpt}

Responda APENAS em JSON:
{{
  "is_supported": true/false,
  "confidence": 0.0-1.0,
  "issues": ["lista de problemas se houver"],
  "missing_info": "oque falta para melhorar a resposta"
}}"""

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 300, "temperature": 0.1},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "").strip()
                # Tenta parsear JSON da resposta
                import json
                # Procura primeiro { ... }
                match = re.search(r"\{[^{}]*\"is_supported\"[^{}]*\}", text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except Exception:
                        pass
                # Fallback: análise simples
                if "is_supported\": true" in text or "true" in text[:50].lower():
                    return {"is_supported": True, "confidence": 0.7, "issues": [], "raw": text}
                return {"is_supported": False, "confidence": 0.5, "issues": ["parse_failed"], "raw": text}
    except Exception as e:
        logger.warning(f"Self-check falhou: {e}")

    return {"is_supported": True, "confidence": 0.5, "issues": ["check_unavailable"]}


def rerank_with_position_bias(
    chunks: List[Tuple[str, str, float]],
    query: str,
) -> List[Tuple[str, str, float]]:
    """
    Re-ranking adicional com bias de posição.
    Documentos com keywords no início ganham peso extra.
    """
    query_tokens = set(re.findall(r"\b[a-zà-ú]{4,}\b", query.lower()))

    rescored = []
    for content, source, score in chunks:
        bonus = 0.0
        # Bonus se keyword aparece no primeiro 10% do chunk
        head = content[:len(content) // 10].lower()
        for qt in query_tokens:
            if qt in head:
                bonus += 0.05
        rescored.append((content, source, score + bonus))

    rescored.sort(key=lambda x: x[2], reverse=True)
    return rescored
