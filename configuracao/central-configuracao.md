---
tipo: navegacao
nivel: configuracao
---

# Configuração do Kothar e CLIs

## Configurações Ativas dos Agentes

### Gemini CLI (`~/.gemini/settings.json`)
*   **Hooks do Kothar:** ✓ Ativos (`SessionStart` com suppressOutput JSON e injeção em segundo plano via `additionalContext`, `SessionEnd`). Os hooks exclusivos do Claude Code (`PreToolUse`, `PostToolUse`, `Stop`) foram removidos por serem incompatíveis com a arquitetura nativa do Gemini CLI.
*   **Parâmetros de Otimização:**
    *   `defaultApprovalMode`: `"auto_edit"` (Autonomia para ler e editar arquivos; confirmação para Bash/criação)
    *   `enableNotifications`: `true` (Notificações do terminal no sistema operacional)
    *   `model.name`: `"gemini-1.5-flash"` (Alterado; o modelo 3.5-flash atingiu limite de cota no ambiente)
    *   `plan.modelRouting`: `false` (Desativado; o modelo Pro falhava com erro desconhecido neste ambiente)
    *   `autoMemory`: `false` (Desativado para evitar conflitos com o auto-aprendizado do Kothar)

### Claude Code (`~/.claude/settings.json`)
*   **Hooks do Kothar:** ✓ Ativos (`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `Stop`)

---

## MCPs Ativos (Histórico / Pendente Portabilidade)

### Memória e Vault
| MCP | Escopo | Status | Arquivo |
|---|---|---|---|
| `obsidian-mcp-complete` | `~/.claude/settings.json` | ⚠️ Inativo | 66 ferramentas (Pendente portar para Gemini CLI) |
| `youtube-scrap` | `~/.claude/settings.json` | ⚠️ Inativo | `extract-youtube` (Pendente portar para Gemini CLI) |

### Design e UI
| MCP | Escopo | Status | Arquivo |
|---|---|---|---|
| `magic` (21st.dev) | `~/.claude.json` | ⚠️ Inativo | `API_KEY` configurada |

### Copy e Marketing
| MCP | Escopo | Status | Ferramentas |
|---|---|---|---|
| `osp-marketing` | `~/.claude.json` | ⚠️ Inativo | 6 — value map, posicionamento, SEO de copy |
| `scout-intel` | `~/.claude.json` | ⚠️ Inativo | 7 — scout_company, etc. |

### Pesquisa e Navegação Web
| MCP | Escopo | Status | Notas |
|---|---|---|---|
| `open-websearch` | `~/.claude.json` | ⚠️ Inativo | DuckDuckGo/Bing/Brave — porta 7331 |
| `browser-mcp` | `~/.claude.json` | ⚠️ Inativo | Extensão instalada no Chromium 147 |
| `firecrawl` | `~/.claude.json` | ⚠️ Inativo | API key configurada |

---

## Setup Pendente

### 1. Ferramentas de Busca do Sistema (Urgente)
Para maximizar a velocidade de busca do agente no terminal, instale no terminal do Linux:
```bash
sudo apt update && sudo apt install ripgrep fd-find -y
```

### 2. Browser MCP — uso
```bash
# Extensão instalada no Chromium 147 ✓
# Para usar: abrir o Chromium e clicar "Conectar a partir desta aba" na extensão BrowserMCP
# O MCP controla a aba conectada — navegação, cliques, formulários, screenshots
```

### 3. Google Workspace (Gmail + Drive + Calendar)
Requer Google Cloud project com OAuth2. Ver o guia em `01_Kothar/habilidades/pesquisa-web.md`.

```bash
# Adicionar servidores remotos Google (se aplicável):
# gemini mcp add gmail ...
```

---

## Arquivos
`mcp.json` — configuração histórica dos MCPs do projeto

## Voltar
[[agente-kothar]]
