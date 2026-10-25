"""
=============================================================
 KOTHAR v4.0 — HyDE Search (Busca Hipotética Adaptativa)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 HyDE = Hypothetical Document Embedding.
 Se a busca vetorial falha, o agente gera um documento hipotético
 sobre o que procura, e usa esse documento como query de embedding.
 Isso aumenta drasticamente a qualidade da busca semântica.
"""

import re
from typing import Any

from backend.core.logger import get_logger
from backend.memory.semantic.chroma_client import ChromaMemory
from backend.trace.rag_metrics import record_rag_hit, record_rag_miss
from backend.trace.trace_recorder import trace_recorder

log = get_logger("memory.semantic.hyde")


class HyDESearch:
    """
    Busca Híbrida com HyDE adaptativo.

    Fluxo:
    1. Tenta busca direta com a query original
    2. Se não encontrar (abaixo do threshold), gera variações da query
    3. Se ainda não encontrar, gera documento hipotético (HyDE)
    4. Usa o documento hipotético como nova query
    5. Ajusta threshold progressivamente

    Mandamento #4: máximo 3 tentativas antes de escalar para humano.
    """

    MAX_RETRIES = 3

    def __init__(self, chroma: ChromaMemory, session_id: str | None = None):
        self.chroma = chroma
        self.session_id = session_id

    async def search_skill(
        self,
        original_query: str,
        context: str = "",
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Busca adaptativa de skills com HyDE.
        Retorna lista de skills relevantes ou lista vazia após MAX_RETRIES.
        """
        log.info("Iniciando HyDE search", query=original_query[:80], category=category)

        # Tentativa 1: query original, threshold padrão
        results = await self.chroma.search_skills(
            original_query, category=category, threshold=0.7
        )
        # TRACE: HyDE attempt 1
        await trace_recorder.record(
            session_id=self.session_id or "global",
            event_type="hyde_attempt",
            agent_name="hyde_search",
            content=f"HyDE attempt 1: {len(results)} skills found",
            tool_name="chroma_search",
            tool_input={"query": original_query[:200], "threshold": 0.7},
            tool_output={"found": len(results), "attempt": 1},
            metadata={"attempt": 1, "method": "original_query"},
        )
        if results:
            log.info("HyDE: encontrado na tentativa 1", count=len(results))
            record_rag_hit("skill")
            return results

        # Tentativa 2: variações lexicais + threshold reduzido
        expanded_query = self._expand_query(original_query, context)
        results = await self.chroma.search_skills(
            expanded_query, category=category, threshold=0.55
        )
        # TRACE: HyDE attempt 2
        await trace_recorder.record(
            session_id=self.session_id or "global",
            event_type="hyde_attempt",
            agent_name="hyde_search",
            content=f"HyDE attempt 2: {len(results)} skills found",
            tool_name="chroma_search",
            tool_input={"query": expanded_query[:200], "threshold": 0.55},
            tool_output={"found": len(results), "attempt": 2},
            metadata={"attempt": 2, "method": "expanded_query"},
        )
        if results:
            log.info("HyDE: encontrado na tentativa 2 (query expandida)", count=len(results))
            record_rag_hit("hyde")
            return results

        # Tentativa 3: documento hipotético + threshold mínimo
        hypothetical_doc = self._generate_hypothetical_document(original_query, context)
        results = await self.chroma.search_skills(
            hypothetical_doc, category=category, threshold=0.4
        )
        # TRACE: HyDE attempt 3
        await trace_recorder.record(
            session_id=self.session_id or "global",
            event_type="hyde_attempt",
            agent_name="hyde_search",
            content=f"HyDE attempt 3: {len(results)} skills found",
            tool_name="chroma_search",
            tool_input={"query": hypothetical_doc[:200], "threshold": 0.4},
            tool_output={"found": len(results), "attempt": 3},
            metadata={"attempt": 3, "method": "hypothetical_document"},
        )
        if results:
            log.info("HyDE: encontrado na tentativa 3 (documento hipotético)", count=len(results))
            record_rag_hit("hyde")
            return results

        # Mandamento #4: após 3 tentativas, retorna vazio
        log.warn(
            "HyDE: skill não encontrada após 3 tentativas",
            query=original_query[:80],
        )
        # TRACE: HyDE failed
        await trace_recorder.record(
            session_id=self.session_id or "global",
            event_type="hyde_not_found",
            agent_name="hyde_search",
            content="HyDE: skill não encontrada após 3 tentativas",
            tool_name="chroma_search",
            tool_input={"query": original_query[:200]},
            tool_output={"found": 0, "attempts": 3},
            metadata={"query": original_query[:200], "attempts": 3},
        )
        # RAG miss tracking
        record_rag_miss("skill")
        return []

    async def search_locks(self, action_description: str) -> list[dict[str, Any]]:
        """
        Verifica se uma ação está bloqueada por travas anteriores.
        Chamado pelo Engenheiro antes de executar qualquer passo crítico.
        """
        locks = await self.chroma.search_locks(action_description)
        if locks:
            log.warn(
                "⛔ TRAVA DETECTADA",
                action=action_description[:60],
                locks_count=len(locks),
            )
            record_rag_hit("lock")
        else:
            record_rag_miss("lock")
        return locks

    # ----------------------------------------------------------
    # Geradores de query adaptativa (sem LLM, determinísticos)
    # ----------------------------------------------------------

    def _expand_query(self, query: str, context: str = "") -> str:
        """
        Expande a query com sinônimos e contexto adicional.
        Versão determinística — não depende de LLM.
        """
        synonyms = {
            "criar": "implementar construir desenvolver",
            "botão": "button componente UI interativo",
            "tabela": "table grid listagem dados",
            "rota": "endpoint route API REST",
            "autenticação": "auth login JWT token segurança",
            "banco": "database postgres SQL armazenamento",
            "cache": "redis memória rápida temporário",
        }

        expanded = query
        for term, syns in synonyms.items():
            if term.lower() in query.lower():
                expanded += f" {syns}"

        if context:
            expanded += f"\nContexto: {context[:200]}"

        return expanded.strip()

    def _generate_hypothetical_document(self, query: str, context: str = "") -> str:
        """
        Gera um documento hipotético descrevendo a skill ideal.
        Este texto é usado como embedding — aproxima da skill real.
        """
        return f"""
# Skill: {query}

## Descrição
Skill especializada para: {query}

## Quando usar
Use esta skill quando for necessário {query}.

## Contexto
{context if context else "Desenvolvimento de software com boas práticas."}

## Passos
1. Analisar o requisito
2. Aplicar o padrão correto
3. Validar o resultado

## Tags
{self._extract_keywords(query)}
""".strip()

    def _extract_keywords(self, text: str) -> str:
        """Extrai palavras-chave relevantes do texto."""
        stopwords = {
            "de", "da", "do", "a", "o", "um", "uma", "para", "com",
            "e", "em", "no", "na", "que", "como", "os", "as", "um", "uma",
        }
        words = re.findall(r'\b\w{3,}\b', text.lower())
        keywords = [w for w in words if w not in stopwords]
        return " ".join(list(dict.fromkeys(keywords))[:10])  # dedup + limit
