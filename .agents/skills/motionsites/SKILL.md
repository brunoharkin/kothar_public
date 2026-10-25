---
name: motionsites
description: >-
  Skill do Kothar v4.0 para consulta e aplicação de layouts de alta conversão,
  motion design, micro-interações e referências visuais de nível mundial através do MCP MotionSites.
  Ativar quando for criar ou refatorar landing pages, páginas institucionais, componentes interativos,
  animações CSS/Framer Motion, heros, seções de destaque e interfaces premium.
---

# 🌐 Skill: MotionSites (Banco de Referências de Layout & Motion Design)

> **Ugarit Digital — Bruno Harkin**  
> Repositório e motor de referências de UI, micro-interações, layouts modernos e motion design para criação de interfaces de padrão internacional (Awwwards / FWA / Motion UI).

---

## 🎯 Gatilhos de Ativação Automática

Ativar esta skill IMEDIATAMENTE sempre que Bruno solicitar:
- *"busca referências de layout"* / *"pesquisa layout no motionsites"*
- *"cria uma landing page"* / *"desenha a interface da página"*
- *"melhora o design/animação do frontend"* / *"estética premium"*
- *"preciso de referências de hero/navbar/pricing/cards"*
- *"adiciona micro-interações e animações modernas"*
- Em toda fase de **Design** de páginas web no `fluxo-discovery-design-build` ou via `Agente Dev Frontend`.

---

## 🔌 Conexão MCP MotionSites

Configurado no Claude Code e VS Code / Copilot:
- **Transporte:** HTTP (JSON-RPC via POST)
- **Endpoint:** `https://xgdzyqfalbibzelpdpvr.supabase.co/functions/v1/mcp`
- **Autenticação:** OAuth 2.0 (`Bearer` token via Supabase Auth)
- **Servidor de Autorização:** `https://xgdzyqfalbibzelpdpvr.supabase.co/auth/v1`
- **Resource:** `Motionsites.ai`
- **Configuração no Claude CLI:** `claude mcp add --transport http --scope project motionsites https://xgdzyqfalbibzelpdpvr.supabase.co/functions/v1/mcp`
- **Configuração no VS Code:** `.vscode/mcp.json` (`motionsites`)
- **Ativação da Sessão OAuth:** Ao iniciar o Claude Code (`claude`), aceitar a solicitação interativa para autorizar a conexão com a conta Motionsites.ai no navegador.

---

## 🛠️ Capacidades do MotionSites MCP

| Recurso / Ferramenta | O que faz | Aplicação Prática |
| :--- | :--- | :--- |
| **Pesquisa de Layouts** | Busca coleções e templates de páginas premiadas por nicho e categoria | Encontrar arquitetura visual para Landing Pages, SaaS, E-commerce e Clínicas |
| **Componentes de Motion** | Consulta implementações de animações fluidas (entradas, scroll reveal, hover states, magnetismo) | Animar botões, cards, hero text, modais e transições de página |
| **Análise de Tipografia & Cores** | Sugere combinações de fontes de alto contraste e paletas escuras premium | Garantir contraste estrito sem elementos ilegíveis (alinhado a `frontend-ugarit-ui`) |
| **Micro-Interações** | Fornece padrões de feedback háptico/visual imediato para ações do usuário | Estados de loading interativos, toggles dinâmicos e confirmações de formulário |

---

## 📐 Diretrizes de Uso no Ecossistema Ugarit

### 1. Pesquisa Antes do Código
Nunca desenhar telas genéricas ou clichês sem antes consultar referências concretas.
1. Consultar o catálogo do MotionSites para o nicho em questão (ex: B2B SaaS, Farmácia, Saúde, Portfólio).
2. Extrair:
   - Estrutura de grid e hierarquia visual;
   - Ritmo de espaçamento (densidade e respiro);
   - Efeitos de motion com propósito (não animações gratuitas que cansam o usuário).

### 2. Princípios de Motion com Propósito (Anti-Exagero)
- **Duração Máxima:** Micro-interações devem durar entre `150ms` e `300ms`. Animações lentas destroem a percepção de performance.
- **Easing:** Usar curvas suaves (ex: `cubic-bezier(0.16, 1, 0.3, 1)` ou spring physics), nunca `linear` ou easing mecânico.
- **Acessibilidade:** Respeitar sempre `prefers-reduced-motion: reduce`.

### 3. Integração com as Regras de Produção Kothar
- **Zero Framework Bloat:** Implementar animações preferencialmente com Tailwind CSS + CSS transitions nativas, ou Framer Motion otimizado.
- **Zero LocalStorage para Auth:** Mesmo ao renderizar dashboards ou layouts interativos da referência, NUNCA usar `localStorage` para tokens ou credenciais.
- **Estrutura de Pastas PT-BR:** Manter os componentes organizados estritamente em `frontend/componentes/{Nome}/` e `frontend/paginas/{nome}/`.

---

## 🗄️ Banco de Dados Local de Referências & Padrões

Além da conexão remota via MCP, esta skill mantém padrões de referência documentados em:
- `.agents/skills/motionsites/referencias/layouts-premium.md` — Estruturas de páginas validadas
- `.agents/skills/motionsites/referencias/motion-curvas.md` — Tokens de curvas de animação e micro-interações

---

*Ugarit Digital — Bruno Harkin | Kothar v4.0*

