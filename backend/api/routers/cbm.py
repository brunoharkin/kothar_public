"""
=============================================================
 KOTHAR v5.0 — CBM Router
 API Routes para Codebase Memory MCP
=============================================================
"""

import json
import os
from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.core.logger import get_logger

log = get_logger("api.cbm")
router = APIRouter(prefix="/cbm", tags=["codebase-memory"])

# Diretório de cache do CBM
CBM_CACHE_DIR = "/home/bruno/.cache/codebase-memory-mcp"

def get_projects() -> list:
    """Lista projetos do cache."""
    if not os.path.exists(CBM_CACHE_DIR):
        return []
    projects = []
    for f in os.listdir(CBM_CACHE_DIR):
        if f.endswith('.db') and f not in ['_config.db', 'config.db']:
            name = f.replace('.db', '')
            projects.append({"name": name, "root_path": f"/projects/{name}"})
    return projects

def read_layout_from_db(project: str) -> Optional[dict]:
    """Lê o layout do projeto diretamente do arquivo JSON."""
    layout_path = os.path.join(CBM_CACHE_DIR, f"{project}.json")
    if os.path.exists(layout_path):
        with open(layout_path) as f:
            return json.load(f)
    return None

# ============================================================
# ROUTES
# ============================================================

@router.get("/projects")
async def list_projects():
    """Lista todos os projetos indexados."""
    projects = get_projects()
    return {"projects": projects, "total": len(projects)}


@router.get("/architecture/{project}")
async def get_architecture(project: str):
    """Obtém overview da arquitetura."""
    projects = get_projects()
    if not any(p["name"] == project for p in projects):
        raise HTTPException(status_code=404, detail=f"Projeto '{project}' não encontrado")

    # Tenta ler o layout do daemon ou do cache
    layout = read_layout_from_db(project)

    # Se não encontrou, retorna info básica
    if not layout:
        return {
            "project": project,
            "total_nodes": 0,
            "total_edges": 0,
            "node_labels": {},
            "note": "Layout não disponível. Inicie o daemon com: codebase-memory-mcp daemon start"
        }

    nodes = layout.get("nodes", [])
    edges = layout.get("edges", [])
    labels = {}
    for node in nodes:
        label = node.get("label", "Unknown")
        labels[label] = labels.get(label, 0) + 1

    return {
        "project": project,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_labels": labels,
        "sample_nodes": nodes[:100]
    }


@router.get("/search/{project}")
async def search_graph(
    project: str,
    query: str = "",
    label: Optional[str] = None,
    limit: int = 100
):
    """Busca símbolos no grafo."""
    projects = get_projects()
    if not any(p["name"] == project for p in projects):
        return {"nodes": [], "total": 0, "query": query, "label": label, "error": "Projeto não encontrado"}

    layout = read_layout_from_db(project)

    if not layout:
        # Retorna busca vazia se não houver layout
        return {"nodes": [], "total": 0, "query": query, "label": label}

    nodes = []
    for item in layout.get("nodes", []):
        name = item.get("name", "").lower()
        q = query.lower() if query else ""
        l = item.get("label", "")

        # Filtra por query e label
        if q and q not in name:
            continue
        if label and l != label:
            continue

        nodes.append({
            "id": item.get("id"),
            "name": item.get("name", ""),
            "label": item.get("label", "Node"),
            "file": item.get("file_path", ""),
            "line": item.get("start_line", 0),
            "qn": item.get("qualified_name", ""),
            "rank": 0
        })

    return {"nodes": nodes[:limit], "total": len(nodes), "query": query, "label": label}


@router.get("/trace/{project}/{function_name}")
async def trace_path(
    project: str,
    function_name: str,
    direction: str = "both",
    depth: int = 3
):
    """Traça caminho de dependências."""
    layout = read_layout_from_db(project)

    if not layout:
        return {"callees": [], "callers": [], "error": "Layout não disponível"}

    nodes = {n.get("id"): n for n in layout.get("nodes", [])}
    edges = layout.get("edges", [])

    # Encontra o nó pelo nome
    target = None
    for node in nodes.values():
        if function_name in node.get("qualified_name", ""):
            target = node
            break

    if not target:
        return {"callees": [], "callers": [], "error": "Símbolo não encontrado"}

    target_id = target.get("id")
    callees = []
    callers = []

    # Encontra arestas
    for edge in edges:
        if edge.get("from") == target_id:
            callees.append(nodes.get(edge.get("to"), {}).get("name", ""))
        if edge.get("to") == target_id:
            callers.append(nodes.get(edge.get("from"), {}).get("name", ""))

    return {
        "callees": callees[:20],
        "callers": callers[:20],
        "target": target.get("name", "")
    }


@router.get("/code/{project}/{qualified_name:path}")
async def get_code_snippet(project: str, qualified_name: str):
    """Obtém snippet de código."""
    return {"code": f"// Código de {qualified_name}\n// Implementação não disponível via API", "error": None}


@router.get("/schema/{project}")
async def get_schema(project: str):
    """Obtém schema do grafo."""
    layout = read_layout_from_db(project)
    if layout:
        nodes = layout.get("nodes", [])
        labels = {}
        for node in nodes:
            label = node.get("label", "Unknown")
            labels[label] = labels.get(label, 0) + 1
        return {"labels": labels}
    return {"labels": {}}


@router.get("/health")
async def health_check():
    """Verifica status do CBM."""
    projects = get_projects()
    return {"status": "ok", "projects_count": len(projects), "cache_dir": CBM_CACHE_DIR}
