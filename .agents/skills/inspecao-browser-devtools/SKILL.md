---
name: inspecao-browser-devtools
description: >-
  Skill do Kothar: Inspeção de Browser — Chrome DevTools MCP. Ativar quando necessário para execução da habilidade inspecao-browser-devtools.
---

← [[catalogo-habilidades]]

---
tipo: habilidade
nivel: ferramenta
mcp: chrome-devtools
---

# Inspeção de Browser — Chrome DevTools MCP

> Habilidade que dá ao Kothar **olhos reais** no navegador: abrir sites, inspecionar CSS e animações, tirar screenshots, medir performance. Instalada em 2026-05-31.

## O que é
MCP oficial `chrome-devtools-mcp` (Google/ChromeDevTools) conectado ao Claude Code. Controla o Google Chrome do sistema via Puppeteer. 26 ferramentas de inspeção e automação.

- **Escopo:** user (vale em todos os projetos — não vai pro git)
- **Status:** ✓ Connected · v1.1.1
- **Comando de instalação:** `claude mcp add chrome-devtools -s user -- npx chrome-devtools-mcp@latest`

## Quando usar

### 1. Extrair design de referências (precisão real)
Abrir sites premium (Linear, Jeton, Cuberto, Stripe) e extrair os valores EXATOS:
- Cores (CSS computado), fontes, tamanhos, espaçamentos
- Animações: transições, durações, easings, keyframes
- Screenshots para comparar
→ Alimentar a [[biblioteca-design]] com dados reais, não estimados.

### 2. Debugar UI da Ugarit (não mais "às cegas")
Abrir `localhost:3000`, ver console, rede, e inspecionar por que algo quebrou visualmente. Resolve o problema histórico de corrigir layout sem ver o resultado.

### 3. Validar página criada
Comparar a página da Ugarit lado a lado com a referência. Rodar o [[biblioteca-design|checklist-anti-ia]] vendo de verdade.

### 4. Performance / Core Web Vitals
Medir LCP, CLS, INP — fatores de SEO. Ver traces e gargalos.

## Capacidades
Inspecionar elementos + CSS computado · screenshots · console · requisições de rede · traces de performance · emular mobile/dispositivos · automação (clicar, rolar, preencher, esperar).

## IMPORTANTE
Após instalar ou reconectar o MCP, **reiniciar o Claude Code** para as ferramentas carregarem. Se as tools não aparecem, reiniciar a sessão.

## Relacionado
- [[biblioteca-design]] — onde os achados viram padrão
- Identidade visual: `03_Empresa/Estrategia/identidade-visual/`

## Voltar
← [[catalogo-habilidades]]
