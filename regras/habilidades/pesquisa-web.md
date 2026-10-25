---
name: pesquisa-web
description: Pesquisar, navegar e extrair conteúdo da web com controle total — busca, scraping e automação de browser
version: 1.0.0
---

# Habilidade: Pesquisa e Navegação Web

## Para que serve

Capacidade de buscar qualquer informação na internet, extrair conteúdo de páginas, automatizar navegação e monitorar dados web. Três camadas de acesso: busca textual, extração de conteúdo e controle real de browser.

---

## Stack de MCPs

### Camada 1 — Busca (sem API key, sempre disponível)
**`open-websearch`** — busca em múltiplos motores e extrai conteúdo

| Ferramenta | Função |
|---|---|
| `search` | Busca em DuckDuckGo, Bing, Brave, Exa |
| `fetchWebContent` | Extrai qualquer URL como Markdown limpo |
| `fetchGithubReadme` | README de qualquer repositório GitHub |

```
Motor padrão: DuckDuckGo
Trocar motor: env DEFAULT_SEARCH_ENGINE=brave
Sem limite de uso, sem API key
```

### Camada 2 — Scraping profissional (Firecrawl — ⚠️ precisa de API key)
**`firecrawl`** — extração avançada com suporte a JS, crawling e mapa de site

| Ferramenta | Função |
|---|---|
| `scrape` | Extrai página única como Markdown |
| `crawl` | Crawla um domínio completo |
| `map` | Descobre todas as URLs de um site |
| `search` | Busca + scraping integrado |
| `extract` | Extração estruturada por schema |
| `interact` | Interage com elementos da página |

```
API key: obter grátis em firecrawl.dev
Tier grátis: suficiente para uso pessoal
```

### Camada 3 — Browser real (BrowserMCP — ⚠️ precisa da extensão Chrome)
**`browser-mcp`** — controle direto do Chrome com sessões reais

| Ferramenta | Função |
|---|---|
| navigate | Navegar para qualquer URL |
| click | Clicar em elementos |
| type | Preencher formulários |
| screenshot | Capturar tela |
| execute_js | Executar JavaScript |
| scroll | Rolar página |
| tab management | Gerenciar abas |

```
Vantagem: reutiliza cookies e sessões abertas no Chrome
Acessa sites com login sem reautenticar
Evita detecção de bot (browser real, não headless)
Extensão: https://browsermcp.io
```

---

## Google Workspace (setup pendente)

O repositório https://github.com/google/mcp aponta para servidores MCP remotos hospedados pelo Google. Após configuração OAuth2:

### O que o Google MCP oferece

**Gmail (10 ferramentas)**
- Buscar threads por query
- Criar rascunhos, aplicar labels
- Ler conversas completas

**Google Drive (8 ferramentas)**
- Buscar arquivos, ler conteúdo
- Criar e copiar documentos
- Gerenciar permissões

**Google Calendar (8 ferramentas)**
- Listar eventos, criar reuniões
- Sugerir horários disponíveis
- Responder convites

**Google Chat, People API, BigQuery, Maps** — disponíveis

### Valor para o Kothar / Ugarit Digital

- Ler emails de clientes e criar tarefas automaticamente
- Criar documentos no Drive a partir de specs
- Agendar reuniões direto do calendário
- Cruzar dados do WhatsApp com email e calendar

### Como configurar (quando necessário)

```bash
# 1. Criar projeto em console.cloud.google.com
# 2. Habilitar APIs: Gmail API, Drive API, Calendar API
# 3. Criar OAuth 2.0 credentials (tipo "Desktop app")
# 4. Baixar client_secret.json

# 5. Instalar gcloud:
sudo snap install google-cloud-cli --classic

# 6. Autenticar:
gcloud auth application-default login

# 7. Adicionar MCPs remotos:
claude mcp add gmail --transport http --scope user https://gmailmcp.googleapis.com/mcp/v1
claude mcp add google-drive --transport http --scope user https://drivemcp.googleapis.com/mcp/v1
claude mcp add google-calendar --transport http --scope user https://calendarmcp.googleapis.com/mcp/v1
```

---

## Fluxo de uso recomendado

```
Pesquisa rápida → open-websearch (search)
Ler artigo/página → open-websearch (fetchWebContent)
Extrair dados estruturados → firecrawl (extract/scrape)
Site com JS pesado → firecrawl (scrape) ou browser-mcp (navigate)
Site com login → browser-mcp (sessão Chrome real)
Email de cliente → Gmail MCP (após setup OAuth)
```

---

## Voltar
← [[catalogo-habilidades]]
