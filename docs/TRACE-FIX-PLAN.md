# 🔧 PLANO DE CORREÇÃO DO TRACE — Kothar v4.0

## Problemas Identificados

### 1. ❌ Nome do Agente Hardcoded
**Arquivos afetados:**
- `claude_hook.py:80` → `"agent_name": "claude_cli"` (sempre o mesmo)
- `gemini_hook.py:59` → `"agent_name": "gemini_cli"` (sempre o mesmo)
- `antigravity_tracer.py:11` → `AGENT_ID = "kothar_maestro"` (sempre o mesmo)

**O que deveria acontecer:** O nome do agente deve ser dinâmico — o nome real do processo/terminal que iniciou.

---

### 2. ❌ Sessões Não São Isoladas
**Problema:** O sistema usa um arquivo de mapeamento `~/.kothar_xxx_sessions.json` que é compartilhado entre todos os terminais.

**O que deveria acontecer:** Cada terminal/processo deve ter sua própria sessão isolada, sem compartilhamento. Se abrir 10 terminais, cada um tem sua sessão separada.

---

### 3. ❌ Arquivo de Log Fixo no Antigravity
**Arquivo:** `antigravity_tracer.py:9`
```python
LOG_FILE = "/home/bruno/.gemini/antigravity/brain/b9a7e6e2-21ef-4dc1-b39b-fe75dbf55bfd/.system_generated/logs/overview.txt"
```

**Problema:** Se esse arquivo não existir, NADA é rastreado. É um path fixo e específico.

---

### 4. ❌ Sessão Encerra Automaticamente
**Problema:** Os hooks têm lógica de "Stop" que tenta finalizar a sessão automaticamente:
- `claude_hook.py:106-111`
- `gemini_hook.py:86-91`

**O que deveria acontecer:** A sessão só deveria encerrar quando o usuário mandar explicitamente.

---

### 5. ❌ Erros Silenciosos
**Problema:** Os hooks têm `except Exception: return None` — erros são completamente silenciosos.
```python
def post_json(endpoint: str, data: dict) -> dict | None:
    try:
        # ...
    except Exception:
        return None  # Ninguém sabe que falhou!
```

---

### 6. ❌ Session Create Não Funciona Corretamente
**Arquivo:** `kothar.sh:199-215`
```bash
if [ "$action" = "create" ]; then
    local agent_name="${2:-Engenheiro Kothar}"  # O $2 pode estar vazio!
```

**Problema:** O argumento pode não estar sendo passado corretamente.

---

## Soluções Propostas

### Correção 1: Nome do Agente Dinâmico

**Novo `claude_hook.py`:**
```python
# Obter nome do processo/terminal
AGENT_NAME = os.environ.get("KOTHAR_AGENT_NAME", os.environ.get("SESSION_NAME", "claude_cli"))

# Na criação da sessão:
"agent_name": AGENT_NAME,
"metadata": {
    "terminal": os.environ.get("TERM", "unknown"),
    "hostname": os.environ.get("HOSTNAME", "unknown"),
    "pid": os.getpid(),
    "claude_session_id": claude_session_id
}
```

**Novo `gemini_hook.py`:**
```python
AGENT_NAME = os.environ.get("KOTHAR_AGENT_NAME", "gemini_cli")
```

---

### Correção 2: Sessões Isoladas por PID/Processo

**Nova estratégia:** Cada processo/cliente cria sua própria sessão e NÃO compartilha com outros.

```python
# Gerar ID único baseado em PID + timestamp + random
def generate_unique_session_id() -> str:
    import uuid
    import time
    return f"session-{os.getpid()}-{int(time.time())}-{uuid.uuid4().hex[:8]}"

# NÃO usar arquivo de mapeamento compartilhado
# Cada chamada cria uma nova sessão se não existir
```

**Arquivo `.current_session` por processo:**
```python
# Cada terminal/process tem seu próprio arquivo de sessão
PROCESS_SESSION_FILE = f"/tmp/kothar_session_{os.getpid()}.json"
```

---

### Correção 3: Arquivo de Log Dinâmico

**Antigravity tracer corrigido:**
```python
# Buscar arquivo de log dinamicamente
def find_log_file():
    import glob
    # Procura em múltiplos locais
    patterns = [
        os.path.expanduser("~/.gemini/antigravity/brain/*/.system_generated/logs/overview.txt"),
        os.path.expanduser("~/.gemini/*/logs/overview.txt"),
        os.path.expanduser("~/.gemini/**/overview.txt"),
    ]
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        if files:
            return files[0]  # Mais recente
    return None
```

---

### Correção 4: Remover Encerra Automático

**Remover lógica de Stop nos hooks:**

```python
# ANTES (errado):
if hook_type == "Stop":
    post_json(f"/api/orchestrate/{kothar_session}/complete", {})
    # ...

# DEPOIS (correto):
# Não fazer nada no Stop - sessão fica ativa até comando explícito
```

---

### Correção 5: Logging de Erros

**Novo `post_json` com logging:**
```python
def post_json(endpoint: str, data: dict) -> dict | None:
    try:
        # ... código existente ...
    except Exception as e:
        # Log para debug
        print(f"[KOTHAR HOOK ERROR] {endpoint}: {e}", file=sys.stderr)
        return None
```

---

### Correção 6: CLI Session Create Corrigido

**Novo `kothar.sh` session create:**
```bash
cmd_session() {
    local action="${1:-}"
    
    if [ "$action" = "create" ]; then
        # Capturar nome do agente de múltiplas fontes
        local agent_name="${2:-}"
        [ -z "$agent_name" ] && agent_name="${KOTHAR_AGENT_NAME:-$(whoami)}"
        [ -z "$agent_name" ] && agent_name="kothar"
        
        # Adicionar info do terminal
        local terminal="${TERM:-unknown}"
        local pid=$$
        
        local res
        res=$(curl -s -X POST "${API_URL}/api/sessions/" \
            -H "Content-Type: application/json" \
            -d "{
                \"agent_name\": \"${agent_name}\",
                \"task_summary\": \"Sessão ${agent_name} - Terminal ${terminal}\",
                \"llm_model\": \"${KOTHAR_MODEL:-unknown}\",
                \"metadata\": {
                    \"terminal\": \"${terminal}\",
                    \"pid\": ${pid},
                    \"hostname\": \"${HOSTNAME:-localhost}\"
                }
            }")
        
        # Salvar sessão no arquivo específico deste terminal
        local session_file="/tmp/kothar_session_${pid}.json"
        echo "$res" > "$session_file"
        echo "$session_file"
    fi
}
```

---

## Arquivos a Serem Modificados

| Arquivo | Modificação |
|---------|-------------|
| `hooks/claude_hook.py` | Nome dinâmico, isolate sessão, remover Stop |
| `hooks/gemini_hook.py` | Nome dinâmico, isolate sessão, remover Stop |
| `scripts/antigravity_tracer.py` | Log dinâmico, isolate sessão |
| `cli/kothar.sh` | Session create corrigido |
| `scripts/trace_live.py` | Suporte a sessões por PID |

---

## ✅ Status das Correções Implementadas

### Fase 1: Hooks Corrigidos ✅
| Arquivo | Correção | Status |
|---------|----------|--------|
| `hooks/claude_hook.py` | Nome dinâmico + isolamento por PID + logging | ✅ Implementado |
| `hooks/gemini_hook.py` | Nome dinâmico + isolamento por PID + logging | ✅ Implementado |
| Removido | Encerra automático | ✅ Removido |

### Fase 2: Antigravity Tracer ✅
| Arquivo | Correção | Status |
|---------|----------|--------|
| `scripts/antigravity_tracer.py` | Busca dinâmica de log | ✅ Implementado |
| `scripts/antigravity_tracer.py` | Isolate sessão por PID | ✅ Implementado |
| `scripts/antigravity_tracer.py` | Logging de erros | ✅ Implementado |

### Fase 3: CLI ✅
| Arquivo | Correção | Status |
|---------|----------|--------|
| `cli/kothar.sh` | Session create corrigido | ✅ Implementado |
| `cli/kothar.sh` | Novos comandos (current, end, list) | ✅ Implementado |
| Help atualizado | Documentação dos novos comandos | ✅ Implementado |

### Fase 4: API ✅
| Arquivo | Correção | Status |
|---------|----------|--------|
| `routers/orchestrate.py` | Endpoint /compile | ✅ Implementado |

---

## Comandos a Serem Adicionados

```bash
# Criar sessão com nome do agente
kothar session create meu_agente

# Ver sessão atual
kothar session current

# Encerrar sessão e gerar relatório
kothar session end

# Listar sessões ativas
kothar sessions
```

---

*Plano gerado para correção do sistema Trace — Kothar v4.0*
