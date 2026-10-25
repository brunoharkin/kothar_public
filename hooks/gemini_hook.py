#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v6.0 — Hook DEFINITIVO do Gemini CLI (ANTI-FANTASMA)
 Engenheiro Kothar | Ugarit Digital
=============================================================

 REGRAS:
 1. Sessão vinculada ao GEMINI_SESSION_ID
 2. Sessões ISOLADAS por agente (claude_hook e gemini_hook NUNCA compartilham)
 3. Lock para evitar duplicação
 4. Match EXATO por session_id
=============================================================
"""

import json
import os
import sys
import fcntl
import urllib.request
import hashlib
from datetime import datetime, timezone

KOTHAR_API = os.environ.get("KOTHAR_API_URL", "http://localhost:8080")
TIMEOUT = 5
DEBUG = os.environ.get("KOTHAR_DEBUG", "0") == "1"

SESSION_DIR = "/tmp/kothar_sessions_gemini"
LOCK_DIR = "/tmp/kothar_locks_gemini"

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOCK_DIR, exist_ok=True)


def log_debug(msg: str):
    if DEBUG:
        print(f"[KOTHAR GEMINI DEBUG] {msg}", file=sys.stderr)


def log_error(msg: str):
    print(f"[KOTHAR GEMINI ERROR] {msg}", file=sys.stderr)


def post_json(endpoint: str, data: dict) -> dict | None:
    try:
        body = json.dumps(data, default=str).encode()
        req = urllib.request.Request(
            f"{KOTHAR_API}{endpoint}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log_error(f"Erro ao enviar para {endpoint}: {e}")
        return None


def get_json(endpoint: str) -> dict | None:
    try:
        req = urllib.request.Request(
            f"{KOTHAR_API}{endpoint}",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log_error(f"Erro ao buscar {endpoint}: {e}")
        return None


def get_session_key(gemini_sid: str) -> str:
    if gemini_sid and not gemini_sid.startswith("gemini-"):
        return hashlib.md5(f"gemini-{gemini_sid}".encode()).hexdigest()[:16]
    return hashlib.md5(f"gemini-{gemini_sid}-{os.getpid()}".encode()).hexdigest()[:16]


def get_session_file(gemini_sid: str) -> str:
    return f"{SESSION_DIR}/kothar_{get_session_key(gemini_sid)}.json"


def get_lock_file(gemini_sid: str) -> str:
    return f"{LOCK_DIR}/kothar_{get_session_key(gemini_sid)}.lock"


def load_session(gemini_sid: str) -> dict | None:
    session_file = get_session_file(gemini_sid)
    try:
        if os.path.exists(session_file):
            with open(session_file) as f:
                return json.load(f)
    except Exception as e:
        log_error(f"Erro ao ler sessão: {e}")
    return None


def save_session(session_data: dict, gemini_sid: str) -> None:
    try:
        with open(get_session_file(gemini_sid), "w") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        log_error(f"Erro ao salvar sessão: {e}")


class FileLock:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.fd = None

    def __enter__(self):
        self.fd = open(self.lock_file, "w")
        fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *args):
        if self.fd:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()


def find_active_session(gemini_sid: str) -> str | None:
    """Match EXATO por gemini_session_id."""
    try:
        sessions = get_json("/api/sessions/") or []
        for s in sessions:
            if s.get("status") != "active":
                continue
            metadata = s.get("metadata", {}) or {}
            if metadata.get("gemini_session_id") == gemini_sid:
                return s.get("id")
    except Exception as e:
        log_error(f"Erro ao buscar sessões: {e}")
    return None


def get_or_create_session(gemini_sid: str, agent_name: str) -> str | None:
    with FileLock(get_lock_file(gemini_sid)):
        current = load_session(gemini_sid)
        if current and current.get("kothar_session_id"):
            current["last_used"] = datetime.now(timezone.utc).isoformat()
            save_session(current, gemini_sid)
            return current["kothar_session_id"]

        existing = find_active_session(gemini_sid)
        if existing:
            session_data = {
                "kothar_session_id": existing,
                "agent_name": agent_name,
                "gemini_session_id": gemini_sid,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_used": datetime.now(timezone.utc).isoformat(),
                "pid": os.getpid(),
            }
            save_session(session_data, gemini_sid)
            return existing

        return create_new_session(gemini_sid, agent_name)


def create_new_session(gemini_sid: str, agent_name: str) -> str | None:
    session_info = {
        "terminal": os.environ.get("TERM", "unknown"),
        "hostname": os.environ.get("HOSTNAME", "localhost"),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "gemini_session_id": gemini_sid,
        "created_via": "gemini_hook_v6",
    }

    result = post_json("/api/sessions/", {
        "agent_name": agent_name,
        "llm_model": os.environ.get("KOTHAR_MODEL", "gemini"),
        "task_summary": f"Sessão {agent_name}",
        "metadata": session_info,
    })

    if result and "id" in result:
        session_data = {
            "kothar_session_id": result["id"],
            "agent_name": agent_name,
            "gemini_session_id": gemini_sid,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
        }
        save_session(session_data, gemini_sid)
        return result["id"]

    return None


def get_agent_name() -> str:
    return (
        os.environ.get("KOTHAR_AGENT_NAME") or
        os.environ.get("USER") or
        "gemini_cli"
    )


def process_event(event: dict) -> None:
    hook_type = event.get("hook_event_name", "unknown")
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    tool_output = event.get("tool_response", "")
    is_error = bool(event.get("error"))
    error_msg = str(event.get("error", ""))[:500] if is_error else None

    gemini_sess_id = event.get("session_id") or f"gemini-{os.getpid()}"
    agent_name = get_agent_name()

    kothar_session = get_or_create_session(gemini_sess_id, agent_name)
    if not kothar_session:
        log_error("Sem sessão Kothar - evento ignorado")
        return

    if hook_type in ("PreToolUse", "pre_tool"):
        event_type = "tool_call"
    elif hook_type in ("PostToolUse", "post_tool"):
        event_type = "tool_result"
    elif hook_type in ("UserPromptSubmit", "user_prompt"):
        event_type = "user_message"
    else:
        event_type = hook_type.lower()

    tool_out_dict = tool_output if isinstance(tool_output, dict) else {"result": str(tool_output)[:4000]}
    tool_in_dict = tool_input if isinstance(tool_input, dict) else {"raw": str(tool_input)}

    post_json("/api/traces/", {
        "session_id": kothar_session,
        "event_type": event_type,
        "agent_name": agent_name,
        "tool_name": tool_name or None,
        "tool_input": tool_in_dict,
        "tool_output": tool_out_dict,
        "tokens_used": 0,
        "is_error": is_error,
        "error_message": error_msg,
        "metadata": {
            "hook_type": hook_type,
            "gemini_session": gemini_sess_id,
            "agent": "gemini",
            "agent_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })


def cmd_end_session():
    raw = sys.stdin.read().strip()
    event = {}
    if raw:
        try:
            event = json.loads(raw)
        except:
            pass

    # Encontrar qualquer sessão local para encerrar
    import glob
    for f in glob.glob(f"{SESSION_DIR}/*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            session_id = data.get("kothar_session_id")
            if session_id:
                post_json(f"/api/sessions/{session_id}/complete", {"status": "completed"})
                post_json("/api/orchestrate/compile", {"session_id": session_id})
            os.remove(f)
        except:
            pass

    print("Sessões Gemini encerradas.")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "end":
            cmd_end_session()
            return
        elif cmd == "status":
            import glob
            for f in glob.glob(f"{SESSION_DIR}/*.json"):
                with open(f) as fp:
                    print(json.dumps(json.load(fp), indent=2))
            return

    raw = sys.stdin.read().strip()
    if raw:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            event = {"hook_event_name": "unknown"}
    else:
        event = {"hook_event_name": "session_start"}

    process_event(event)


if __name__ == "__main__":
    main()
