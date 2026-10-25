# KOTHAR — Scripts e Ferramentas

## 📍 Localização Base
```
~/kothar/
├── scripts/           # Scripts ATIVOS
│   └── archive/       # Scripts ARQUIVADOS (não utilizados)
└── hooks/            # Hooks do Claude Code
```

---

## 🚀 SCRIPTS ATIVOS

### 1. kothar-cli.sh — CLI Principal
**Local:** `~/kothar/scripts/kothar-cli.sh`

CLI principal do Kothar. Ativado pelo comando `k`.

```bash
# Ativar Kothar (mostra banner e contexto)
k

# Ver status
k status

# Health check
k health

# Iniciar/parar gravação de sessão
k start
k stop

# Corrigir problemas
k fix
```

**Aliases configurados:**
```bash
alias k="~/kothar/scripts/kothar-cli.sh"
alias kstatus="~/kothar/scripts/kothar-cli.sh status"
alias khealth="~/kothar/scripts/kothar-cli.sh health"
alias kstart="~/kothar/scripts/kothar-cli.sh start"
alias kstop="~/kothar/scripts/kothar-cli.sh stop"
```

---

### 2. kothar-health.sh — Verificação do Sistema
**Local:** `~/kothar/scripts/kothar-health.sh`

Verifica se o sistema Kothar está 100% funcional.

```bash
# Verificar apenas
~/kothar/scripts/kothar-health.sh check

# Verificar e corrigir automaticamente
~/kothar/scripts/kothar-health.sh fix

# Forçar correção
~/kothar/scripts/kothar-health.sh force-fix
```

**O que verifica:**
- Estrutura de diretórios
- Arquivos core (core-loop, perception, gates, etc)
- Skills/habilidades
- Configuração do Claude Code
- Hooks
- Scripts essenciais
- Segurança SSH

---

### 3. kothar-setup.sh — Setup Inicial
**Local:** `~/kothar/scripts/kothar-setup.sh`

Configura o Kothar pela primeira vez ou após clone.

```bash
~/kothar/scripts/kothar-setup.sh
```

**O que faz:**
1. Configura permissões dos scripts
2. Copia comandos para `~/.claude/commands/`
3. Cria executável `k` em `~/bin/`
4. Adiciona `~/bin` ao PATH no `.bashrc`

---

### 4. kothar-orchestra.sh — Docker Orchestrator
**Local:** `~/kothar/scripts/kothar-orchestra.sh`

Gerencia containers Docker dos projetos.

```bash
# Iniciar projeto com dependências
~/kothar/scripts/kothar-orchestra.sh start <projeto>

# Parar projeto
~/kothar/scripts/kothar-orchestra.sh stop <projeto>

# Status de todos
~/kothar/scripts/kothar-orchestra.sh status all

# Reiniciar
~/kothar/scripts/kothar-orchestra.sh restart <projeto>
```

**Projetos disponíveis:**
| Projeto | Dependências |
|---------|-------------|
| `crm-saphia` | postgres + redis |
| `orby-ia` | postgres + redis |
| `disparo-em-massa` | postgres |
| `chronodesk` | redis |
| `all` | todos |

**Exemplo:**
```bash
# Subir CRM com postgres e redis
~/kothar/scripts/kothar-orchestra.sh start crm-saphia

# Ver status de todos
~/kothar/scripts/kothar-orchestra.sh status all

# Parar todos
~/kothar/scripts/kothar-orchestra.sh stop all
```

---

### 5. kothar-diagnostic.sh — Diagnóstico Completo
**Local:** `~/kothar/scripts/kothar-diagnostic.sh`

Diagnóstico detalhado do sistema com pontuação.

```bash
~/kothar/scripts/kothar-diagnostic.sh
```

**Saída:**
- Score de 0-100
- Verificações de estrutura, hooks, SSH, Git
- Status de serviços

---

### 6. kothar-setup-gemini.sh — Setup Gemini CLI
**Local:** `~/kothar/scripts/kothar-setup-gemini.sh`

Instala o Kothar no Gemini CLI (Antigravity).

```bash
~/kothar/scripts/kothar-setup-gemini.sh
```

**O que faz:**
1. Verifica Node.js >= v20
2. Mostra instruções de instalação do Gemini CLI
3. Copia definição do Kothar para `~/.gemini/antigravity/`
4. Configura comandos customizados

---

## 📦 SCRIPTS ARQUIVADOS

**Local:** `~/kothar/scripts/archive/`

Estes scripts foram arquivados porque não são mais utilizados ou foram substituídos.

| Script | Motivo do Arquivamento |
|--------|------------------------|
| `kothar-welcome.sh` | Funcionalidade duplicada no `kothar-cli.sh` |
| `kothar-ativar.sh` | Duplicado do CLI principal |
| `kothar-auto-start.sh` | Não utilizado |
| `kothar-claude.sh` | Wrapper redundante |
| `kothar-command-wrapper.sh` | Não utilizado |
| `kothar-observer-*.sh` | Sistema de tracing removido |
| `kothar-session-init-complete.sh` | Hook duplicado |
| `kothar-register-gemini.sh` | Substituído por `kothar-setup-gemini.sh` |
| `kothar-watchdog*.sh` | Sistema de watchdog removido |
| `kothar-watchdog-api.py` | API não utilizada |
| `kothar-security-check.sh` | Verificação incorporada no health |
| `kothar-ssh-*.sh` | Scripts SSH isolados |
| `kothar-start-recording.sh` | Recording removido |
| `kothar-stop-recording.sh` | Recording removido |
| `model-router.py` | Não utilizado |
| `prompt-enricher.py` | Não utilizado |
| `context-planner.py` | Não utilizado |
| `error-tracker.py` | Sistema de tracking removido |
| `compressor-memoria.py` | Não utilizado |
| `populate-entity-knowledge.py` | Não utilizado |
| `backup-all.sh` | Backup manual |
| `restore-system.sh` | Não utilizado |
| `transcritor.py` | Não utilizado |
| `false-positive-detector.py` | Não utilizado |

---

## 🪝 HOOKS DO CLAUDE CODE

**Local:** `~/kothar/hooks/`

| Hook | Quando | Função |
|------|--------|--------|
| `kothar-session-init.sh` | sessionStart | Inicializa sessão |
| `credential-scanner.sh` | PostToolUse | Verifica credenciais |
| `kothar-structure-audit.sh` | - | Auditoria de estrutura |

---

## 🔧 RESTAURAÇÃO DE SCRIPTS

Se precisar de um script arquivado:

```bash
# Ver conteúdo antes de restaurar
cat ~/kothar/scripts/archive/<script>

# Restaurar (mover de volta)
mv ~/kothar/scripts/archive/<script> ~/kothar/scripts/

# Executar
~/kothar/scripts/<script>
```

---

## 📝 FLUXO TÍPICO DE USO

```bash
# 1. Ativar Kothar (mostra contexto)
k

# 2. Verificar saúde do sistema (se necessário)
k health

# 3. Corrigir problemas (se necessário)
k fix

# 4. Orquestrar projetos Docker
~/kothar/scripts/kothar-orchestra.sh start crm-saphia

# 5. Diagnosticar problemas
~/kothar/scripts/kothar-diagnostic.sh
```

---

## ❓ AJUDA

Para ajuda com qualquer script:
```bash
# Mostrar ajuda do script
~/kothar/scripts/<script> --help
# ou
~/kothar/scripts/<script> help
```

---

**Kothar v3.0 — Scripts e Ferramentas**
*Ugarit Digital — Bruno Harkin*
