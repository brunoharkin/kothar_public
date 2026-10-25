#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Daemon de Tracing (CORRIGIDO)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Monitora arquivo de log e envia traces ao Kothar.

 CORREÇÕES:
 1. Busca arquivo de log dinamicamente (não hardcoded)
 2. Sessões isoladas por processo/PID
 3. Logging de erros (não silencioso)
 4. Sessão não encerra automaticamente
=============================================================
"""

import json
import os
import sys
import glob
import time
import urllib.request
from datetime import datetime, timezone

KOTHAR_API = os.environ.get("KOTHAR_API_URL", "http://localhost:8080")
DEBUG = os.environ.get("KOTHAR_DEBUG", "0") == "1"


def log_debug(msg: str):
    """Log de debug."""
    if DEBUG:
        print(f"[KOTHAR DEBUG] {msg}", file=sys.stderr)


def log_error(msg: str):
    """Log de erro."""
    print(f"[KOTHAR ERROR] {msg}", file=sys.stderr)


def log_info(msg: str):
    """Log info."""
    print(f"[KOTHAR] {msg}", file=sys.stderr)


def post_json(endpoint: str, data: dict) -> dict | None:
    """Envia JSON para API com logging."""
    try:
        body = json.dumps(data, default=str).encode()
        req = urllib.request.Request(
            f"{KOTHAR_API}{endpoint}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        log_error(f"API offline ({endpoint}): {e}")
        return None
    except Exception as e:
        log_error(f"Erro ao enviar para {endpoint}: {e}")
        return None


def get_session_file() -> str:
    """Retorna arquivo de sessão para o usuário (fixo).

    Usa o nome do usuário como identificador - reutiliza sessão para o mesmo usuário.
    """
    user = os.environ.get("USER", "default")
    return f"/tmp/kothar_session_{user}.json"


def load_current_session() -> dict | None:
    """Carrega sessão atual."""
    session_file = get_session_file()
    try:
        if os.path.exists(session_file):
            with open(session_file) as f:
                return json.load(f)
    except Exception as e:
        log_error(f"Erro ao ler sessão: {e}")
    return None


def save_current_session(session_data: dict) -> None:
    """Salva sessão atual."""
    session_file = get_session_file()
    try:
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
        log_debug(f"Sessão salva em {session_file}")
    except Exception as e:
        log_error(f"Erro ao salvar sessão: {e}")


def get_agent_name() -> str:
    """Obtém nome do agente dinamicamente."""
    return (
        os.environ.get("KOTHAR_AGENT_NAME") or
        os.environ.get("SESSION_NAME") or
        os.environ.get("USER") or
        "kothar_maestro"
    )


def find_log_file() -> str | None:
    """
    Busca arquivo de log dinamicamente em múltiplos locais.

    Procura em ordem de prioridade:
    1. ~/.gemini/antigravity/brain/*/logs/overview.txt
    2. ~/.gemini/*/logs/overview.txt
    3. ~/.gemini/**/overview.txt
    4. ~/.kothar/logs/*.log
    """
    home = os.path.expanduser("~")

    patterns = [
        # Antigravity logs
        f"{home}/.gemini/antigravity/brain/*/.system_generated/logs/overview.txt",
        f"{home}/.gemini/antigravity/*/logs/overview.txt",
        f"{home}/.gemini/antigravity/**/overview.txt",
        # Gemini logs gerais
        f"{home}/.gemini/*/logs/overview.txt",
        f"{home}/.gemini/**/overview.txt",
        # Kothar logs
        f"{home}/.kothar/logs/*.log",
        # Fallback - qualquer log txt
        f"{home}/.gemini/**/*.txt",
    ]

    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern, recursive=True))

    if not all_files:
        return None

    # Remove duplicatas
    all_files = list(set(all_files))
    # Ordena por data de modificação (mais recente primeiro)
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    log_debug(f"Encontrado arquivo de log mais recente: {all_files[0]}")
    return all_files[0]


def create_session() -> dict | None:
    """Cria nova sessão no Kothar."""
    agent_name = get_agent_name()

    log_debug(f"Criando sessão para agente: {agent_name}")

    result = post_json("/api/sessions/", {
        "agent_name": agent_name,
        "llm_model": os.environ.get("KOTHAR_MODEL", "gemini-antigravity"),
        "task_summary": f"Sessão Kothar Maestro — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        "metadata": {
            "terminal": os.environ.get("TERM", "unknown"),
            "hostname": os.environ.get("HOSTNAME", "localhost"),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "created_via": "antigravity_tracer",
        },
    })

    if result and "id" in result:
        session_data = {
            "kothar_session_id": result["id"],
            "agent_name": agent_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        save_current_session(session_data)
        log_info(f"Sessão criada: {result['id']}")
        return session_data

    log_error("Falha ao criar sessão")
    return None


def get_or_create_session() -> str | None:
    """Obtém ou cria sessão."""
    current = load_current_session()
    if current and current.get("kothar_session_id"):
        log_debug(f"Usando sessão existente: {current['kothar_session_id']}")
        return current["kothar_session_id"]

    session_data = create_session()
    return session_data["kothar_session_id"] if session_data else None


def send_trace(session_id: str, event_type: str, input_data: dict, output_data: dict,
               tool_name: str = None, is_error: bool = False, error_msg: str = None):
    """Envia trace para API."""
    agent_name = get_agent_name()

    result = post_json("/api/traces/", {
        "session_id": session_id,
        "event_type": event_type,
        "agent_name": agent_name,
        "tool_name": tool_name,
        "tool_input": input_data,
        "tool_output": output_data,
        "tokens_used": 0,
        "is_error": is_error,
        "error_message": error_msg,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "terminal": os.environ.get("TERM", "unknown"),
            "hostname": os.environ.get("HOSTNAME", "localhost"),
        }
    })

    if result:
        log_debug(f"Trace: {event_type} - {tool_name}")
    else:
        log_error(f"Falha ao enviar trace: {event_type}")


def main():
    log_info("Kothar Antigravity Tracer iniciando...")

    # Buscar arquivo de log dinamicamente
    log_file = find_log_file()

    if not log_file:
        log_error("Nenhum arquivo de log encontrado!")
        log_error("Procurando em:")
        log_error("  - ~/.gemini/antigravity/brain/*/logs/")
        log_error("  - ~/.gemini/*/logs/")
        log_error("  - ~/.kothar/logs/")

        # Tenta criar sessão mesmo assim (sem arquivo de log)
        session_id = get_or_create_session()
        if session_id:
            log_info(f"Sessão criada sem monitoramento de log: {session_id}")
        else:
            log_error("Não foi possível criar sessão. API offline?")
        return

    log_info(f"Monitorando: {log_file}")

    # Criar ou obter sessão
    session_id = get_or_create_session()
    if not session_id:
        log_error("Falha ao criar/obter sessão")
        return

    log_info(f"Trace watcher started for session {session_id}")

    # Verificar tamanho atual do arquivo
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # Ir para o final
            last_pos = f.tell()
    except Exception as e:
        log_error(f"Erro ao abrir arquivo de log: {e}")
        return

    # Loop principal - monitora arquivo
    while True:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(last_pos)

                while True:
                    line = f.readline()
                    if not line:
                        break

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    source = data.get("source")
                    content = data.get("content", "")
                    tool_calls = data.get("tool_calls", [])

                    if source == "USER_EXPLICIT":
                        # Extrair mensagem do usuário
                        clean_content = content
                        if "<USER_REQUEST>" in content:
                            clean_content = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                        send_trace(session_id, "user_message", {"msg": clean_content}, {})

                    elif source == "MODEL":
                        if content:
                            send_trace(session_id, "llm_response", {"msg": "Resposta do Maestro"}, {"result": content})

                        if tool_calls:
                            for tc in tool_calls:
                                t_name = tc.get("name", "tool")
                                args = tc.get("args", {})
                                output = {}

                                # Anti-Truncation: Capturar snapshot completo do arquivo
                                if t_name in ("write_to_file", "multi_replace_file_content", "replace_file_content"):
                                    target = args.get("TargetFile")
                                    if target:
                                        retries = 10
                                        while not os.path.exists(target) and retries > 0:
                                            time.sleep(0.5)
                                            retries -= 1
                                        if os.path.exists(target):
                                            try:
                                                with open(target, 'r', encoding='utf-8') as f:
                                                    output["FileSnapshot"] = f.read()
                                            except Exception:
                                                pass

                                send_trace(session_id, t_name, args, output, tool_name=t_name)

                last_pos = f.tell()

        except FileNotFoundError:
            log_error(f"Arquivo de log removido: {log_file}")
            # Tentar encontrar novo arquivo
            log_file = find_log_file()
            if not log_file:
                log_error("Nenhum arquivo de log encontrado. Aguardando...")
                time.sleep(5)
                continue
            log_info(f"Novo arquivo encontrado: {log_file}")
            last_pos = 0

        except Exception as e:
            log_error(f"Erro no loop: {e}")
            time.sleep(1)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
