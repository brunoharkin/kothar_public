#!/usr/bin/env python3
"""Worker local de tarefas duráveis; não envia campanhas nem publica alterações."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.servicos.evolucao.integracao import EvolutionCoordinator  # noqa: E402


async def run_worker(project: str, *, once: bool = False, interval: int = 15):
    owner = os.environ.get("ADMIN_USERNAME", "")
    if not owner:
        raise ValueError("Identidade do operador não configurada no servidor.")
    runtime = EvolutionCoordinator(owner, project)
    while True:
        result = await runtime.run_next()
        # Payloads de tarefas, contatos e prompts não pertencem ao console do worker.
        print(json.dumps({"project": project, "id": result.get("id"),
                          "status": result.get("status")}, ensure_ascii=False), flush=True)
        if once:
            return 0
        await asyncio.sleep(interval)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Executa tarefas operacionais já persistidas no Kothar.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--once", action="store_true", help="Processa no máximo uma tarefa e encerra.")
    parser.add_argument("--interval", type=int, default=15, help="Intervalo de consulta em segundos (1–3600).")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", args.project) or not 1 <= args.interval <= 3600:
        parser.error("Projeto ou intervalo inválido.")
    try:
        return asyncio.run(run_worker(args.project, once=args.once, interval=args.interval))
    except KeyboardInterrupt:
        return 130
    except Exception:
        print(json.dumps({"status": "blocked", "reason": "Dependência ou identidade operacional indisponível."}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
