import asyncio
from mcp.server.mcpserver import MCPServer

from backend.mcp_server.tools import register_tools
from backend.code_intelligence.cbm_tools import (
    mcp_index_repository, mcp_list_projects, mcp_index_status,
    mcp_search_graph, mcp_trace_path, mcp_query_cypher,
    mcp_get_architecture, mcp_search_code, mcp_get_code_snippet,
    mcp_find_dead_code, mcp_detect_circular_deps, mcp_analyze_impact,
    mcp_get_call_graph
)
from backend.core.logger import get_logger

log = get_logger("mcp_server")

# Create the MCP Server instance
mcp = MCPServer("Kothar RAG MCP")

# Register memory tools
import backend.mcp_server.tools as mcp_tools
mcp.tool()(mcp_tools.search_memory)
mcp.tool()(mcp_tools.save_memory)

# Register CBM (Codebase Memory) tools
mcp.tool()(mcp_index_repository)
mcp.tool()(mcp_list_projects)
mcp.tool()(mcp_index_status)
mcp.tool()(mcp_search_graph)
mcp.tool()(mcp_trace_path)
mcp.tool()(mcp_query_cypher)
mcp.tool()(mcp_get_architecture)
mcp.tool()(mcp_search_code)
mcp.tool()(mcp_get_code_snippet)
mcp.tool()(mcp_find_dead_code)
mcp.tool()(mcp_detect_circular_deps)
mcp.tool()(mcp_analyze_impact)
mcp.tool()(mcp_get_call_graph)

# Register Google Workspace (Gmail & Calendar) tools
from backend.mcp_server.google_tools import (
    gmail_resumo_caixa,
    gmail_inspecionar_email,
    gmail_descartar_mensagens,
    gmail_bloquear_descartar_remetente,
    google_agenda_eventos_dia,
    gmail_higienizar_propagandas
)
mcp.tool()(gmail_resumo_caixa)
mcp.tool()(gmail_inspecionar_email)
mcp.tool()(gmail_descartar_mensagens)
mcp.tool()(gmail_bloquear_descartar_remetente)
mcp.tool()(google_agenda_eventos_dia)
mcp.tool()(gmail_higienizar_propagandas)

# Register LinkedIn tools
from backend.mcp_server.linkedin_tools import (
    linkedin_status_conexao,
    linkedin_obter_perfil,
    linkedin_publicar_post,
    linkedin_publicar_post_link,
    linkedin_listar_posts,
    linkedin_excluir_post
)
mcp.tool()(linkedin_status_conexao)
mcp.tool()(linkedin_obter_perfil)
mcp.tool()(linkedin_publicar_post)
mcp.tool()(linkedin_publicar_post_link)
mcp.tool()(linkedin_listar_posts)
mcp.tool()(linkedin_excluir_post)

# Register Meta (Facebook & Instagram) tools
from backend.mcp_server.meta_tools import (
    meta_status_conexao,
    meta_listar_paginas,
    meta_detalhes_pagina_facebook,
    instagram_obter_perfil,
    facebook_publicar_post,
    instagram_publicar_foto,
    meta_listar_historico_posts,
    meta_listar_contas_anuncio
)
mcp.tool()(meta_status_conexao)
mcp.tool()(meta_listar_paginas)
mcp.tool()(meta_detalhes_pagina_facebook)
mcp.tool()(instagram_obter_perfil)
mcp.tool()(facebook_publicar_post)
mcp.tool()(instagram_publicar_foto)
mcp.tool()(meta_listar_historico_posts)
mcp.tool()(meta_listar_contas_anuncio)

def main():
    """
    Inicia o servidor MCP via stdio.
    Este é o padrão usado por IDEs como Cursor, Claude Desktop, etc.
    """
    log.info("Starting Kothar MCP Server via stdio...")
    log.info("Registered tools: Memory (2) + CBM (12) + Google Workspace (6) + LinkedIn (6) + Meta (8)")
    mcp.run()

if __name__ == "__main__":
    main()
