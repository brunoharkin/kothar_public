"""
=============================================================
 KOTHAR v4.0 — GraphRAG Client (Neo4j)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Mapeia EXATAMENTE o que está conectado a quê no codebase.
 Deletar uma feature = buscar nó raiz e deletar tudo conectado.
 Sem fantasmas no código.
"""

from typing import Any

from backend.core.database import get_neo4j_session
from backend.core.exceptions import GraphRAGError
from backend.core.logger import get_logger
from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    get_neo4j_circuit,
)

log = get_logger("memory.graph.graphrag")


class GraphRAG:
    """
    Interface para o Mapa de Dependências via Neo4j.

    Tipos de nós:
        File, Route, Table, Component, Skill, Session

    Tipos de relacionamentos:
        IMPORTS, IMPLEMENTS, READS, WRITES, CALLS, USES, MODIFIED, APPLIES_TO
    """

    def __init__(self):
        # Circuit breaker para resiliência do Neo4j
        self._circuit = get_neo4j_circuit()

    # ----------------------------------------------------------
    # Arquivos
    # ----------------------------------------------------------

    async def register_file(
        self,
        path: str,
        file_type: str,
        session_id: str,
        content_hash: str = "",
    ) -> None:
        """Registra ou atualiza um arquivo no grafo."""
        async def _do_register():
            async with get_neo4j_session() as session:
                await session.run(
                    """
                    MERGE (f:File {path: $path})
                    SET f.type = $file_type,
                        f.last_modified = datetime(),
                        f.content_hash = $content_hash
                    WITH f
                    MERGE (s:Session {id: $session_id})
                    MERGE (s)-[:MODIFIED]->(f)
                    """,
                    path=path,
                    file_type=file_type,
                    content_hash=content_hash,
                    session_id=session_id,
                )
            log.debug("Arquivo registrado no grafo", path=path)

        try:
            await self._circuit.call(_do_register)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha ao registrar arquivo: {e}", {"path": path})

    async def register_dependency(
        self, source_path: str, target_path: str, relation: str = "IMPORTS"
    ) -> None:
        """Registra dependência entre dois arquivos."""
        valid_relations = {"IMPORTS", "IMPLEMENTS", "READS", "WRITES", "CALLS", "USES"}
        if relation not in valid_relations:
            raise GraphRAGError(f"Relação inválida: {relation}", {"valid": list(valid_relations)})

        async def _do_register():
            async with get_neo4j_session() as session:
                await session.run(
                    f"""
                    MERGE (a:File {{path: $source}})
                    MERGE (b:File {{path: $target}})
                    MERGE (a)-[:{relation}]->(b)
                    """,
                    source=source_path,
                    target=target_path,
                )
            log.debug("Dependência registrada", source=source_path, target=target_path, rel=relation)

        try:
            await self._circuit.call(_do_register)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha ao registrar dependência: {e}")

    async def get_file_dependencies(self, path: str, depth: int = 2) -> list[dict[str, Any]]:
        """
        Retorna todos os arquivos conectados a um arquivo (até N níveis de profundidade).
        Essencial para deletar features sem fantasmas.
        """
        async def _do_query():
            async with get_neo4j_session() as session:
                result = await session.run(
                    """
                    MATCH (f:File {path: $path})-[r*1..$depth]-(connected)
                    RETURN DISTINCT connected.path AS path,
                           connected.type AS type,
                           labels(connected) AS labels
                    """,
                    path=path,
                    depth=depth,
                )
                records = await result.data()
                return records

        try:
            return await self._circuit.call(_do_query)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha ao buscar dependências: {e}", {"path": path})

    async def get_files_modified_in_session(self, session_id: str) -> list[str]:
        """Lista todos os arquivos modificados em uma sessão."""
        async def _do_query():
            async with get_neo4j_session() as session:
                result = await session.run(
                    """
                    MATCH (s:Session {id: $session_id})-[:MODIFIED]->(f:File)
                    RETURN f.path AS path
                    ORDER BY f.last_modified DESC
                    """,
                    session_id=session_id,
                )
                records = await result.data()
                return [r["path"] for r in records]

        try:
            return await self._circuit.call(_do_query)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha ao buscar arquivos da sessão: {e}", {"session_id": session_id})

    async def get_impact_analysis(self, path: str) -> dict[str, Any]:
        """
        Análise de impacto: o que seria afetado se este arquivo for removido/modificado?
        Retorna todos os dependentes diretos e indiretos.
        """
        async def _do_analysis():
            async with get_neo4j_session() as session:
                # Dependentes (quem depende de mim)
                dependents_result = await session.run(
                    """
                    MATCH (dependent)-[r]->(f:File {path: $path})
                    RETURN dependent.path AS path, type(r) AS relation
                    """,
                    path=path,
                )
                dependents = await dependents_result.data()

                # Dependências (de quem eu dependo)
                deps_result = await session.run(
                    """
                    MATCH (f:File {path: $path})-[r]->(dependency)
                    RETURN dependency.path AS path, type(r) AS relation
                    """,
                    path=path,
                )
                dependencies = await deps_result.data()

            return {
                "file": path,
                "dependents": dependents,      # quem vai quebrar se eu mudar
                "dependencies": dependencies,  # o que eu uso
                "impact_level": self._calculate_impact(dependents),
            }

        try:
            return await self._circuit.call(_do_analysis)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha na análise de impacto: {e}", {"path": path})

    async def register_session(self, session_id: str, agent_name: str) -> None:
        """Registra uma sessão no grafo."""
        async def _do_register():
            async with get_neo4j_session() as session:
                await session.run(
                    """
                    MERGE (s:Session {id: $session_id})
                    SET s.agent_name = $agent_name,
                        s.created_at = datetime()
                    """,
                    session_id=session_id,
                    agent_name=agent_name,
                )

        try:
            await self._circuit.call(_do_register)
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            raise GraphRAGError(f"Falha ao registrar sessão no grafo: {e}")

    async def get_graph_stats(self) -> dict[str, int]:
        """Retorna estatísticas do grafo."""
        async def _do_query():
            async with get_neo4j_session() as session:
                result = await session.run(
                    """
                    MATCH (f:File) WITH count(f) AS files
                    MATCH (s:Session) WITH files, count(s) AS sessions
                    MATCH ()-[r]->() WITH files, sessions, count(r) AS relations
                    RETURN files, sessions, relations
                    """
                )
                record = await result.single()
                return dict(record) if record else {"files": 0, "sessions": 0, "relations": 0}

        try:
            return await self._circuit.call(_do_query)
        except CircuitBreakerOpen:
            # Em stats, retornamos zeros em vez de falhar
            log.warning("Circuit breaker aberto para get_graph_stats, retornando zeros")
            return {"files": 0, "sessions": 0, "relations": 0}
        except Exception as e:
            log.warn("Falha ao obter stats do grafo", error=str(e))
            return {"files": 0, "sessions": 0, "relations": 0}

    @staticmethod
    def _calculate_impact(dependents: list[dict]) -> str:
        count = len(dependents)
        if count == 0:
            return "low"
        elif count <= 3:
            return "medium"
        else:
            return "high"

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Retorna o circuit breaker para métricas."""
        return self._circuit


# Instância singleton
graph_rag = GraphRAG()
