# HERMES v1.5.0 — SPEC DE EVOLUÇÃO

> **Versão:** 1.5.0 (rascunho)
> **Data:** 2026-06-25
> **Autor:** Kothar v1.4.0 (análise) + Bruno (aprovação)
> **Status:** RASCUNHO — aguardando aprovação de Bruno

---

## 🎯 OBJETIVO

Transformar o Kothar v1.4.0 em um sistema semi-autônomo **realmente funcional**, onde:
- Os 8 hooks estejam wired e executando
- O Instinct Engine gere insights automaticamente
- O Memory Nudge funcione de verdade
- Os logs sejam usados para métricas
- O sistema seja validado e sem erros

---

## 📊 DIAGNÓSTICO ATUAL (v1.4.0)

### Status por Área

| Área | Maturidade | Status |
|------|------------|--------|
| Arquitetura Core Loop | 90% | ✅ Design sólido |
| Hooks implementados | 100% | ⚠️ Scripts existem mas NÃO WIRED |
| Gates | 50% | ⚠️ Lógica existe, não ativa |
| Checkpoints | 60% | ⚠️ Templates existem, não automáticos |
| Instinct Engine | 20% | 🔴 Captura existe, análise não |
| Memory Nudge | 10% | 🔴 Design existe, zero implementação |
| CLI | 80% | ✅ Funcional |
| Logs/Métricas | 0% | 🔴 Estrutura existe, não usa |
| Skills | 85% | ✅ Bem documentadas |

### GAPs Identificados

| # | GAP | Prioridade | Esforço |
|---|-----|------------|---------|
| 1 | Hooks não wired no settings.json | 🔴 CRÍTICA | 2h |
| 2 | instinct-analyzer.py não existe | 🔴 CRÍTICA | 3h |
| 3 | Memory Nudge não implementado | 🟡 ALTA | 2h |
| 4 | Logs não estão sendo usados | 🟡 ALTA | 1h |
| 5 | CP2 muito verboso | 🟢 MÉDIA | 2h |
| 6 | Tabela de projetos desatualizada | 🟢 BAIXA | 1h |

---

## 🏗️ ARQUITETURA v1.5.0

### Mudanças Estruturais

```
HERMES v1.5.0
├── CORE LOOP (mantém)
│   ├── perception.md
│   ├── reasoning.md
│   ├── gates.md
│   └── checkpoints.md
│
├── HOOKS WIRED (MUDANÇA)
│   ├── pre-bash-guard.sh      → settings.json
│   ├── pre-bash-project.sh    → settings.json
│   ├── pre-bash-ssh.sh        → settings.json
│   ├── post-edit-cred-scan.sh → settings.json
│   ├── post-edit-dod.sh       → settings.json
│   ├── post-tool-instinct.sh  → settings.json
│   ├── session-init.sh        → settings.json
│   └── session-snapshot.sh    → settings.json
│
├── AUTO-MELHORIA (NOVO)
│   ├── instinct-analyzer.py   → NOVO
│   ├── memory-nudge.sh        → NOVO
│   ├── hook-validator.sh      → NOVO
│   └── metrics-dashboard.sh   → NOVO
│
├── CLI EXPANDIDA (MUDANÇA)
│   ├── kothar hooks --verify  → NOVO
│   ├── kothar instincts stats  → NOVO
│   └── kothar nudge [show]    → NOVO
│
└── VALIDATORS (NOVO)
    ├── test-hooks.sh           → NOVO
    ├── test-gates.sh           → NOVO
    └── integration-test.sh     → NOVO
```

---

## 📋 FEATURES A IMPLEMENTAR

### FEATURE 1: Wire Hooks no settings.json

**Arquivos afetados:**
- `~/.claude/settings.json` (adicionar 8 hooks)
- `~/.claude/settings.local.json` (alternativa)

**Hooks a adicionar:**

```json
{
  "hooks": {
    "pre-bash": [
      {
        "name": "kothar-guard",
        "path": "/home/bruno/.kothar/hooks/pre-bash-guard.sh",
        "enabled": true
      },
      {
        "name": "kothar-project",
        "path": "/home/bruno/.kothar/hooks/pre-bash-project.sh",
        "enabled": true
      },
      {
        "name": "kothar-ssh",
        "path": "/home/bruno/.kothar/hooks/pre-bash-ssh.sh",
        "enabled": true
      }
    ],
    "post-edit": [
      {
        "name": "kothar-cred-scan",
        "path": "/home/bruno/.kothar/hooks/post-edit-cred-scan.sh",
        "enabled": true
      },
      {
        "name": "kothar-dod",
        "path": "/home/bruno/.kothar/hooks/post-edit-dod.sh",
        "enabled": true
      }
    ],
    "post-tool-use": [
      {
        "name": "kothar-instinct",
        "path": "/home/bruno/.kothar/hooks/post-tool-instinct-collector.sh",
        "enabled": true
      }
    ],
    "session-start": [
      {
        "name": "kothar-init",
        "path": "/home/bruno/.kothar/hooks/session-init.sh",
        "enabled": true
      }
    ],
    "session-end": [
      {
        "name": "kothar-snapshot",
        "path": "/home/bruno/.kothar/hooks/session-snapshot.sh",
        "enabled": true
      }
    ]
  }
}
```

**Validação:**
- `kothar hooks --verify` testa cada hook
- Script `test-hooks.sh` simula cada tipo de chamada

---

### FEATURE 2: instinct-analyzer.py

**Propósito:** Parsear `raw-events.jsonl`, detectar padrões, gerar instincts pendentes.

**Algoritmo:**

```python
# Pseudocódigo
1. Ler raw-events.jsonl
2. Para cada dia:
   a. Contar tool calls por tipo
   b. Detectar repeated-edits (mesmo arquivo 3+)
   c. Detectar workflows (mesma sequência 5+)
   d. Detectar high-frequency (30+ chamadas)
3. Para cada padrão:
   a. Calcular confiança
   b. Se confiança >= 0.5, gerar YAML
   c. Salvar em pending/
4. Gerar relatório de métricas
```

**Arquivo:** `~/.kothar/scripts/instinct-analyzer.py`

**Testes:**
- Parsear eventos de teste
- Detectar padrões known
- Não gerar falsos positivos

---

### FEATURE 3: Memory Nudge Shell Script

**Propósito:** Implementar os 5 gatilhos do memory-nudge.md

**Gatilhos:**

```bash
# 1. Timer (30 min) — via /loop do Claude Code
# 2. Decisão importante (R4)
# 3. Erro registrado
# 4. Mudança de projeto
# 5. Fim de sessão (session-end hook)
```

**Script:** `~/.kothar/scripts/memory-nudge.sh`

**Fluxo:**
```
1. Verificar estado ~/.kothar/state/nudge-state.json
2. Avaliar cada gatilho
3. Se gatilho ativo E cooldown passou:
   - Mostrar nudge formatado
   - Aguardar resposta
   - Executar ação
   - Atualizar cooldown
```

**Integração com /loop:**
- /loop agora chama `memory-nudge.sh` a cada tick
- Se nudge pendente, exibe automaticamente

---

### FEATURE 4: Logging Ativo

**Propósito:** Fazer os hooks logarem de verdade.

**Mudanças nos hooks:**

```bash
# Em cada hook, adicionar:
LOG_FILE="$HERMES_HOME/logs/hooks-$(date +%Y-%m-%d).jsonl"

log_event() {
    local event="$1"
    local data="$2"
    echo "{\"timestamp\":\"$(date -Iseconds)\",\"hook\":\"$HOOK_NAME\",\"event\":\"$event\",\"data\":$data}" >> "$LOG_FILE"
}
```

**Dashboard:** `~/.kothar/scripts/metrics-dashboard.sh`

```bash
# Mostra:
- Tool calls hoje
- Hooks executados
- Violações detectadas
- Instincts gerados
- Sessões
```

---

### FEATURE 5: CP2 Batch Mode

**Propósito:** Reduzir fricção do CP2.

**Mudança no comportamento:**
- Coletar criações pendentes por 5 minutos OU 3 criações
- Agrupar e pedir 1 aprovação
- Exceções expandidas:
  - `package.json`, `tsconfig.json`, `.gitignore` (já existe)
  - `index.ts`, `index.js`, `types.ts`
  - Arquivos em `node_modules/`, `.next/`, `dist/`
  - Arquivos de lock

**Implementação:**
- Adicionar estado `~/.kothar/state/pending-creations.json`
- CP2 agora é "CP2 batch" com lista formatada

---

### FEATURE 6: Tabela de Projetos Sincronizada

**Propósito:** Manter perception.md atualizado automaticamente.

**Script:** `~/.kothar/scripts/sync-projects.sh`

```bash
# 1. Listar ~/.claude/projects/*/
# 2. Extrair projeto de cada memory/MEMORY.md
# 3. Atualizar perception.md
```

**Gatilho:** A cada session-init E semanalmente via cron

---

### FEATURE 7: kothar hooks --verify

**Propósito:** Validar que todos os hooks estão wireados e funcionais.

**Saída:**

```
╔═══════════════════════════════════════════════════════════════╗
║ HERMES v1.5.0 — Hook Validator                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  pre-bash-guard.sh          ✅ WIRED     ✅ EXECUTA          ║
║  pre-bash-project.sh        ✅ WIRED     ✅ EXECUTA          ║
║  pre-bash-ssh.sh            ✅ WIRED     ⚠️  ERRO (path)     ║
║  post-edit-cred-scan.sh    ✅ WIRED     ✅ EXECUTA          ║
║  post-edit-dod.sh           ✅ WIRED     ⚠️  ERRO (regex)    ║
║  post-tool-instinct.sh      ✅ WIRED     ✅ EXECUTA          ║
║  session-init.sh             ✅ WIRED     ✅ EXECUTA          ║
║  session-snapshot.sh         ✅ WIRED     ✅ EXECUTA          ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  Total: 8 hooks | ✅ 6 OK | ⚠️  2 com warnings              ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🔧 TESTES

### Teste 1: Hooks Integration

```bash
#!/bin/bash
# test-hooks.sh

test_pre_bash_guard() {
    # Teste rm -rf bloqueado
    echo "rm -rf /tmp" | bash pre-bash-guard.sh
    # Deve bloquear
}

test_pre_bash_project() {
    # Teste pwd válido
    cd /home/bruno/Cofre
    echo '{"tool_input":{"command":"pwd"}}' | bash pre-bash-project.sh
    # Deve passar
}

# ... etc
```

### Teste 2: Instinct Analyzer

```bash
# Gerar eventos de teste
echo '{"timestamp":"2026-06-25T10:00:00Z","tool":"Edit","input_preview":"..."}' >> raw-events.jsonl
echo '{"timestamp":"2026-06-25T10:01:00Z","tool":"Edit","input_preview":"..."}' >> raw-events.jsonl
echo '{"timestamp":"2026-06-25T10:02:00Z","tool":"Edit","input_preview":"..."}' >> raw-events.jsonl

# Rodar analyzer
python3 instinct-analyzer.py

# Verificar instinct gerado
ls pending/
```

### Teste 3: Memory Nudge

```bash
# Simular 30min de sessão
touch -d "31 minutes ago" ~/.kothar/state/nudge-state.json

# Rodar nudge
bash memory-nudge.sh

# Verificar se apareceu
```

---

## 📁 ARQUIVOS A CRIAR

| Arquivo | Ação | Prioridade |
|---------|------|------------|
| `~/.kothar/scripts/instinct-analyzer.py` | CRIAR | 🔴 CRÍTICA |
| `~/.kothar/scripts/memory-nudge.sh` | CRIAR | 🔴 CRÍTICA |
| `~/.kothar/scripts/hook-validator.sh` | CRIAR | 🔴 CRÍTICA |
| `~/.kothar/scripts/metrics-dashboard.sh` | CRIAR | 🟡 ALTA |
| `~/.kothar/scripts/sync-projects.sh` | CRIAR | 🟢 MÉDIA |
| `~/.kothar/scripts/test-hooks.sh` | CRIAR | 🔴 CRÍTICA |
| `~/.kothar/scripts/test-gates.sh` | CRIAR | 🟡 ALTA |
| `~/.kothar/scripts/integration-test.sh` | CRIAR | 🟡 ALTA |
| `~/.claude/settings.json` | EDITAR | 🔴 CRÍTICA |

---

## 📁 ARQUIVOS A MODIFICAR

| Arquivo | Mudança | Prioridade |
|---------|---------|------------|
| `~/.kothar/hooks/post-tool-instinct-collector.sh` | Adicionar logging real | 🟡 ALTA |
| `~/.kothar/hooks/session-init.sh` | Logging + sync projects | 🟡 ALTA |
| `~/.kothar/hooks/session-snapshot.sh` | Chamar instinct analyzer | 🟡 ALTA |
| `/home/bruno/Cofre/01_Kothar/core/perception.md` | Atualizar tabela projetos | 🟢 MÉDIA |
| `/home/bruno/Cofre/01_Kothar/core/checkpoints.md` | CP2 batch mode | 🟢 MÉDIA |
| `/home/bruno/.local/bin/kothar` | Novos comandos CLI | 🟡 ALTA |
| `/home/bruno/Cofre/01_Kothar/RELEASE-v1.5.0.md` | Criar release notes | 🟢 MÉDIA |
| `/home/bruno/Cofre/01_Kothar/SPEC.md` | Atualizar spec | 🟢 MÉDIA |

---

## ⏱️ TIMELINE

| Dia | Entregável |
|-----|------------|
| **Dia 1** | settings.json wired + hook-validator.sh + testes |
| **Dia 2** | instinct-analyzer.py + testes |
| **Dia 3** | memory-nudge.sh + integração /loop |
| **Dia 4** | Logging real + metrics dashboard |
| **Dia 5** | CP2 batch + sync projects + CLI |
| **Dia 6** | Integration tests + validação final |
| **Dia 7** | RELEASE v1.5.0 |

---

## ✅ DEFINITION OF DONE

Para cada feature:

- [ ] Código implementado
- [ ] Testes unitários passando
- [ ] Teste de integração passando
- [ ] Documentação atualizada
- [ ] CLI atualizada (se aplicável)
- [ ] Nenhum erro no hook-validator.sh
- [ ] Commit feito

Para o release v1.5.0:

- [ ] Todas as 7 features implementadas
- [ ] Todos os hooks validados
- [ ] Instinct analyzer gerando insights
- [ ] Memory nudge funcionando
- [ ] Logs mostrando dados reais
- [ ] SPEC.md atualizado
- [ ] RELEASE.md criado
- [ ] Snapshot de encerramento

---

## 🎯 SUCESSO v1.5.0

**Métricas:**

| Métrica | Antes | Meta |
|---------|-------|------|
| Hooks wired | 0/8 | 8/8 |
| Instincts gerados/semana | 0 | 5+ |
| Logs записей/dia | 0 | 100+ |
| Nudges executados/semana | 0 | 10+ |
| Erros de implementação | ? | 0 |

---

*Aprovação de Bruno necessária para iniciar implementação.*
