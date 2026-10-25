"""
=============================================================
 KOTHAR v6.0 — Tool Use
 Ferramentas que o LLM pode invocar (function calling nativo do Ollama)
 - read_file(path): lê arquivo do cofre ou do kothar/
 - list_dir(path): lista diretório
 - search_files(pattern): busca por padrão
 - search_code(query, glob): busca código por conteúdo
=============================================================
"""
import os
import re
import json
import logging
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("kothar.tools")

# Diretórios permitidos para o agente acessar
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_DIRS = [
    Path(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre")).expanduser(),
    PROJECT_ROOT,
]

MAX_FILE_SIZE = 200_000  # 200KB max por arquivo
MAX_SEARCH_RESULTS = 30


def _is_path_allowed(path: str) -> bool:
    """Verifica se o path está dentro de algum diretório permitido."""
    try:
        p = Path(path).resolve()
        for allowed in ALLOWED_DIRS:
            if not allowed.exists():
                continue
            try:
                p.relative_to(allowed.resolve())
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False


def tool_read_file(path: str, max_lines: int = 500) -> Dict:
    """
    Lê um arquivo. Retorna {ok, content, lines, size, error}.
    """
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"Path não permitido: {path}", "content": ""}

    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": f"Arquivo não existe: {path}", "content": ""}
        if not p.is_file():
            return {"ok": False, "error": f"Não é arquivo: {path}", "content": ""}

        size = p.stat().st_size
        if size > MAX_FILE_SIZE:
            return {
                "ok": False,
                "error": f"Arquivo muito grande ({size} bytes, max {MAX_FILE_SIZE})",
                "content": "",
            }

        content = p.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        truncated = False
        if len(lines) > max_lines:
            content = "\n".join(lines[:max_lines])
            truncated = True

        return {
            "ok": True,
            "content": content,
            "lines": len(lines),
            "shown_lines": min(len(lines), max_lines),
            "size": size,
            "truncated": truncated,
            "path": str(p),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "content": ""}


def tool_list_dir(path: str, pattern: str = "*") -> Dict:
    """Lista arquivos em um diretório."""
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"Path não permitido", "items": []}

    try:
        p = Path(path)
        if not p.exists():
            return {"ok": False, "error": f"Diretório não existe: {path}", "items": []}
        if not p.is_dir():
            return {"ok": False, "error": f"Não é diretório: {path}", "items": []}

        items = []
        for f in p.rglob(pattern):
            if f.is_file():
                items.append({
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "rel": str(f.relative_to(p)),
                })
                if len(items) >= MAX_SEARCH_RESULTS:
                    break

        return {
            "ok": True,
            "path": str(p),
            "items": items,
            "count": len(items),
            "truncated": len(items) >= MAX_SEARCH_RESULTS,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}


def tool_search_files(
    pattern: str,
    base_dir: str = os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"),
) -> Dict:
    """Busca arquivos por nome (glob pattern)."""
    base = Path(base_dir)
    if not _is_path_allowed(base_dir):
        return {"ok": False, "error": f"Path não permitido: {base_dir}", "matches": []}

    try:
        matches = []
        for f in base.rglob(pattern):
            if f.is_file():
                matches.append({
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                })
                if len(matches) >= MAX_SEARCH_RESULTS:
                    break

        return {
            "ok": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "matches": []}


def tool_search_code(
    query: str,
    glob: str = "*.py",
    base_dir: str = "/home/bruno/tracing",
) -> Dict:
    """Busca em código por conteúdo (case-insensitive substring)."""
    base = Path(base_dir)
    if not _is_path_allowed(base_dir):
        return {"ok": False, "error": f"Path não permitido", "matches": []}

    try:
        q_lower = query.lower()
        matches = []
        for f in base.rglob(glob):
            if not f.is_file() or f.stat().st_size > MAX_FILE_SIZE:
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if q_lower in line.lower():
                        matches.append({
                            "path": str(f),
                            "line": i,
                            "content": line.strip()[:200],
                        })
                        if len(matches) >= MAX_SEARCH_RESULTS:
                            break
                if len(matches) >= MAX_SEARCH_RESULTS:
                    break
            except Exception:
                continue

        return {
            "ok": True,
            "query": query,
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= MAX_SEARCH_RESULTS,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "matches": []}


# === DEFINIÇÃO DAS TOOLS (formato Ollama) ===
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo. Use quando o usuário pedir para ver/abrir/inspecionar um arquivo específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho absoluto do arquivo dentro do Cofre ou projeto Kothar.",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Máximo de linhas a retornar (padrão 500)",
                        "default": 500,
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Lista arquivos de um diretório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho do diretório",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (ex: *.md, *.py). Padrão: *",
                        "default": "*",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Busca arquivos por nome (glob pattern).",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (ex: '*.md', 'kothar*')",
                    },
                    "base_dir": {
                        "type": "string",
                        "description": "Diretório base; por padrão usa KOTHAR_VAULT_PATH.",
                        "default": os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"),
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Busca em código fonte por conteúdo. Retorna matches com path, linha e trecho.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto a buscar (case-insensitive)",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Padrão de extensão (ex: *.py, *.ts). Padrão: *.py",
                        "default": "*.py",
                    },
                    "base_dir": {
                        "type": "string",
                        "description": "Diretório base (padrão: /home/bruno/tracing)",
                        "default": "/home/bruno/tracing",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name: str, args: Dict) -> Dict:
    """Executa uma tool pelo nome."""
    try:
        if name == "read_file":
            return tool_read_file(**args)
        elif name == "list_dir":
            return tool_list_dir(**args)
        elif name == "search_files":
            return tool_search_files(**args)
        elif name == "search_code":
            return tool_search_code(**args)
        else:
            return {"ok": False, "error": f"Tool desconhecida: {name}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === FORMAT TOOL RESULTS TO CONTEXT ===
def format_tool_result(result: Dict, max_chars: int = 4000) -> str:
    """Formata resultado de tool para injetar no contexto."""
    if not result.get("ok"):
        return f"[Tool Error: {result.get('error', 'unknown')}]"

    if "content" in result:
        content = result["content"]
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... ({len(content) - max_chars} chars omitidos)"
        return f"# Conteúdo de {result.get('path', 'arquivo')}:\n```\n{content}\n```"

    if "items" in result:
        items = result["items"][:30]
        text = f"# Arquivos em {result.get('path', 'diretório')}:\n"
        for it in items:
            text += f"- {it.get('rel', it.get('name', '?'))} ({it.get('size', 0)} bytes)\n"
        return text

    if "matches" in result:
        matches = result["matches"][:30]
        text = f"# Resultados de busca ({result.get('count', 0)} matches):\n"
        for m in matches:
            if "line" in m:
                text += f"- {m['path']}:{m['line']} → {m['content']}\n"
            else:
                text += f"- {m['path']} ({m.get('size', 0)} bytes)\n"
        return text

    return json.dumps(result, ensure_ascii=False, indent=2)[:max_chars]
