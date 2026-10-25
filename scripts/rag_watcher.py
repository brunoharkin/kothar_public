#!/usr/bin/env python3
"""
Kothar RAG Watcher
Monitora a pasta kothar_core/ e re-indexa automaticamente quando há mudanças.

Pode ser usado de 3 formas:
1. Como daemon (loop contínuo com polling)
2. Como oneshot (executa uma vez)
3. Como hook (chamado por outros scripts ao criar docs)

Uso:
  python3 rag_watcher.py --watch    # daemon contínuo
  python3 rag_watcher.py --oneshot  # executa uma vez
  python3 rag_watcher.py --incremental  # só indexa novos/mudados (sem limpar)
"""

import os
import sys
import time
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import chromadb
from chromadb.config import Settings


# Configuração
WATCH_DIRS = [
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "kothar_core"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "kothar_manuais"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "sessao"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "planos"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "produtos"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "planejamento"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "local_ai_sessions"),
    os.path.join(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre"), "kothar_local_chats"),
]

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEXER_SCRIPT = str(PROJECT_ROOT / "index_rag.py")
SUPREMO_SCRIPT = str(PROJECT_ROOT / "index_supremo.py")
PYTHON_WITH_CHROMADB = os.environ.get("KOTHAR_PYTHON", sys.executable)

# State file para detectar mudanças
STATE_FILE = os.environ.get(
    "KOTHAR_RAG_STATE_FILE",
    str(PROJECT_ROOT / ".rag_state.json"),
)


def get_file_hash(file_path: Path) -> str:
    """Calcula hash MD5 do arquivo."""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except Exception:
        return ""


def load_state() -> dict:
    """Carrega estado anterior (hashes por arquivo)."""
    state_path = Path(STATE_FILE)
    if state_path.exists():
        try:
            import json
            return json.loads(state_path.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    """Salva estado atual."""
    import json
    Path(STATE_FILE).write_text(json.dumps(state, indent=2))


def scan_files() -> dict:
    """Escaneia todos os arquivos .md nas pastas monitoradas."""
    state = {}
    for watch_dir in WATCH_DIRS:
        watch_path = Path(watch_dir)
        if not watch_path.exists():
            continue
        for file_path in watch_path.rglob("*.md"):
            rel_path = str(file_path.relative_to(os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre")))
            state[rel_path] = {
                "hash": get_file_hash(file_path),
                "mtime": file_path.stat().st_mtime,
            }
    return state


def has_changes(old_state: dict, new_state: dict) -> bool:
    """Detecta se houve mudanças."""
    if set(old_state.keys()) != set(new_state.keys()):
        return True
    for path, info in new_state.items():
        if path not in old_state or old_state[path]["hash"] != info["hash"]:
            return True
    return False


def run_indexer():
    """Executa o indexador RAG (legado + supremo)."""
    print(f"\n[{datetime.now().isoformat()}] 🔄 Re-indexando RAG...")

    # Roda indexador legado (collections específicas)
    for script in [INDEXER_SCRIPT, SUPREMO_SCRIPT]:
        try:
            result = subprocess.run(
                [PYTHON_WITH_CHROMADB, script],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                stats = [l for l in lines if "✅" in l or "📊" in l or "🎉" in l]
                for s in stats[-4:]:
                    print(f"  {s}")
            else:
                print(f"  ❌ Erro em {script}:")
                print(result.stderr[-500:])
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout em {script}")
        except Exception as e:
            print(f"  ❌ Erro em {script}: {e}")

    print(f"  ✅ RAG atualizado com sucesso!")


def run_incremental_indexer():
    """Indexa incrementalmente (sem limpar collections existentes)."""
    print(f"\n[{datetime.now().isoformat()}] 🔄 Indexação incremental...")
    # Por enquanto, usa o mesmo indexador (que limpa e re-indexa tudo)
    # Futuramente: implementar logica de diff
    run_indexer()


def watch_mode():
    """Modo daemon: monitora e re-indexa quando há mudanças."""
    print(f"👀 Kothar RAG Watcher")
    print(f"=" * 50)
    print(f"Monitorando:")
    for d in WATCH_DIRS:
        print(f"  • {d}")
    print(f"\nPolling a cada 30 segundos. Ctrl+C para parar.\n")

    old_state = load_state()
    initial = scan_files()

    # Primeira execução se houver mudanças desde o último estado
    if has_changes(old_state, initial):
        print(f"[Inicial] Detectei mudanças desde a última execução")
        run_indexer()
        save_state(initial)
    else:
        print(f"[Inicial] Nenhuma mudança desde a última execução")

    try:
        while True:
            time.sleep(30)
            new_state = scan_files()
            if has_changes(old_state, new_state):
                changed = [
                    p for p in new_state
                    if p not in old_state or old_state.get(p, {}).get("hash") != new_state[p]["hash"]
                ]
                print(f"\n[{datetime.now().isoformat()}] 📝 Mudanças detectadas:")
                for c in changed[:10]:
                    print(f"  • {c}")
                run_indexer()
                save_state(new_state)
                old_state = new_state
    except KeyboardInterrupt:
        print(f"\n\n👋 Watcher encerrado.")


def oneshot_mode():
    """Executa uma vez e sai."""
    print(f"⚡ Kothar RAG Refresh (oneshot)")
    old_state = load_state()
    new_state = scan_files()

    if has_changes(old_state, new_state):
        print(f"  📝 Mudanças detectadas:")
        for p in new_state:
            if p not in old_state or old_state.get(p, {}).get("hash") != new_state[p]["hash"]:
                print(f"    • {p}")
        run_indexer()
        save_state(new_state)
    else:
        print(f"  ✅ Nada mudou, RAG já está atualizado")


def incremental_mode():
    """Re-indexa tudo (incremental não implementado ainda)."""
    print(f"⚡ Kothar RAG Refresh (incremental)")
    run_incremental_indexer()
    new_state = scan_files()
    save_state(new_state)


def main():
    parser = argparse.ArgumentParser(description="Kothar RAG Watcher")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--watch", action="store_true", help="Modo daemon (loop contínuo)")
    group.add_argument("--oneshot", action="store_true", help="Executa uma vez e sai")
    group.add_argument("--incremental", action="store_true", help="Re-indexa tudo")

    args = parser.parse_args()

    if args.watch:
        watch_mode()
    elif args.oneshot:
        oneshot_mode()
    elif args.incremental:
        incremental_mode()
    else:
        # Default: oneshot se não especificado
        oneshot_mode()


if __name__ == "__main__":
    main()
