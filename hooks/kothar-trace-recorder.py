#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — Trace Recorder (Captura COMPLETA)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Captura TUDO: entrada, contexto, thinking, resposta, tools, subagentes
 Funciona 100% offline (gravação em JSONL local)
=============================================================
"""

import json
import os
import sys
import uuid
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# CONFIGURAÇÃO
# ============================================================
TRACE_DIR = Path(os.environ.get("KOTHAR_TRACE_DIR", "/home/bruno/.claude/kothar-trace"))
TRACE_DIR.mkdir(parents=True, exist_ok=True)

SESSION_FILE = TRACE_DIR / "active-session.json"
EVENTS_FILE = TRACE_DIR / "events.jsonl"
CONTEXT_FILE = TRACE_DIR / "context.jsonl"
THINKING_FILE = TRACE_DIR / "thinking.jsonl"

# ============================================================
# UTILITÁRIOS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def safe_filename(s: str) -> str:
    """Remove caracteres inválidos de文件名."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in s)[:64]

def log(msg: str, level: str = "INFO"):
    print(f"[KOTHAR-TRACE {level}] {msg}", file=sys.stderr)

def write_jsonl(filepath: Path, data: dict) -> None:
    """Escreve uma linha JSON de forma thread-safe."""
    try:
        with open(filepath, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        log(f"Erro ao escrever em {filepath}: {e}", "ERROR")

def load_json(filepath: Path) -> dict | None:
    """Carrega JSON de arquivo."""
    try:
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
    except Exception as e:
        log(f"Erro ao ler {filepath}: {e}", "ERROR")
    return None

def save_json(filepath: Path, data: dict) -> None:
    """Salva JSON em arquivo."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        log(f"Erro ao salvar {filepath}: {e}", "ERROR")

# ============================================================
# SESSÃO
# ============================================================

def init_session() -> dict:
    """Inicializa sessão limpa de trace."""
    session_id = f"kothar-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"

    session = {
        "session_id": session_id,
        "started_at": utc_now(),
        "mode": "ISOLATED",
        "status": "ACTIVE",
        "events_count": 0,
        "context_count": 0,
        "thinking_count": 0,
        "tools_count": 0,
        "subagents_count": 0,
        "errors_count": 0,
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "hostname": os.environ.get("HOSTNAME", "localhost"),
        "model": os.environ.get("KOTHAR_MODEL", "claude-opus-5"),
    }

    save_json(SESSION_FILE, session)
    log(f"Sessão iniciada: {session_id}")
    return session

def update_session(updates: dict) -> None:
    """Atualiza contador da sessão."""
    session = load_json(SESSION_FILE) or {}
    session.update(updates)
    save_json(SESSION_FILE, session)

def get_active_session() -> dict | None:
    """Retorna sessão ativa."""
    return load_json(SESSION_FILE)

# ============================================================
# CAPTURA DE EVENTOS
# ============================================================

def capture_event(
    event_type: str,
    content: str = "",
    tool_name: str = "",
    tool_input: dict = None,
    tool_output: dict = None,
    agent_name: str = "claude",
    duration_ms: int = 0,
    tokens: int = 0,
    is_error: bool = False,
    error_msg: str = "",
    metadata: dict = None,
    context_files: list = None,
    thinking: str = "",
) -> None:
    """Captura um evento completo de trace."""

    session = get_active_session()
    if not session:
        session = init_session()

    event = {
        # Identificação
        "event_id": str(uuid.uuid4()),
        "session_id": session["session_id"],
        "event_type": event_type,
        "sequence": session.get("events_count", 0) + 1,
        "timestamp": utc_now(),

        # Conteúdo
        "content": content[:50000] if content else "",  # Limita tamanho
        "thinking": thinking[:50000] if thinking else "",

        # Tool info
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "duration_ms": duration_ms,

        # Contexto
        "context_files": context_files or [],
        "agent_name": agent_name,

        # Métricas
        "tokens": tokens,
        "is_error": is_error,
        "error_message": error_msg[:2000] if error_msg else "",

        # Metadata
        "metadata": metadata or {},
        "pid": os.getpid(),
        "cwd": os.getcwd(),
    }

    write_jsonl(EVENTS_FILE, event)

    # Contadores
    updates = {"events_count": session.get("events_count", 0) + 1}

    if event_type in ("tool_call", "tool_result"):
        updates["tools_count"] = session.get("tools_count", 0) + 1
    elif event_type == "context_read":
        updates["context_count"] = session.get("context_count", 0) + 1
    elif event_type in ("thinking", "reasoning"):
        updates["thinking_count"] = session.get("thinking_count", 0) + 1
    elif event_type in ("subagent_spawn", "subagent_complete"):
        updates["subagents_count"] = session.get("subagents_count", 0) + 1

    if is_error:
        updates["errors_count"] = session.get("errors_count", 0) + 1

    update_session(updates)

    log(f"Captured: {event_type} | {tool_name or event.get('content', '')[:50]}")

def capture_input(user_input: str, metadata: dict = None) -> None:
    """Captura entrada do usuário (prompt)."""
    capture_event(
        event_type="user_input",
        content=user_input,
        metadata={"source": "user_prompt", **(metadata or {})},
    )

def capture_context(files: list[dict]) -> None:
    """Captura contexto lido (arquivos)."""
    for f in files:
        capture_event(
            event_type="context_read",
            content=f.get("content", "")[:10000] if f.get("content") else "",
            metadata={"file_path": f.get("file_path"), "size": f.get("size", 0)},
        )

def capture_thinking(thinking: str, agent_name: str = "claude") -> None:
    """Captura pensamento/reasoning do modelo."""
    capture_event(
        event_type="thinking",
        thinking=thinking,
        agent_name=agent_name,
    )

def capture_response(content: str, agent_name: str = "claude", tokens: int = 0) -> None:
    """Captura resposta do modelo."""
    capture_event(
        event_type="assistant_response",
        content=content,
        agent_name=agent_name,
        tokens=tokens,
    )

def capture_tool_call(
    tool_name: str,
    tool_input: dict,
    agent_name: str = "claude",
) -> None:
    """Captura chamada de ferramenta (PreToolUse)."""
    capture_event(
        event_type="tool_call",
        tool_name=tool_name,
        tool_input=tool_input,
        agent_name=agent_name,
    )

def capture_tool_result(
    tool_name: str,
    tool_input: dict,
    tool_output: dict,
    duration_ms: int = 0,
    is_error: bool = False,
    error_msg: str = "",
    agent_name: str = "claude",
) -> None:
    """Captura resultado de ferramenta (PostToolUse)."""
    capture_event(
        event_type="tool_result",
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        duration_ms=duration_ms,
        is_error=is_error,
        error_msg=error_msg,
        agent_name=agent_name,
    )

def capture_subagent(
    action: str,  # "spawn" ou "complete"
    subagent_name: str,
    task: str = "",
    result: str = "",
    agent_name: str = "claude",
) -> None:
    """Captura eventos de subagentes."""
    event_type = f"subagent_{action}"
    capture_event(
        event_type=event_type,
        content=f"[{subagent_name}] {task or result}",
        agent_name=agent_name,
        metadata={
            "subagent_name": subagent_name,
            "task": task,
            "result": result[:5000] if result else "",
        },
    )

def capture_decision(decision: str, reasoning: str = "", agent_name: str = "claude") -> None:
    """Captura decisão estratégica."""
    capture_event(
        event_type="decision",
        content=f"DECISÃO: {decision}\n\nRAZÃO: {reasoning}",
        agent_name=agent_name,
    )

# ============================================================
# PROCESSAMENTO DE EVENTOS DO HOOK
# ============================================================

def process_hook_event(raw_event: dict) -> None:
    """Processa evento recebido do hook do Claude CLI."""

    hook_type = raw_event.get("hook_event_name", "unknown")
    session_id = raw_event.get("session_id", "")
    tool_name = raw_event.get("tool_name", "")
    tool_input = raw_event.get("tool_input", {})
    tool_result = raw_event.get("tool_response", {})
    error = raw_event.get("error")
    usage = raw_event.get("usage", {})
    duration_ms = raw_event.get("duration_ms", 0)

    tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    is_error = bool(error)

    # Verificar se é entrada do usuário
    if hook_type == "UserPromptSubmit":
        user_message = raw_event.get("message", "")
        if isinstance(user_message, dict):
            content = user_message.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            else:
                content = str(content)
        else:
            content = str(user_message)

        capture_input(content, {"hook_type": hook_type})
        return

    # Tool calls
    if hook_type == "PreToolUse":
        capture_tool_call(tool_name, tool_input)
        return

    if hook_type == "PostToolUse":
        capture_tool_result(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_result,
            duration_ms=duration_ms,
            is_error=is_error,
            error_msg=str(error) if error else "",
        )
        return

    # Subagentes (Agent tool)
    if tool_name == "Agent" and tool_input:
        subagent_type = tool_input.get("subagent_type", "general")
        task = str(tool_input.get("prompt", ""))[:500]
        capture_subagent("spawn", subagent_type, task=task)
        return

    # Thinking/reasoning
    if hook_type == "Content":
        # Resposta do modelo
        content = raw_event.get("content", "")
        if isinstance(content, list):
            # Processar blocos de conteúdo
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "thinking":
                        capture_thinking(block.get("thinking", ""), block.get("speaker", "claude"))
                    elif block.get("type") == "text":
                        capture_response(block.get("text", ""), tokens=tokens)
        else:
            capture_response(str(content), tokens=tokens)
        return

    # Eventos genéricos
    capture_event(
        event_type=hook_type.lower(),
        content=json.dumps(raw_event, default=str)[:1000],
        is_error=is_error,
        error_msg=str(error) if error else "",
    )

# ============================================================
# COMANDOS
# ============================================================

def cmd_show_session() -> None:
    """Mostra sessão ativa."""
    session = get_active_session()
    if session:
        print(json.dumps(session, indent=2))
    else:
        print("Nenhuma sessão ativa.")

def cmd_show_stats() -> None:
    """Mostra estatísticas da sessão."""
    session = get_active_session()
    if not session:
        print("Nenhuma sessão ativa.")
        return

    print(f"\n📊 KOTHAR TRACE - Session: {session['session_id']}")
    print(f"   Started: {session['started_at']}")
    print(f"   Status: {session['status']}")
    print(f"")
    print(f"   📥 Entradas: 1 (this session)")
    print(f"   📄 Contextos: {session.get('context_count', 0)}")
    print(f"   🧠 Pensamentos: {session.get('thinking_count', 0)}")
    print(f"   🔧 Tools: {session.get('tools_count', 0)}")
    print(f"   🤖 Subagentes: {session.get('subagents_count', 0)}")
    print(f"   ❌ Erros: {session.get('errors_count', 0)}")
    print(f"")
    print(f"   📁 Arquivos:")
    print(f"      - Events: {EVENTS_FILE}")
    print(f"      - Session: {SESSION_FILE}")
    print(f"")

def cmd_end_session() -> None:
    """Encerra sessão atual."""
    session = get_active_session()
    if session:
        session["status"] = "completed"
        session["ended_at"] = utc_now()
        save_json(SESSION_FILE, session)
        print(f"Sessão encerrada: {session['session_id']}")
    else:
        print("Nenhuma sessão para encerrar.")

def cmd_list_events(limit: int = 50) -> None:
    """Lista eventos recentes."""
    if not EVENTS_FILE.exists():
        print("Nenhum evento registrado.")
        return

    events = []
    with open(EVENTS_FILE) as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except:
                pass

    events = events[-limit:]
    print(f"\n📋 Últimos {len(events)} eventos:")
    for e in events:
        tool = e.get("tool_name", "")
        content = e.get("content", "")[:60]
        etype = e.get("event_type", "")
        ts = e.get("timestamp", "")[11:19]

        icon = {
            "user_input": "📥",
            "context_read": "📄",
            "thinking": "🧠",
            "tool_call": "⚡",
            "tool_result": "✅",
            "subagent_spawn": "🚀",
            "subagent_complete": "🏁",
            "assistant_response": "💬",
            "decision": "🎯",
        }.get(etype, "📌")

        print(f"   {ts} {icon} [{etype}] {tool or content}")

# ============================================================
# MAIN
# ============================================================

def main():
    # Comandos de controle
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_session()
            cmd_show_stats()
        elif cmd == "session":
            cmd_show_session()
        elif cmd == "stats":
            cmd_show_stats()
        elif cmd == "events":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            cmd_list_events(limit)
        elif cmd == "end":
            cmd_end_session()
        elif cmd == "stop":
            cmd_end_session()
        return

    # Inicializar sessão se não existir
    if not get_active_session():
        init_session()

    # Processar evento do stdin
    raw = sys.stdin.read().strip()
    if raw:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            log(f"JSON inválido: {raw[:100]}", "ERROR")
            event = {"hook_event_name": "unknown", "raw": raw[:200]}
    else:
        event = {"hook_event_name": "session_start"}

    process_hook_event(event)

if __name__ == "__main__":
    main()
