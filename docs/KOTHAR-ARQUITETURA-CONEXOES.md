# KOTHAR - Arquitetura de Conexões

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KOTHAR v3.0                                       │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐  │
│  │   CLAUDE    │     │   GEMINI    │     │         RAG                │  │
│  │   (CLI)     │     │   (CLI)     │     │     (ChromaDB)              │  │
│  │  localhost  │     │ ~/.gemini/   │     │     localhost:8000          │  │
│  └─────────────┘     └─────────────┘     └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1. Conexão KOTHAR ↔ CLAUDE CLI

### Como Funciona

O Kothar **NÃO** se conecta diretamente ao Claude Code via API. Em vez disso:

1. **Claude Code já está instalado** no sistema (`claude` no PATH)
2. **Kothar é o prompt/context** que define como o Claude Code deve se comportar
3. **O hook `kothar-session-init.sh`** executa na inicialização de cada sessão

### Arquivos Relacionados

| Arquivo | Função |
|---------|--------|
| `~/.claude/` | Configuração global do Claude Code |
| `~/.claude/projects/-home-bruno-kothar/` | Memória persistente do Kothar |
| `hooks/kothar-session-init.sh` | Hook de inicialização de sessão |
| `regras/` | Diretivas e habilidades do Kothar |

### Fluxo de Inicialização

```
Claude Code inicia
    │
    ▼
~/.claude/projects/-home-bruno-kothar/CLAUDE.md carregado
    │
    ▼
hooks/kothar-session-init.sh executado
    │
    ├──► Verifica estrutura Kothar
    ├──► Verifica ChromaDB
    └──► Registra início de sessão
    │
    ▼
Kothar está pronto para orquestrar
```

### Memória Persistente

- **Local**: `~/.claude/projects/-home-bruno-kothar/memory/`
- **Arquivos de memória**:
  - `kothar-identity.md` — Identidade
  - `regras-operacionais.md` — Mandamentos
  - `projetos-ativos.md` — Projetos (aprendizado dinâmico)

---

## 2. Conexão KOTHAR ↔ GEMINI CLI

### Como Funciona

O Kothar se integra ao **Google Gemini CLI** através do sistema **Antigravity**:

```
┌─────────────────────────────────────────────────────────┐
│                    GEMINI CLI                           │
│                    (gemini)                             │
│                                                         │
│  ~/.gemini/                                             │
│  ├── antigravity/          ← Kothar registrado aqui     │
│  │   ├── KOTHAR.md        ← Definição do agente       │
│  │   ├── GEMINI.md        ← Configuração              │
│  │   └── mcp_config.json  ← MCP servers               │
│  └── commands/             ← Comandos customizados     │
│      └── kothar.toml      ← /kothar command           │
└─────────────────────────────────────────────────────────┘
```

### Scripts de Instalação/Configuração

| Script | Função |
|--------|--------|
| `scripts/kothar-setup-gemini.sh` | Mostra como instalar Gemini CLI |
| `scripts/kothar-register-gemini.sh` | Registra Kothar no Antigravity |

### Instalação do Gemini CLI

```bash
# Opção 1: Local (sem sudo)
mkdir -p ~/.local/npm-global
npm config set prefix ~/.local/npm-global
npm install -g @google/gemini-cli
export PATH=$HOME/.local/npm-global/bin:$PATH

# Opção 2: Global (com sudo)
sudo npm install -g @google/gemini-cli
```

---

## 3. Fluxo Completo de Inicialização

```
┌─────────────────────────────────────────────────────────────────┐
│                  INICIALIZAÇÃO COMPLETA DO KOTHAR                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Claude Code carrega contexto                                  │
│    - ~/.claude/projects/-home-bruno-kothar/CLAUDE.md            │
│    - Regras de ~/.claude/projects/-home-bruno-kothar/memory/    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Hook de Inicialização (kothar-session-init.sh)               │
│    - Verifica estrutura de diretórios                            │
│    - Verifica ChromaDB                                           │
│    - Verifica configuração MCP                                   │
│    - Verifica portas em uso                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Se Gravação Ativa (.recording existe)                         │
│    - Inicia Observer em background                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Kothar Pronto                                                 │
│    - Aguarda comandos                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Arquivos de Estado

| Arquivo | Função |
|---------|--------|
| `.recording` | Flag indicando gravação ativa |
| `.recording-started` | Timestamp de início da gravação |
| `logs/` | Logs de comandos executados |

---

## 5. Quick Reference

### Iniciar Kothar com Gravação

```bash
# Iniciar gravação
~/kothar/scripts/kothar-start-recording.sh
```

### Parar Gravação

```bash
# Parar gravação
~/kothar/scripts/kothar-stop-recording.sh
```

### Verificar Status

```bash
# Status completo
lsof -i -P -n | grep LISTEN
[ -f ~/kothar/.recording ] && echo "🎬 Gravação ATIVA" || echo "📴 Gravação INATIVA"
```

---

## 6. Portas e Serviços

**Nota**: Portas são verificadas dinamicamente. O Kothar aprende as portas dos projetos conforme trabalha.

---

**Documento atualizado**: Agosto 2026  
**Versão**: Kothar v3.0  
**Ugarit Digital — Bruno Harkin**
