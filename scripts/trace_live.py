#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — CLI de Traces no Terminal
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Exibe traces ao vivo no terminal, como um tail -f dos agentes.
 Uso: python3 ~/kothar/scripts/trace_live.py [--session SESSION_ID]
=============================================================
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime

KOTHAR_API = "http://localhost:8080"

# Cores ANSI
COLORS = {
    "tool_call":     "\033[36m",    # cyan
    "tool_result":   "\033[32m",    # green
    "llm_response":  "\033[35m",    # magenta
    "decision":      "\033[33m",    # yellow
    "error":         "\033[31m",    # red
    "agent_start":   "\033[1;34m",  # bold blue
    "agent_complete":"\033[1;32m",  # bold green
    "handoff":       "\033[1;35m",  # bold magenta
    "security_audit":"\033[31m",    # red
    "qa_check":      "\033[33m",    # yellow
    "skill_forged":  "\033[1;36m",  # bold cyan
    "blueprint_created": "\033[34m",# blue
    "default":       "\033[0m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"

EVENT_ICONS = {
    "tool_call":      "🔧",
    "tool_result":    "✅",
    "llm_response":   "🤖",
    "decision":       "💡",
    "agent_start":    "🟢",
    "agent_complete": "🏁",
    "handoff":        "🤝",
    "security_audit": "🔒",
    "qa_check":       "🧪",
    "skill_forged":   "💎",
    "blueprint_created": "📋",
    "lock_check":     "⛔",
    "session_end":    "🔴",
    "user_message":   "👤",
}


def fetch_traces(session_id: str | None, since_id: str | None, limit: int = 20) -> list:
    params = f"limit={limit}"
    if session_id:
        params += f"&session_id={session_id}"

    try:
        req = urllib.request.Request(f"{KOTHAR_API}/api/traces/?{params}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            traces = json.loads(resp.read())
            # A API retorna descrescente (mais recentes 1o). Queremos crescente.
            if since_id:
                new = []
                for t in traces:
                    if t["id"] == since_id:
                        break
                    new.append(t)
                return list(reversed(new))
            return list(reversed(traces))
    except Exception:
        return []


def format_trace(trace: dict) -> str:
    event_type = trace.get("event_type", "unknown")
    agent      = trace.get("agent_name", "?")
    tool       = trace.get("tool_name") or ""
    content    = (trace.get("content") or "")[:120]
    seq        = trace.get("sequence", 0)
    tokens     = trace.get("tokens_used", 0)
    is_error   = trace.get("is_error", False)
    ts         = trace.get("created_at", "")[:19].replace("T", " ")

    color = COLORS.get("error" if is_error else event_type, COLORS["default"])
    icon  = EVENT_ICONS.get(event_type, "•")

    tool_str = f" [{tool}]" if tool else ""
    token_str = f" ({tokens}t)" if tokens else ""
    content_str = f"\n     {content}" if content else ""

    return (
        f"{color}{icon} #{seq:03d} {BOLD}{event_type}{RESET}{color}"
        f"{tool_str} | {agent}{token_str} | {ts}"
        f"{content_str}{RESET}"
    )


def fetch_sessions(limit: int = 10) -> list:
    try:
        req = urllib.request.Request(f"{KOTHAR_API}/api/sessions/?limit={limit}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Kothar Trace Live Viewer")
    parser.add_argument("--session", "-s", help="Session ID para filtrar")
    parser.add_argument("--follow",  "-f", action="store_true", help="Modo live (como tail -f)")
    parser.add_argument("--limit",   "-n", type=int, default=30, help="Número de traces")
    parser.add_argument("--sessions",action="store_true", help="Lista sessões ativas")
    args = parser.parse_args()

    if args.sessions:
        sessions = fetch_sessions()
        print(f"\n{BOLD}Sessões recentes:{RESET}")
        for s in sessions:
            status_icon = "🟢" if s["status"] == "active" else "⚫"
            print(f"  {status_icon} {s['id'][:8]}... | {s['agent_name']:20} | {s['status']:10} | {s.get('task_summary', '')[:50]}")
        return

    print(f"\n{BOLD}🎵 Kothar v4.0 — Trace Live Viewer{RESET}")
    if args.session:
        print(f"   Sessão: {args.session[:8]}...")
    print(f"   API: {KOTHAR_API}\n")

    # Busca inicial
    traces = fetch_traces(args.session, None, args.limit)
    if not traces:
        print("  Nenhum trace encontrado. A API está rodando? (kothar start)")
        return

    last_id = None
    for trace in traces:
        print(format_trace(trace))
        last_id = trace["id"]

    if not args.follow:
        print(f"\n  Total: {len(traces)} trace(s). Use --follow para modo live.\n")
        return

    # Modo live
    print(f"\n  {BOLD}Modo live ativo{RESET} (Ctrl+C para sair)...\n")
    try:
        while True:
            time.sleep(2)
            new = fetch_traces(args.session, last_id, 50)
            for trace in new:
                print(format_trace(trace))
                last_id = trace["id"]
    except KeyboardInterrupt:
        print(f"\n  {BOLD}Encerrado.{RESET}\n")


if __name__ == "__main__":
    main()
