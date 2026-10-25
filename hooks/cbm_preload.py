#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — Codebase Memory Preload
 Executado ANTES de cada tarefa de código
 Busca contexto estrutural via CBM
=============================================================
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================
CBM_CMD = "codebase-memory-mcp"
CACHE_DIR = Path.home() / ".cache" / "codebase-memory-mcp"

# ============================================================
# UTILITÁRIOS
# ============================================================

def log(msg: str):
    print(f"[KOTHAR-CBM] {msg}", file=sys.stderr)

def run_cbm(args: list) -> dict | None:
    """Executa comando CBM via CLI."""
    try:
        result = subprocess.run(
            [CBM_CMD] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        log(f"Erro ao executar CBM: {e}")
        return None

# ============================================================
# FUNÇÕES DE CONSULTA
# ============================================================

def get_architecture_summary(repo_path: str) -> str:
    """Obtém resumo da arquitetura do projeto."""
    result = run_cbm(["cli", "get_architecture", "--repo-path", repo_path])
    if not result:
        return "Arquitetura não disponível"

    languages = result.get("languages", [])
    packages = result.get("packages", [])

    lines = [f"**Arquitetura do Projeto**"]
    lines.append(f"- Linguagens: {', '.join(languages[:5])}")
    lines.append(f"- Pacotes: {len(packages)}")

    return "\n".join(lines)

def search_symbols(query: str, repo_path: str) -> str:
    """Busca símbolos no código."""
    result = run_cbm([
        "cli", "search_graph",
        "--project", os.path.basename(repo_path),
        "--query", query,
        "--limit", "10"
    ])

    if not result or not result.get("nodes"):
        return f"Nenhum símbolo encontrado para: {query}"

    lines = [f"**Símbolos encontrados para '{query}':**"]
    for node in result["nodes"][:10]:
        name = node.get("name", "unknown")
        label = node.get("label", "Node")
        file = node.get("file", "unknown")
        lines.append(f"- [{label}] {name} ({file})")

    return "\n".join(lines)

def trace_dependencies(function_name: str, repo_path: str, depth: int = 2) -> str:
    """Rastreia dependências de uma função."""
    result = run_cbm([
        "cli", "trace_path",
        "--project", os.path.basename(repo_path),
        "--function-name", function_name,
        "--direction", "both",
        "--depth", str(depth)
    ])

    if not result:
        return f"Dependências não encontradas para: {function_name}"

    paths = result.get("paths", [])
    if not paths:
        return f"Nenhuma dependência para: {function_name}"

    lines = [f"**Dependências de '{function_name}':**"]
    for path in paths[:10]:
        nodes = " → ".join([n.get("name", "?") for n in path])
        lines.append(f"  {nodes}")

    return "\n".join(lines)

def detect_code_smells(repo_path: str) -> str:
    """Detecta problemas potenciais no código."""
    issues = []

    # Busca funções muito longas (heurística)
    result = run_cbm([
        "cli", "query_graph",
        "--query", "MATCH (f:Function) WHERE f.end_line - f.start_line > 100 RETURN f"
    ])

    if result and result.get("results"):
        issues.append(f"⚠️ {len(result['results'])} funções muito longas (>100 linhas)")

    return "\n".join(issues) if issues else "✅ Nenhum code smell detectado"

# ============================================================
# PRELOAD PRINCIPAL
# ============================================================

def preload(query: str, repo_path: str = None) -> str:
    """
    Função principal: retorna contexto estrutural do código.
    Use isto antes de modificar código.
    """
    if repo_path is None:
        repo_path = os.getcwd()

    repo_name = os.path.basename(repo_path)

    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("🔍 KOTHAR CODEBASE INTELLIGENCE (CBM)")
    lines.append("=" * 60)

    # 1. Resumo da arquitetura
    lines.append("\n📊 **Arquitetura:**")
    lines.append(get_architecture_summary(repo_path))

    # 2. Busca por termos relevantes na query
    query_keywords = query.lower().split()
    for keyword in query_keywords:
        if len(keyword) > 3:
            symbols = search_symbols(keyword, repo_path)
            if "Nenhum símbolo" not in symbols:
                lines.append(f"\n🔎 **Símbolos para '{keyword}':**")
                lines.append(symbols)
                break

    # 3. Detecção de code smells
    lines.append("\n🔬 **Análise de Código:**")
    lines.append(detect_code_smells(repo_path))

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)

def index_project(repo_path: str = None) -> str:
    """Indexa um projeto no CBM."""
    if repo_path is None:
        repo_path = os.getcwd()

    log(f"Indexando {repo_path}...")

    result = run_cbm([
        "cli", "index_repository",
        "--repo-path", repo_path
    ])

    if result:
        return f"✅ Projeto indexado: {result.get('project_name', 'ok')}"
    return "❌ Falha ao indexar projeto"

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: cbm_preload.py <comando> [args]")
        print("  preload <query>       - Busca contexto para tarefa")
        print("  index [path]         - Indexa projeto")
        print("  arch [path]          - Mostra arquitetura")
        print("  search <termo>       - Busca símbolos")
        print("  trace <função>       - Rastreia dependências")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "preload":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        print(preload(query))

    elif cmd == "index":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        print(index_project(path))

    elif cmd == "arch":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        print(get_architecture_summary(path or os.getcwd()))

    elif cmd == "search":
        term = sys.argv[2] if len(sys.argv) > 2 else ""
        print(search_symbols(term, os.getcwd()))

    elif cmd == "trace":
        func = sys.argv[2] if len(sys.argv) > 2 else ""
        print(trace_dependencies(func, os.getcwd()))

    else:
        print(f"Comando desconhecido: {cmd}")
