"""
=============================================================
 KOTHAR v5.0 — Vault Reader
 Lê sessões passadas do Cofre para encontrar contexto relevante
=============================================================
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from backend.core.logger import get_logger

log = get_logger("memory.vault.reader")

# Cofre padrão
COFRE_DIR = Path(
    os.environ.get("KOTHAR_VAULT_PATH", str(Path.home() / "Cofre"))
)
SESSIONS_DIR = COFRE_DIR / "sessoes"


def find_recent_sessions(days: int = 7) -> list[dict]:
    """
    Encontra sessões recentes no Cofre.
    Retorna lista de sessões com metadados.
    """
    sessions = []
    if not SESSIONS_DIR.exists():
        log.debug("Cofre de sessões não existe ainda")
        return sessions

    cutoff = datetime.now() - timedelta(days=days)

    for session_file in SESSIONS_DIR.glob("*.md"):
        try:
            # Extrair data do nome do arquivo
            # Formato esperado: SESSAO-YYYY-MM-DD-HHMMSS.md
            name = session_file.stem
            if "-" in name:
                parts = name.split("-")
                if len(parts) >= 2:
                    date_str = parts[1] if len(parts) >= 2 else ""
                    try:
                        session_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if session_date >= cutoff:
                            sessions.append({
                                "file": str(session_file),
                                "name": name,
                                "date": date_str,
                                "path": session_file,
                            })
                    except ValueError:
                        pass
        except Exception as e:
            log.debug(f"Erro ao processar {session_file}: {e}")

    return sorted(sessions, key=lambda x: x["date"], reverse=True)


def search_sessions(query: str, days: int = 30) -> list[dict]:
    """
    Busca sessões que contenham a query no título ou conteúdo.
    Retorna sessões similares para contexto.
    """
    query_lower = query.lower()
    results = []

    recent = find_recent_sessions(days)
    for session in recent:
        try:
            content = session["path"].read_text(encoding="utf-8", errors="ignore")
            if query_lower in content.lower() or query_lower in session["name"].lower():
                # Extrair um snippet relevante
                lines = content.split("\n")
                snippet = ""
                for line in lines:
                    if query_lower in line.lower():
                        snippet = line.strip()[:200]
                        break

                results.append({
                    "file": session["file"],
                    "name": session["name"],
                    "date": session["date"],
                    "snippet": snippet,
                    "relevance": "high" if query_lower in session["name"].lower() else "medium",
                })
        except Exception as e:
            log.debug(f"Erro ao buscar em {session['file']}: {e}")

    return results


def get_session_context(task_description: str) -> dict:
    """
    Obtém contexto de sessões passadas para uma nova tarefa.
    Retorna sessões similares e insights relevantes.
    """
    similar_sessions = search_sessions(task_description, days=30)

    return {
        "similar_sessions": similar_sessions[:5],  # Top 5
        "sessions_found": len(similar_sessions),
        "has_context": len(similar_sessions) > 0,
    }


# Instância singleton
vault_reader = type("VaultReader", (), {
    "find_recent_sessions": staticmethod(find_recent_sessions),
    "search_sessions": staticmethod(search_sessions),
    "get_session_context": staticmethod(get_session_context),
})()
