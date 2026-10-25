"""
=============================================================
 KOTHAR v6.0 — Query Intelligence
 - Intent detection (tutorial / conceitual / debug / código)
 - Query decomposition (sub-perguntas)
 - BM25 híbrido (keyword + semântico)
 - CoT forçado no prompt
=============================================================
"""
import re
import logging
from typing import List, Tuple, Dict, Optional
from collections import Counter
import math

logger = logging.getLogger("kothar.query_intel")


# === INTENT DETECTION ===
INTENT_PATTERNS = {
    "tutorial": [
        r"\bcomo (fazer|criar|configurar|usar|instalar)\b",
        r"\btutorial\b",
        r"\bpasso a passo\b",
        r"\bcomo faço\b",
        r"\bgostaria de (saber|aprender)\b",
    ],
    "conceitual": [
        r"\bo que (é|são|e significa)\b",
        r"\bexplique\b",
        r"\bcomo funciona\b",
        r"\bqual a diferença\b",
        r"\bdefina\b",
        r"\bconceito\b",
    ],
    "debug": [
        r"\berro\b",
        r"\bdebug\b",
        r"\bnão funciona\b",
        r"\bfalha\b",
        r"\bbug\b",
        r"\bexception\b",
        r"\bnão está rodando\b",
    ],
    "codigo": [
        r"\b(implementar|codar|programar|escrever código)\b",
        r"\bexemplo de código\b",
        r"\bfunção\b",
        r"\bclasse\b",
        r"\bmétodo\b",
    ],
    "planejamento": [
        r"\b(arquitetura|plano|design|estrutura)\b",
        r"\bcrie um (plano|app|sistema|projeto)\b",
        r"\bcomo organizar\b",
        r"\bestratégia\b",
    ],
}


def detect_intent(user_msg: str) -> str:
    """Detecta a intenção do usuário baseado em padrões regex."""
    msg_lower = user_msg.lower()
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        scores[intent] = sum(1 for p in patterns if re.search(p, msg_lower, re.IGNORECASE))
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "geral"


def get_system_prompt_for_intent(intent: str) -> str:
    """Retorna fragmento de system prompt específico para a intenção."""
    prompts = {
        "tutorial": """
## MODO TUTORIAL ATIVO
- Forneça passos numerados (1, 2, 3...)
- Cada passo deve ser uma ação concreta
- Inclua pré-requisitos no início
- Termine com "Próximo passo: [ação]"
""",
        "conceitual": """
## MODO CONCEITUAL ATIVO
- Definição clara em 1-2 frases
- Contexto/histórico (por que existe)
- Exemplo prático simples
- Comparação com alternativas (se relevante)
- Termine com "Próximo passo: [aplicação prática]"
""",
        "debug": """
## MODO DEBUG ATIVO
- Identifique a causa raiz provável
- Liste 2-3 hipóteses
- Para cada hipótese: teste que confirma/refuta
- Sugira fix mais provável primeiro
- Termine com "Próximo passo: [tente X e me diga o resultado]"
""",
        "codigo": """
## MODO CÓDIGO ATIVO
- Código COMPLETO e funcional, não trechos
- Comentários explicativos nas linhas importantes
- Sempre indique o caminho do arquivo (ex: /home/bruno/kothar/backend/...)
- Inclua imports necessários
- Termine com "Próximo passo: quer que eu [execute/teste/otimize]?"
""",
        "planejamento": """
## MODO PLANEJAMENTO ATIVO
- Visão geral primeiro
- Stack recomendada (frontend + backend + banco + deploy)
- Schema de banco (SQL ou NoSQL)
- Lista de APIs/endpoints
- Telas/wireframes
- Critérios de aceitação
- Handoff para Claude Code executar
""",
        "geral": """
## MODO GERAL
- Resposta direta e técnica
- Se a pergunta for simples: 1-3 frases
- Se complexa: estruturada com headers
- Termine com "Próximo passo: ..."
""",
    }
    return prompts.get(intent, prompts["geral"])


# === QUERY DECOMPOSITION ===
def decompose_query(user_msg: str) -> List[str]:
    """
    Decompõe uma pergunta complexa em sub-perguntas atômicas.
    Sem LLM — usa padrões sintáticos.
    """
    msg = user_msg.strip()

    # Se tem " e " ou " também" ou " como também", pode ser multi-pergunta
    if any(sep in msg.lower() for sep in [" e como", " e também", " e qual"]):
        # Split em partes
        parts = re.split(r"\s+e\s+(?=como|qual|o que|onde|quando|por que)", msg, flags=re.IGNORECASE)
        if len(parts) > 1:
            return [p.strip() for p in parts if len(p.strip()) > 10]

    # Se tem " vs " (comparação)
    if " vs " in msg.lower() or " versus " in msg.lower():
        return [msg]  # mantém como uma só (semântica vai pegar)

    return [msg]


# === BM25 SEARCH ===
def tokenize(text: str) -> List[str]:
    """Tokeniza texto em palavras lowercase, removendo pontuação e stopwords."""
    text = text.lower()
    stopwords = {
        "que", "como", "qual", "quais", "diga", "fale",
        "sobre", "para", "com", "por", "oque", "voce", "você", "sabe", "nosso", "meu", "minha",
        "um", "uma", "uns", "umas", "ele", "ela", "eles", "elas", "isso", "isto", "aquilo",
        "aqui", "ali", "lá", "quem", "quando", "onde", "porque", "porquê",
        "faço", "fazer", "criar", "configurar", "usar", "instalar", "aprender"
    }
    tokens = re.findall(r"\b[a-zà-ú]{3,}\b", text)
    return [t for t in tokens if t not in stopwords]


def bm25_score(query_tokens: List[str], doc_tokens: List[str], avg_dl: float, N: int, df: Dict) -> float:
    """Calcula score BM25 simplificado."""
    k1 = 1.5
    b = 0.75

    doc_len = len(doc_tokens)
    if doc_len == 0:
        return 0.0

    tf = Counter(doc_tokens)
    score = 0.0
    for qt in query_tokens:
        if qt not in tf:
            continue
        # IDF
        n_q = df.get(qt, 0)
        idf = math.log(((N - n_q + 0.5) / (n_q + 0.5)) + 1)
        # TF normalized
        tf_norm = (tf[qt] * (k1 + 1)) / (tf[qt] + k1 * (1 - b + b * doc_len / avg_dl))
        score += idf * tf_norm
    return score


def bm25_search(query: str, documents: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
    """
    Faz busca BM25 nos documentos.
    Retorna lista de (index, score) ordenada por score desc.
    """
    query_tokens = tokenize(query)
    if not query_tokens or not documents:
        return []

    # Tokeniza todos os docs
    doc_tokens_list = [tokenize(d) for d in documents]
    N = len(doc_tokens_list)
    avg_dl = sum(len(t) for t in doc_tokens_list) / max(N, 1)

    # Calcula document frequency
    df = {}
    for dt in doc_tokens_list:
        for term in set(dt):
            df[term] = df.get(term, 0) + 1

    # Score cada doc
    scores = []
    for i, dt in enumerate(doc_tokens_list):
        s = bm25_score(query_tokens, dt, avg_dl, N, df)
        if s > 0:
            scores.append((i, s))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def hybrid_search(
    query: str,
    semantic_results: List[Tuple[str, str]],  # [(content, source), ...]
    bm25_weight: float = 0.3,
    semantic_weight: float = 0.7,
) -> List[Tuple[str, str, float]]:
    """
    Combina resultados semânticos (já ranqueados) com BM25.
    semantic_results deve estar ordenado por relevância semântica (melhor primeiro).
    """
    if not semantic_results:
        return []

    # Extrai só os contents
    contents = [c for c, _ in semantic_results]

    # BM25 nos mesmos docs
    bm25_ranked = bm25_search(query, contents, top_k=len(contents))
    bm25_scores = {idx: score for idx, score in bm25_ranked}

    # Normaliza BM25 (0-1)
    max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
    if max_bm25 == 0:
        max_bm25 = 1

    # Combina
    combined = []
    for i, (content, source) in enumerate(semantic_results):
        # Score semântico: posição na lista (1º = 1.0, último = 0)
        sem_score = 1.0 - (i / len(semantic_results))
        # Score BM25
        bm_score = bm25_scores.get(i, 0) / max_bm25
        # Weighted
        final = (sem_score * semantic_weight) + (bm_score * bm25_weight)
        combined.append((content, source, final))

    combined.sort(key=lambda x: x[2], reverse=True)
    return combined


# === CHAIN-OF-THOUGHT PROMPT (compacto) ===
COT_PROMPT = """
## INSTRUÇÕES RIGOROSAS

1. **IDENTIDADE E SAUDAÇÕES**: Se o usuário disser "olá", "bom dia" ou perguntar quem é você, apresente-se orgulhosamente como KOTHAR v3.0, o Maestro do Orquestro Digital da Ugarit Digital. Não diga que não encontrou no Cofre nesses casos.
2. **USE O CONTEXTO RAG FORNECIDO**: para perguntas de projetos, se a resposta está no "CONTEXTO RAG", USE-A como verdade absoluta. NÃO invente.
3. **Se for pergunta técnica e não está no RAG**: diga "Não encontrei essa informação no Cofre" e ofereça pesquisar.
4. **SEM ALUCINAÇÃO**: nunca invente features, números, tecnologias, biometria, ou detalhes não fornecidos.
5. **Resposta CURTA primeiro** (2-4 frases). Detalhes só se pedirem.
6. **Cite a fonte** no formato [arquivo.md] quando usar RAG.
7. **Termine com**: "Próximo passo: [ação concreta]"
"""


# === FEW-SHOT EXAMPLES (curtos e diretos) ===
FEW_SHOT_EXAMPLES = """
## EXEMPLO DE RESPOSTA BASEADA EM RAG

Quando o RAG fornece contexto, SEMPRE siga este padrão:

**User:** "O que é o Chronodesk?"
**RAG forneceu:** definição do Chronodesk
**Kothar responde:** "# ChronoDesk

**Definição:** ChronoDesk é um Dashboard 360° de Gestão Empresarial que centraliza projetos, finanças, agenda e IA em uma única interface.

**Funções principais:**
- Gestão de Projetos
- Controle Financeiro
- Gestão de Agenda
- Assistente IA (Zaya)
- Integração WhatsApp

**Fonte:** [01_VISAO_GERAL.md]

Próximo passo: quer saber mais sobre alguma função específica?"

---

REGRA: Quando o RAG tem a resposta, USE-A como verdade. NUNCA invente detalhes.
Quando o RAG NÃO tem a resposta, diga: "Não encontrei essa informação específica no Cofre."
"""
