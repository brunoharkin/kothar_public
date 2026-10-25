#!/usr/bin/env python3
"""
KOTHAR — Hook: Session Init (PreInvocation)
Roda ANTES de cada chamada ao modelo.
- Detecta se há handoff ativo e injeta contexto resumido
- Reporta estado do projeto (sensores S1-S5)
- Informa skills carregadas
Saída: JSON com injectSteps para o AGY
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def main():
    payload = {}
    raw = sys.stdin.read().strip()
    if raw:
        try:
            payload = json.loads(raw)
        except:
            pass

    invocation_num = payload.get("invocationNum", 0)

    # Só injeta na PRIMEIRA invocação da sessão
    if invocation_num != 0:
        print(json.dumps({}))
        return

    kothar_dir = Path(
        os.environ.get(
            "CLAUDE_PROJECT_DIR",
            os.environ.get("KOTHAR_PROJECT_DIR", os.getcwd()),
        )
    ).resolve()
    mensagens = []

    # S1 — Projeto atual (fixo — os.getcwd() retorna o diretório do plugin)
    cwd = str(kothar_dir)
    mensagens.append(f"📁 S1 Projeto: {cwd}")

    # S2 — Git
    import subprocess
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
        status = f"branch:{branch}" + (f" | {len(dirty.splitlines())} modificados" if dirty else " | limpo")
        mensagens.append(f"🌿 S2 Git: {status}")
    except:
        mensagens.append("🌿 S2 Git: não disponível")

    # S4 — Handoff ativo?
    cofre_snapshots = [
        Path.home() / "Cofre" / "00_Memoria" / "Snapshots" / "handoff-ativo.md",
        Path.home() / "cofre" / "00_Memoria" / "Snapshots" / "handoff-ativo.md",
    ]
    handoff_encontrado = None
    for p in cofre_snapshots:
        if p.exists():
            handoff_encontrado = p
            break

    if handoff_encontrado:
        mensagens.append(f"🔄 S4 Handoff ATIVO: {handoff_encontrado} — RETOMADA EM CURSO")
    else:
        mensagens.append("✨ S4 Modo: Início fresco — sem handoff pendente")

    # S5 — ChromaDB
    chromadb_dir = kothar_dir / ".chroma-data"
    if chromadb_dir.exists():
        mensagens.append(f"🧠 S5 ChromaDB: disponível em {chromadb_dir}")
    else:
        mensagens.append("🧠 S5 ChromaDB: não inicializado")

    # Total de skills
    skills_dir = kothar_dir / ".agents" / "skills"
    total_skills = len(list(skills_dir.glob("*/SKILL.md"))) if skills_dir.exists() else 0
    mensagens.append(f"⚡ Skills AGY: {total_skills} skills carregadas")

    msg = "\n".join([
        "═" * 50,
        f"[Kothar v4.0] {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        *mensagens,
        "═" * 50,
    ])

    output = {
        "injectSteps": [
            {"ephemeralMessage": msg}
        ]
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
