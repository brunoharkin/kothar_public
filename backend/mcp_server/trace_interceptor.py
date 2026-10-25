import json
import urllib.request
import urllib.error
import sys
from datetime import datetime, timezone
from typing import Optional

KOTHAR_API = "http://localhost:8080"
AGENT_ID = "kothar_mcp"

def _log_error(msg: str, error: Optional[Exception] = None):
    """Log de erros para stderr (visível no console)."""
    import os
    pid = os.getpid()
    timestamp = datetime.now(timezone.utc).isoformat()
    if error:
        sys.stderr.write(f"[KOTHAR TRACE ERROR] {timestamp} PID={pid} | {msg}: {error}\n")
        sys.stderr.flush()
    else:
        sys.stderr.write(f"[KOTHAR TRACE ERROR] {timestamp} PID={pid} | {msg}\n")
        sys.stderr.flush()

def _log_debug(msg: str):
    """Log de debug (ativo via KOTHAR_DEBUG=1)."""
    import os
    if os.environ.get("KOTHAR_DEBUG") == "1":
        timestamp = datetime.now(timezone.utc).isoformat()
        sys.stderr.write(f"[KOTHAR DEBUG] {timestamp} | {msg}\n")
        sys.stderr.flush()

def get_or_create_session() -> str | None:
    """Obtém ou cria sessão MCP no Kothar."""
    try:
        _log_debug(f"get_or_create_session() - criando sessão MCP")
        body = json.dumps({
            "agent_name": AGENT_ID,
            "llm_model": "mcp-server",
            "task_summary": f"Sessão MCP RAG — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            "metadata": {"type": "mcp"}
        }).encode()

        req = urllib.request.Request(
            f"{KOTHAR_API}/api/sessions/",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            session_id = result.get("id")
            _log_debug(f"Sessão MCP criada: {session_id}")
            return session_id
    except urllib.error.URLError as e:
        _log_error(f"KOTHAR API offline (get_or_create_session): {e}")
        return None
    except json.JSONDecodeError as e:
        _log_error(f"Erro ao decodificar resposta da API: {e}")
        return None
    except Exception as e:
        _log_error(f"Erro ao criar sessão MCP: {e}")
        return None

def trace_mcp_event(
    session_id: str,
    tool_name: str,
    input_data: dict,
    output_data: dict,
    is_error: bool = False,
    error_msg: str = None
):
    """
    Registra um evento de memória no Kothar Trace.
    Usa o event_type="memory" para ativar o painel roxo (RAG) no frontend.

    ERROS SÃO LOGADOS - não são mais silenciosos.
    """
    try:
        _log_debug(f"trace_mcp_event() - tool={tool_name}, session={session_id[:8]}")

        payload = {
            "session_id": session_id,
            "event_type": "memory",
            "agent_name": AGENT_ID,
            "tool_name": tool_name,
            "tool_input": input_data,
            "tool_output": output_data,
            "tokens_used": 0,
            "is_error": is_error,
            "error_message": error_msg,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "trace_interceptor",
            }
        }
        req = urllib.request.Request(
            f"{KOTHAR_API}/api/traces/",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        _log_debug(f"Trace MCP gravado com sucesso")

    except urllib.error.URLError as e:
        _log_error(f"KOTHAR API offline (trace_mcp_event) - tool={tool_name}: {e}")
        # Não repassar exceção - trace não deve quebrar fluxo
    except json.JSONDecodeError as e:
        _log_error(f"Erro ao serializar payload - tool={tool_name}: {e}")
    except TimeoutError as e:
        _log_error(f"Timeout ao enviar trace - tool={tool_name}: {e}")
    except Exception as e:
        _log_error(f"Erro ao gravar trace MCP - tool={tool_name}: {e}")
        # Nunca quebrar o fluxo principal por erro de trace
