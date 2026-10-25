#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v6.0 — Hook DEFINITIVO (ANTI-FANTASMA)
 Engenheiro Kothar | Ugarit Digital
=============================================================

 REGRAS ABSOLUTAS:
 1. Sessão é vinculada ao CLAUDE_SESSION_ID (ID nativo do Claude CLI)
 2. Uma sessão = UM único ID do início ao fim
 3. PROIBIDO criar nova sessão se já existe uma ativa
 4. Lockfile previne duplicação em processos paralelos
 5. Reutiliza sessão ativa se mesmo claude_session_id
=============================================================
"""

import json
import os
import sys
import fcntl
import uuid
import urllib.request
import urllib.error
import hashlib
from datetime import datetime, timezone

KOTHAR_API = os.environ.get("KOTHAR_API_URL", "http://localhost:8080")
TIMEOUT = 5
DEBUG = os.environ.get("KOTHAR_DEBUG", "0") == "1"

SESSION_DIR = "/tmp/kothar_sessions"
LOCK_DIR = "/tmp/kothar_locks"

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOCK_DIR, exist_ok=True)


def get_token_type(tool_name: str, hook_type: str) -> str:
    """Classifica o tipo de token gasto para categorização."""
    if hook_type == "UserPromptSubmit":
        return "user_input"
    if tool_name in ("Read", "Claude:Read", "Grep", "Claude:Grep", "Glob", "Claude:Glob"):
        return "context_loading"
    if tool_name in ("Write", "Claude:Write", "Edit", "Claude:Edit"):
        return "code_generation"
    if tool_name in ("Bash", "Claude:Bash"):
        return "execution"
    if tool_name in ("Agent", "Claude:Agent") or "Agent" in (tool_name or ""):
        return "subagent"
    if tool_name == "Chat:Agent" or "thinking" in (tool_name or "").lower():
        return "model_reasoning"
    return "other"


def estimate_tokens(text: str) -> int:
    """Estimativa simples de tokens (1 token ≈ 4 caracteres em inglês)."""
    if not text:
        return 0
    # Para código/markdown, usa ~3.5 chars por token (mais denso)
    return max(1, int(len(text) / 3.5))


def extract_text_from_input(tool_input) -> str:
    """Extrai texto legível do tool_input para estimar tokens."""
    if isinstance(tool_input, dict):
        parts = []
        # Read tools
        if tool_input.get('file_path'):
            parts.append(f"file: {tool_input.get('file_path', '')}")
        if tool_input.get('path'):
            parts.append(f"path: {tool_input.get('path', '')}")
        # Bash
        if tool_input.get('command'):
            parts.append(f"cmd: {tool_input.get('command', '')}")
        # Edit
        if tool_input.get('old_string'):
            parts.append(f"before: {tool_input.get('old_string', '')}")
        if tool_input.get('new_string'):
            parts.append(f"after: {tool_input.get('new_string', '')}")
        # Write
        if tool_input.get('content'):
            parts.append(f"content: {tool_input.get('content', '')}")
        # Search
        if tool_input.get('pattern'):
            parts.append(f"pattern: {tool_input.get('pattern', '')}")
        if tool_input.get('query'):
            parts.append(f"query: {tool_input.get('query', '')}")
        # Agent/Subagent
        if tool_input.get('prompt'):
            parts.append(f"prompt: {tool_input.get('prompt', '')}")
        if tool_input.get('task'):
            parts.append(f"task: {tool_input.get('task', '')}")
        if tool_input.get('description'):
            parts.append(f"desc: {tool_input.get('description', '')}")
        # Thinking
        if tool_input.get('thinking'):
            parts.append(f"thinking: {tool_input.get('thinking', '')}")
        # Output (Chat:Agent)
        if tool_input.get('text'):
            parts.append(f"text: {tool_input.get('text', '')}")
        # Todos
        if tool_input.get('todos'):
            todos = tool_input.get('todos', [])
            if isinstance(todos, list):
                parts.append(f"todos: {json.dumps(todos)}")
        return '\n'.join(parts)
    return str(tool_input) if tool_input else ""


def log_debug(msg: str):
    if DEBUG:
        print(f"[KOTHAR DEBUG] {msg}", file=sys.stderr)


def log_error(msg: str):
    print(f"[KOTHAR ERROR] {msg}", file=sys.stderr)


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
    except urllib.error.URLError as e:
        log_error(f"API offline ({endpoint}): {e}")
        return None
    except Exception as e:
        log_error(f"Erro ao enviar para {endpoint}: {e}")
        return None


def post_thinking(session_id: str, agent_name: str, thinking_content: str, tokens: int = 0, metadata: dict | None = None) -> dict | None:
    """Envia thinking para API usando record_thinking() no backend."""
    return post_json("/api/traces/thinking", {
        "session_id": session_id,
        "agent_name": agent_name,
        "thinking_content": thinking_content,
        "tokens": tokens,
        "metadata": metadata or {},
    })


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


# ============================================================
# IDENTIFICAÇÃO ÚNICA DA SESSÃO
# ============================================================

def get_session_key() -> str:
    """Chave única da sessão baseada em:
    1. CLAUDE_SESSION_ID (se disponível) - PRIORIDADE MÁXIMA
    2. PID do processo
    3. CWD + Terminal + User (fallback)
    """
    claude_sid = os.environ.get("CLAUDE_SESSION_ID", "")

    if claude_sid:
        # Hash para evitar problemas com caracteres especiais
        return hashlib.md5(f"claude-{claude_sid}".encode()).hexdigest()[:16]

    # Fallback: PID + CWD
    pid = os.getpid()
    cwd = os.getcwd()
    user = os.environ.get("USER", "default")
    raw_key = f"{user}-{pid}-{cwd}"
    return hashlib.md5(raw_key.encode()).hexdigest()[:16]


def get_session_file() -> str:
    return f"{SESSION_DIR}/kothar_{get_session_key()}.json"


def get_lock_file() -> str:
    return f"{LOCK_DIR}/kothar_{get_session_key()}.lock"


def load_session() -> dict | None:
    session_file = get_session_file()
    try:
        if os.path.exists(session_file):
            with open(session_file) as f:
                data = json.load(f)
                # Verificar se ainda é válida (PID ativo)
                if data.get("pid") and not is_pid_alive(data["pid"]):
                    log_debug(f"Sessão órfã detectada (PID {data['pid']} morto). Limpando.")
                    os.remove(session_file)
                    return None
                return data
    except Exception as e:
        log_error(f"Erro ao ler sessão: {e}")
    return None


def save_session(session_data: dict) -> None:
    session_file = get_session_file()
    try:
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        log_error(f"Erro ao salvar sessão: {e}")


def is_pid_alive(pid: int) -> bool:
    """Verifica se o PID ainda está ativo."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


# ============================================================
# LOCK PARA EVITAR CRIAÇÃO PARALELA
# ============================================================

class FileLock:
    """Lock file para prevenir criação de sessões duplicadas."""
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


# ============================================================
# CRIAÇÃO DE SESSÃO (COM PROTEÇÃO)
# ============================================================

def get_or_create_session(claude_sid: str) -> str | None:
    """Obtém ou cria sessão Kothar.

    PROTEÇÃO:
    1. Verifica arquivo local PRIMEIRO
    2. Se existe e mesmo claude_sid, REUTILIZA
    3. Se não existe, cria nova COM LOCK
    4. Verifica se já existe sessão ativa no backend com mesmo agente
    """
    with FileLock(get_lock_file()):
        # 1. Verificar sessão local
        current = load_session()
        if current and current.get("kothar_session_id"):
            # Atualizar claude_sid se mudou
            current["claude_session_id"] = claude_sid
            current["last_used"] = datetime.now(timezone.utc).isoformat()
            save_session(current)
            log_debug(f"Reutilizando sessão local: {current['kothar_session_id']}")
            return current["kothar_session_id"]

        # 2. Verificar se backend já tem sessão ativa para este agente
        agent_name = get_agent_name()
        existing = find_active_session_for_agent(agent_name, claude_sid)
        if existing:
            log_debug(f"Sessão ativa encontrada no backend: {existing}")
            session_data = {
                "kothar_session_id": existing,
                "agent_name": agent_name,
                "claude_session_id": claude_sid,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_used": datetime.now(timezone.utc).isoformat(),
                "pid": os.getpid(),
                "reused_from_backend": True,
            }
            save_session(session_data)
            return existing

        # 3. Criar nova sessão (protegido por lock)
        return create_new_session(agent_name, claude_sid)


def find_active_session_for_agent(agent_name: str, claude_sid: str) -> str | None:
    """Busca sessão ativa no backend que corresponda EXATAMENTE ao claude_sid.

    REGRA ABSOLUTA: Só retorna sessão se o claude_session_id BATE EXATAMENTE.
    Se não bate, retorna None para criar nova (evita sessões cruzadas).
    """
    try:
        sessions = get_json("/api/sessions/") or []
        for s in sessions:
            if s.get("status") != "active":
                continue
            metadata = s.get("metadata", {}) or {}
            # MATCH EXATO - sem fallback
            if metadata.get("claude_session_id") == claude_sid:
                return s.get("id")
    except Exception as e:
        log_error(f"Erro ao buscar sessões: {e}")
    return None


def create_new_session(agent_name: str, claude_sid: str) -> str | None:
    """Cria nova sessão Kothar."""
    session_info = {
        "terminal": os.environ.get("TERM", "unknown"),
        "hostname": os.environ.get("HOSTNAME", "localhost"),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "claude_session_id": claude_sid,  # CRÍTICO: vincula ao Claude CLI
        "created_via": "claude_hook_v6",
    }

    result = post_json("/api/sessions/", {
        "agent_name": agent_name,
        "llm_model": os.environ.get("KOTHAR_MODEL", "claude"),
        "task_summary": f"Sessão {agent_name}",
        "metadata": session_info,
    })

    if result and "id" in result:
        session_data = {
            "kothar_session_id": result["id"],
            "agent_name": agent_name,
            "claude_session_id": claude_sid,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "info": session_info,
        }
        save_session(session_data)
        log_debug(f"Nova sessão criada: {result['id']}")
        return result["id"]

    log_error("Falha ao criar sessão no backend")
    return None


def get_agent_name() -> str:
    return (
        os.environ.get("KOTHAR_AGENT_NAME") or
        os.environ.get("USER") or
        "claude_cli"
    )


# ============================================================
# TRANSCRIPT TAILING
# ============================================================

def process_incremental_transcript(transcript_path: str, session_id: str, claude_sess_id: str):
    if not transcript_path or not os.path.exists(transcript_path):
        return

    cursor_file = f"{SESSION_DIR}/cursor_{claude_sess_id}.txt"
    last_pos = 0
    if os.path.exists(cursor_file):
        try:
            with open(cursor_file, "r") as c:
                last_pos = int(c.read().strip())
        except (ValueError, IOError) as e:
            log_debug(f"Cursor inválido, iniciando do início: {e}")

    agent_name = get_agent_name()
    events_captured = 0

    try:
        with open(transcript_path, "r") as f:
            f.seek(last_pos)
            new_lines = f.readlines()
            with open(cursor_file, "w") as c:
                c.write(str(f.tell()))

        for line in new_lines:
            try:
                data = json.loads(line)
                msg_type = data.get("type", "")

                # Detectar se é mensagem de SUBAGENTE
                is_subagent_msg = data.get("isMeta", False) or data.get("isSidechain", False)
                parent_tool_id = data.get("parent_tool_use_id", None)
                msg_agent = "subagent" if is_subagent_msg else agent_name

                if msg_type == "assistant":
                    msg_obj = data.get("message", {})
                    content = msg_obj.get("content", [])
                    usage = msg_obj.get("usage", {})
                    total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

                    text_parts = []
                    thinking_parts = []
                    tool_uses = []

                    for c in content:
                        ctype = c.get("type", "")
                        if ctype == "text":
                            text = c.get("text", "").strip()
                            if text:
                                text_parts.append(text)
                        elif ctype == "thinking":
                            think = c.get("thinking", "").strip()
                            if think:
                                thinking_parts.append(think)
                        elif ctype == "tool_use":
                            tool_name_inner = c.get("name", "")
                            tool_input_inner = c.get("input", {})
                            tool_uses.append({"name": tool_name_inner, "input": tool_input_inner})

                    if thinking_parts:
                        thinking_text = "\n\n".join(thinking_parts)
                        # Enviar via record_thinking() para salvar conteúdo completo
                        thinking_metadata = {
                            "source": "transcript_tail",
                            "type": "thinking",
                            "is_subagent_message": is_subagent_msg,
                            "parent_tool_use_id": parent_tool_id,
                        }
                        post_thinking(
                            session_id=session_id,
                            agent_name=msg_agent,
                            thinking_content=thinking_text,
                            tokens=total_tokens,
                            metadata=thinking_metadata,
                        )
                        events_captured += 1

                    if text_parts:
                        text = "\n\n".join(text_parts)
                        post_json("/api/traces/", {
                            "session_id": session_id,
                            "event_type": "assistant_response",
                            "agent_name": msg_agent,
                            "tool_name": "Chat:Agent",
                            "tool_input": {"text": text[:20000]},
                            "tokens_used": total_tokens,
                            "metadata": {
                                "source": "transcript_tail",
                                "type": "text",
                                "is_subagent_message": is_subagent_msg,
                                "parent_tool_use_id": parent_tool_id,
                            }
                        })
                        events_captured += 1

                    for tool in tool_uses:
                        post_json("/api/traces/", {
                            "session_id": session_id,
                            "event_type": "tool_call",
                            "agent_name": msg_agent,
                            "tool_name": tool["name"],
                            "tool_input": tool["input"],
                            "tokens_used": 0,
                            "metadata": {
                                "source": "transcript_tail",
                                "inline": True,
                                "is_subagent_message": is_subagent_msg,
                                "parent_tool_use_id": parent_tool_id,
                            }
                        })
                        events_captured += 1

                elif msg_type == "tool_result":
                    content = data.get("content", [])
                    for c in content:
                        if c.get("type") == "text":
                            tool_output = c.get("text", "")[:5000]
                            post_json("/api/traces/", {
                                "session_id": session_id,
                                "event_type": "tool_result",
                                "agent_name": msg_agent,
                                "tool_output": {"text": tool_output},
                                "tokens_used": 0,
                                "metadata": {
                                    "source": "transcript_tail",
                                    "type": "tool_result",
                                    "is_subagent_message": is_subagent_msg,
                                    "parent_tool_use_id": parent_tool_id,
                                }
                            })
                            events_captured += 1

            except json.JSONDecodeError as e:
                log_debug(f"JSON inválido no transcript: {e}")

    except Exception as e:
        log_error(f"Erro no incremental tailing: {e}")


# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def process_claude_event(event: dict) -> None:
    hook_type = event.get("hook_event_name", "unknown")

    # CRÍTICO: Usar CLAUDE_SESSION_ID do evento, não do ambiente
    claude_sess_id = (
        event.get("session_id") or
        os.environ.get("CLAUDE_SESSION_ID") or
        f"unknown-{os.getpid()}"
    )

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    tool_result = event.get("tool_response", {})
    is_error = bool(event.get("error") or (
        isinstance(tool_result, dict) and tool_result.get("is_error")
    ))

    # Obter sessão (reutiliza ou cria - PROTEGIDO)
    kothar_session = get_or_create_session(claude_sess_id)
    if not kothar_session:
        log_error("Sem sessão Kothar - evento ignorado")
        return

    # Mapear tipo de evento
    event_type_map = {
        "PreToolUse": "tool_call",
        "PostToolUse": "tool_result",
        "UserPromptSubmit": "user_message",
        "PreCompact": "context_compact",
        # Memória e RAG
        "memory_load": "memory_load",
        "memory_preload": "memory_load",
        "memory_inject": "memory_inject",
        "rag_preload": "rag_preload",
        "rag_inject": "rag_inject",
        "rag_search": "rag_search",
        "rag_cache_hit": "rag_cache_hit",
        "rag_cache_miss": "rag_cache_miss",
        "skill_index": "skill_index",
        "skill_retrieval": "skill_retrieval",
    }
    event_type = event_type_map.get(hook_type, hook_type.lower())

    # Auto-detectar RAG/Memória no nome do tool/metadata
    if event_type not in ("tool_call", "tool_result", "user_message", "context_compact"):
        tool_name = event.get("tool_name", "") or ""
        metadata = event.get("metadata", {}) or {}
        if "rag" in tool_name.lower() or metadata.get("rag"):
            event_type = "rag_preload"
        elif "memory" in tool_name.lower() or metadata.get("memory"):
            event_type = "memory_load"
        elif "skill" in tool_name.lower() or metadata.get("skill"):
            event_type = "skill_retrieval"

    # Extrair mensagem do usuário
    if hook_type == "UserPromptSubmit":
        msg = event.get("prompt", "")
        if isinstance(msg, dict):
            c = msg.get("content", "")
            if isinstance(c, list):
                c = " ".join(part.get("text", "") for part in c if isinstance(part, dict))
            else:
                c = str(c)
        else:
            c = str(msg)
        tool_input = {"prompt": c}

    usage = event.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Se não tem usage real do Claude, estimar tokens baseado no conteúdo
    if input_tokens == 0 and output_tokens == 0:
        # Estimar input tokens (conteúdo enviado)
        if hook_type == "UserPromptSubmit":
            msg = event.get("prompt", "")
            if isinstance(msg, dict):
                c = msg.get("content", "")
                if isinstance(c, list):
                    c = " ".join(part.get("text", "") for part in c if isinstance(part, dict))
                else:
                    c = str(c)
            else:
                c = str(msg)
            input_tokens = estimate_tokens(str(c))
            output_tokens = 0
        elif hook_type == "PreToolUse":
            # Tools de leitura têm input tokens altos
            if tool_name in ("Read", "Claude:Read") or tool_name == "Grep" or tool_name == "Claude:Grep":
                # Read consome MUITO token (lê arquivo inteiro)
                file_path = tool_input.get("file_path") or tool_input.get("path", "") if isinstance(tool_input, dict) else ""
                # Estimativa baseada no path (não sabemos tamanho real, mas ~500 tokens mínimo)
                input_tokens = 500  # Base para ler
                if file_path:
                    # Tenta ler o tamanho do arquivo se possível
                    try:
                        if os.path.exists(file_path):
                            size = os.path.getsize(file_path)
                            input_tokens += size // 3
                    except (IOError, OSError) as e:
                        log_debug(f"Erro ao ler tamanho do arquivo: {e}")
                output_tokens = 50
            elif tool_name in ("Write", "Claude:Write"):
                content = tool_input.get("content", "") if isinstance(tool_input, dict) else ""
                input_tokens = estimate_tokens(str(content))
                output_tokens = 50
            elif tool_name in ("Edit", "Claude:Edit"):
                old_str = tool_input.get("old_string", "") if isinstance(tool_input, dict) else ""
                new_str = tool_input.get("new_string", "") if isinstance(tool_input, dict) else ""
                input_tokens = estimate_tokens(str(old_str)) + 100
                output_tokens = estimate_tokens(str(new_str))
            elif tool_name == "Bash" or tool_name == "Claude:Bash":
                cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
                input_tokens = estimate_tokens(str(cmd))
                output_tokens = 100  # Para a execução
            elif tool_name == "Agent" or tool_name == "Claude:Agent":
                prompt = tool_input.get("prompt", "") if isinstance(tool_input, dict) else ""
                input_tokens = estimate_tokens(str(prompt))
                output_tokens = 1500  # Subagente gera bastante output
            else:
                input_tokens = estimate_tokens(extract_text_from_input(tool_input))
                output_tokens = 50
        elif hook_type == "PostToolUse":
            # Resultado da tool
            if tool_name in ("Read", "Claude:Read"):
                # O resultado (conteúdo do arquivo) é input tokens do PRÓXIMO turno
                input_tokens = 3000  # Estimativa média para arquivo lido
                output_tokens = 0
            elif tool_name == "Bash" or tool_name == "Claude:Bash":
                # Output do bash é enviado de volta
                output_str = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                input_tokens = estimate_tokens(str(output_str))
                output_tokens = 50
            else:
                output_str = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                input_tokens = estimate_tokens(str(output_str))
                output_tokens = 20

    tokens = input_tokens + output_tokens

    agent_name = get_agent_name()
    is_subagent = tool_name == "Agent"
    subagent_real_name = None

    if is_subagent and hook_type == "PreToolUse":
        if isinstance(tool_input, dict):
            subagent_type = tool_input.get("subagent_type", "general")
            subagent_task = tool_input.get("prompt", "")[:2000]
            subagent_description = tool_input.get("description", "")
        else:
            subagent_type = "general"
            subagent_task = str(tool_input)[:2000]
            subagent_description = ""

        subagent_real_name = subagent_type
        event_type = "subagent_spawn"
        tool_input = {
            "subagent_type": subagent_type,
            "subagent_name": subagent_type,
            "task": subagent_task,
            "description": subagent_description,
        }

    trace_agent_name = subagent_real_name if subagent_real_name else agent_name

    # Detectar subagente - tem 3 eventos: spawn, execução interna, resultado
    subagent_logs = []
    subagent_id = None
    is_subagent_spawn = False
    is_subagent_result = False

    if tool_name == "Agent" and hook_type == "PreToolUse":
        is_subagent_spawn = True
        if isinstance(tool_input, dict):
            subagent_type = tool_input.get("subagent_type", "general")
            subagent_task = tool_input.get("prompt", "")[:5000]
            subagent_description = tool_input.get("description", "")
            # Extrair task do input
            subagent_logs.append({
                "type": "spawn",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "subagent_type": subagent_type,
                "description": subagent_description,
                "task": subagent_task[:5000],
            })
        else:
            subagent_type = "general"
            subagent_task = str(tool_input)[:5000]
            subagent_description = ""

        subagent_real_name = subagent_type
        event_type = "subagent_spawn"
        tool_input_payload = {
            "subagent_type": subagent_type,
            "subagent_name": subagent_type,
            "task": subagent_task,
            "description": subagent_description,
        }
        tool_input = tool_input_payload

    elif tool_name == "Agent" and hook_type == "PostToolUse":
        is_subagent_result = True
        # Capturar o resultado completo do subagente
        subagent_id = "result_" + str(uuid.uuid4())[:8]
        # O tool_output pode ter o resultado do subagente
        if isinstance(tool_result, dict):
            subagent_result_text = ""
            if "content" in tool_result:
                content = tool_result["content"]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            subagent_result_text += item.get("text", "")
                        elif isinstance(item, dict) and item.get("type") == "tool_use":
                            subagent_logs.append({
                                "type": "subagent_tool_call",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "tool_name": item.get("name", "?"),
                                "tool_input": item.get("input", {}),
                            })
                else:
                    subagent_result_text = str(content)
            elif "text" in tool_result:
                subagent_result_text = str(tool_result["text"])
            else:
                subagent_result_text = str(tool_result)[:10000]

            subagent_logs.append({
                "type": "result",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": subagent_result_text[:20000],
            })
        else:
            subagent_logs.append({
                "type": "result",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": str(tool_result)[:20000],
            })
        event_type = "subagent_complete"

    trace_agent_name = subagent_real_name if subagent_real_name else agent_name

    # Detectar tipo pelo tool_name
    is_thinking_event = False
    thinking_content = ""
    if tool_name == "Claude:thinking" or (isinstance(tool_input, dict) and "thinking" in tool_input and not tool_input.get("command")):
        event_type = "thinking"
        is_thinking_event = True
        # Extrair conteúdo completo do thinking
        if isinstance(tool_input, dict):
            thinking_content = tool_input.get("thinking", "")
        if not thinking_content:
            thinking_content = str(tool_input) if tool_input else ""
    elif tool_name == "Chat:Agent" or (isinstance(tool_input, dict) and tool_input.get("text") and hook_type != "UserPromptSubmit"):
        event_type = "assistant_response"

    # Detectar Plan/Task
    plan_content = None
    plan_type = None
    todos_data = None
    if hook_type == "PreToolUse" and isinstance(tool_input, dict):
        subagent_type = tool_input.get("subagent_type", "")
        if subagent_type == "Plan" or tool_name == "EnterPlanMode":
            plan_type = "plan"
            plan_content = tool_input.get("prompt") or tool_input.get("task") or tool_input.get("content")
        elif "Task" in str(tool_name) or "TodoWrite" in str(tool_name):
            plan_type = "task"
            plan_content = tool_input.get("todos") or tool_input.get("content")
            # Capturar todos estruturados
            todos_data = tool_input.get("todos")

    extra_metadata = {
        "hook_type": hook_type,
        "claude_session": claude_sess_id,
        "parent_agent": agent_name,
        "subagent_real_name": subagent_real_name,
        "is_subagent": is_subagent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if plan_type:
        extra_metadata["plan_type"] = plan_type
        extra_metadata["plan_content"] = str(plan_content)[:50000] if plan_content else ""
        if todos_data:
            extra_metadata["todos"] = todos_data
        event_type = f"agent_{plan_type}"

    if subagent_logs:
        extra_metadata["subagent_logs"] = subagent_logs

    # Enviar trace principal
    post_json("/api/traces/", {
        "session_id": kothar_session,
        "event_type": event_type,
        "agent_name": trace_agent_name,
        "tool_name": tool_name or None,
        "tool_input": tool_input if isinstance(tool_input, dict) else {"raw": str(tool_input)},
        "tool_output": tool_result if isinstance(tool_result, dict) else {"raw": str(tool_result)[:2000]},
        "tokens_used": tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "is_error": is_error,
        "error_message": str(event.get("error", ""))[:500] if is_error else None,
        "metadata": {
            **extra_metadata,
            "tokens_in": input_tokens,
            "tokens_out": output_tokens,
            "token_type": get_token_type(tool_name, hook_type),
        },
    })

    # Para thinking events, enviar via record_thinking() para salvar conteúdo completo
    if is_thinking_event and thinking_content:
        thinking_metadata = {
            **extra_metadata,
            "source": "process_claude_event",
            "hook_type": hook_type,
        }
        post_thinking(
            session_id=kothar_session,
            agent_name=trace_agent_name,
            thinking_content=thinking_content,
            tokens=tokens,
            metadata=thinking_metadata,
        )
        log_debug(f"Thinking enviado via record_thinking(): {len(thinking_content)} chars")

    # Subagent complete
    if is_subagent and hook_type == "PostToolUse":
        completed_agent_name = subagent_real_name or trace_agent_name
        original_input = event.get("tool_input", {})
        if isinstance(original_input, dict):
            real_name = original_input.get("subagent_type")
            if real_name:
                completed_agent_name = real_name

        post_json("/api/traces/", {
            "session_id": kothar_session,
            "event_type": "subagent_complete",
            "agent_name": completed_agent_name,
            "tool_name": tool_name,
            "tool_input": {"status": "complete"},
            "tool_output": tool_result if isinstance(tool_result, dict) else {"raw": str(tool_result)[:5000]},
            "tokens_used": tokens,
            "metadata": {
                "is_subagent_complete": True,
                "subagent_real_name": completed_agent_name,
                "parent_agent": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

    # Transcript tailing
    transcript_path = event.get("transcript_path")
    if transcript_path and kothar_session:
        process_incremental_transcript(transcript_path, kothar_session, claude_sess_id)


def cmd_end_session():
    """Encerra sessão manualmente."""
    raw = sys.stdin.read().strip()
    usage = {}
    event = {}
    if raw:
        try:
            event = json.loads(raw)
            usage = event.get("usage", {})
        except (json.JSONDecodeError, ValueError) as e:
            log_error(f"Erro ao parsear evento end: {e}")

    current = load_session()
    if not current or not current.get("kothar_session_id"):
        print("Nenhuma sessão ativa.")
        return

    session_id = current["kothar_session_id"]
    claude_sid = current.get("claude_session_id", "unknown")

    transcript_path = event.get("transcript_path")
    if transcript_path:
        process_incremental_transcript(transcript_path, session_id, claude_sid)

    tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    if tokens > 0:
        post_json("/api/traces/", {
            "session_id": session_id,
            "event_type": "session_stop",
            "agent_name": get_agent_name(),
            "tool_input": {"msg": "Sessão encerrada"},
            "tool_output": {"usage": usage},
            "tokens_used": tokens,
            "metadata": {"timestamp": datetime.now(timezone.utc).isoformat()}
        })

    post_json(f"/api/sessions/{session_id}/complete", {"status": "completed"})
    post_json("/api/orchestrate/compile", {"session_id": session_id})

    try:
        os.remove(get_session_file())
    except OSError as e:
        log_debug(f"Arquivo de sessão já removido ou não existe: {e}")

    print(f"Sessão encerrada: {session_id}")


def cmd_status():
    current = load_session()
    if current:
        print(json.dumps(current, indent=2))
    else:
        print("Nenhuma sessão ativa.")


def cmd_cleanup():
    """Limpa todas as sessões fantasmas (orphaned sessions)."""
    import glob
    cleaned = 0
    for f in glob.glob(f"{SESSION_DIR}/*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            pid = data.get("pid")
            if pid and not is_pid_alive(pid):
                os.remove(f)
                cleaned += 1
        except (OSError, json.JSONDecodeError) as e:
            log_debug(f"Erro ao limpar sessão {f}: {e}")
    print(f"Limpas {cleaned} sessões órfãs.")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "end":
            cmd_end_session()
            return
        elif cmd == "status":
            cmd_status()
            return
        elif cmd == "cleanup":
            cmd_cleanup()
            return

    raw = sys.stdin.read().strip()
    if raw:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            log_error(f"JSON inválido: {raw[:100]}")
            event = {"hook_event_name": "unknown"}
    else:
        event = {"hook_event_name": "session_start"}

    process_claude_event(event)


if __name__ == "__main__":
    main()
