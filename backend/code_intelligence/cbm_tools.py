"""
=============================================================
 KOTHAR v5.0 — CBM MCP Tools
 Ferramentas MCP para Codebase Memory
=============================================================
"""

import os
from typing import Optional, List
from pathlib import Path

from backend.code_intelligence import CBMClient, QueryEngine
from backend.mcp_server.trace_interceptor import trace_mcp_event, get_or_create_session

# Instâncias globais
session_id = get_or_create_session()
_cbm_client = None
_query_engine = None

def get_cbm() -> CBMClient:
    global _cbm_client
    if _cbm_client is None:
        _cbm_client = CBMClient()
    return _cbm_client

def get_engine() -> QueryEngine:
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine(get_cbm())
    return _query_engine

def _get_project_name(repo_path: str = None) -> str:
    """Obtém nome do projeto de forma inteligente."""
    if repo_path is None:
        repo_path = os.getcwd()
    return Path(repo_path).name

# ============================================================
# MCP TOOLS - INDEXING
# ============================================================

async def mcp_index_repository(repo_path: str, project_name: str = None) -> str:
    """Indexa um repositório no grafo de código."""
    try:
        if project_name is None:
            project_name = _get_project_name(repo_path)

        client = get_cbm()
        result = client.index_repository(repo_path, project_name)

        trace_mcp_event(
            session_id=session_id,
            tool_name="CBM:index_repository",
            input_data={"repo_path": repo_path, "project_name": project_name},
            output_data={"result": result}
        )

        if result:
            return f"✅ Projeto '{project_name}' indexado com sucesso"
        return "❌ Falha ao indexar projeto"

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_list_projects() -> str:
    """Lista todos os projetos indexados."""
    try:
        client = get_cbm()
        projects = client.list_projects()

        if not projects:
            return "Nenhum projeto indexado"

        lines = ["**Projetos Indexados:**"]
        for p in projects:
            lines.append(f"  • {p}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_index_status(project_name: str = None) -> str:
    """Mostra status de indexação de um projeto."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        status = client.index_status(project_name)

        if not status:
            return f"❌ Projeto '{project_name}' não encontrado"

        lines = [f"**Status: {project_name}**"]
        for key, value in status.items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

# ============================================================
# MCP TOOLS - QUERYING
# ============================================================

async def mcp_search_graph(
    query: str,
    label: str = None,
    project_name: str = None,
    limit: int = 50
) -> str:
    """Busca símbolos no grafo de código."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        result = client.search_graph(project_name, query, label, limit)

        if not result or not result.get("nodes"):
            return f"Nenhum resultado para: {query}"

        lines = [f"**Resultados para '{query}':**"]
        for node in result["nodes"][:20]:
            lines.append(f"  [{node.get('label', '?')}] {node.get('name', '?')} — {node.get('file', '?')}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_trace_path(
    function_name: str,
    direction: str = "both",
    depth: int = 3,
    project_name: str = None
) -> str:
    """Traça caminho de dependências de uma função."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        result = client.trace_path(project_name, function_name, direction, depth)

        if not result or not result.get("paths"):
            return f"Nenhuma dependência encontrada para: {function_name}"

        lines = [f"**Dependências de '{function_name}' ({direction}):**"]
        for path in result["paths"][:15]:
            nodes = " → ".join([n.get("name", "?") for n in path])
            lines.append(f"  {nodes}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_query_cypher(
    cypher_query: str,
    project_name: str = None
) -> str:
    """Executa query Cypher no grafo."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        result = client.query_graph(project_name, cypher_query)

        if not result:
            return "Query não retornou resultados"

        lines = [f"**Query Cypher Results:**"]
        if "results" in result:
            for r in result["results"][:20]:
                lines.append(f"  {r}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_get_architecture(project_name: str = None) -> str:
    """Obtém overview da arquitetura."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        result = client.get_architecture(project_name)

        if not result:
            return f"❌ Projeto '{project_name}' não encontrado"

        lines = [f"**Arquitetura: {project_name}**"]

        if "languages" in result:
            lines.append(f"\n**Linguagens:** {', '.join(result['languages'])}")

        if "packages" in result:
            lines.append(f"**Pacotes:** {len(result['packages'])}")
            for pkg in result["packages"][:5]:
                lines.append(f"  • {pkg}")

        if "file_count" in result:
            lines.append(f"**Arquivos:** {result['file_count']}")

        if "loc" in result:
            lines.append(f"**Linhas de código:** {result['loc']:,}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_search_code(
    pattern: str,
    file_pattern: str = None,
    project_name: str = None,
    limit: int = 50
) -> str:
    """Busca texto em código indexado."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        result = client.search_code(project_name, pattern, file_pattern, limit)

        if not result or not result.get("matches"):
            return f"Nenhum código encontrado para: {pattern}"

        lines = [f"**Código encontrado para '{pattern}':**"]
        for m in result["matches"][:20]:
            lines.append(f"  {m.get('file', '?')}:{m.get('line', '?')}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_get_code_snippet(
    qualified_name: str,
    project_name: str = None,
    max_lines: int = 50
) -> str:
    """Obtém snippet de código por qualified name."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        code = client.get_code_snippet(project_name, qualified_name)

        if not code:
            return f"Símbolo não encontrado: {qualified_name}"

        # Limita linhas
        lines = code.split("\n")[:max_lines]
        if len(code.split("\n")) > max_lines:
            lines.append("...")

        return f"**{qualified_name}:**\n```\n" + "\n".join(lines) + "\n```"

    except Exception as e:
        return f"❌ Erro: {str(e)}"

# ============================================================
# MCP TOOLS - ANALYSIS
# ============================================================

async def mcp_find_dead_code(project_name: str = None) -> str:
    """Encontra código morto (funções nunca chamadas)."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        dead = client.find_dead_code(project_name)

        if not dead:
            return "✅ Nenhum código morto detectado"

        lines = [f"⚠️ **{len(dead)} funções nunca chamadas:**"]
        for fn in dead[:30]:
            lines.append(f"  • {fn.get('name', '?')} — {fn.get('file', '?')}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_detect_circular_deps(project_name: str = None) -> str:
    """Detecta dependências circulares."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        circular = client.find_circular_deps(project_name)

        if not circular:
            return "✅ Nenhuma dependência circular"

        lines = [f"🔄 **{len(circular)} dependências circulares:**"]
        for fn in circular[:20]:
            lines.append(f"  • {fn}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_analyze_impact(
    changed_file: str,
    project_name: str = None
) -> str:
    """Analisa impacto de mudança em arquivo."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        client = get_cbm()
        impact = client.analyze_impact(project_name, changed_file)

        lines = [f"**Impacto de mudança em '{changed_file}':**"]
        lines.append(f"Símbolos afetados: {impact.get('dependency_count', 0)}")

        symbols = impact.get("affected_symbols", [])
        if symbols:
            lines.append("\n**Símbolos afetados:**")
            for s in symbols[:20]:
                lines.append(f"  • {s}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"

async def mcp_get_call_graph(
    function_name: str,
    project_name: str = None
) -> str:
    """Obtém grafo de chamadas completo."""
    try:
        if project_name is None:
            project_name = _get_project_name()

        engine = get_engine()
        graph = engine.get_full_call_graph(project_name, function_name)

        lines = [f"**Call Graph: {function_name}**"]

        if graph.get("upstream"):
            lines.append("\n**Chamadores (entrada):**")
            for path in graph["upstream"][:10]:
                nodes = " → ".join([n.get("name", "?") for n in path])
                lines.append(f"  {nodes}")

        if graph.get("downstream"):
            lines.append("\n**Chamados (saída):**")
            for path in graph["downstream"][:10]:
                nodes = " → ".join([n.get("name", "?") for n in path])
                lines.append(f"  {nodes}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Erro: {str(e)}"
