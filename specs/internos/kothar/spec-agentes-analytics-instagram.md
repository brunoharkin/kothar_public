---
tipo: spec
projeto: kothar
modulo: agentes-analytics-instagram
status: aprovada
criado: 2026-06-01
---

# Spec — Agentes (SDR), Analytics (Ads) e Instagram

## Visão

Três novos módulos do Painel do Kothar:

1. **Agentes** — criar e gerenciar agentes de IA. O primeiro é o **SDR**, que se
   vincula a um chip do WhatsApp e qualifica leads, movendo-os para a etapa certa
   do funil. (Decisão 2026-06-01: estrutura completa agora; resposta por IA pluga
   depois.)
2. **Analytics** — metrificar os **anúncios** (Ads): campanhas, demografia
   (idade, gênero), público — via Windsor (Meta Ads / Facebook já conectado).
3. **Instagram** — gerenciar conversas (DMs) e comentários; **visualizar +
   responder** via Instagram Graph API.

## Decisões de arquitetura

- **Leads**: banco de dados (SQLite, `backend/dados/kothar.db`) **+ espelho no
  Cofre** (cada lead também é uma nota em `03_Empresa/Comercial/Pipeline/`).
- **SDR**: vinculado a um chip existente (módulo WhatsApp). Regras de
  qualificação → etapa do funil (E1..E17). Motor de IA é um slot a plugar.
- **Analytics**: backend serve um snapshot de dados de ads (atualizável via
  Windsor). Dashboards de campanha + demografia + público.
- **Instagram**: backend prepara a integração Graph API (token Meta). Painel de
  comentários e DMs com ação de responder.

## Backend (`/home/bruno/kothar/backend/src/`)

```
banco/conexao.ts            — abre SQLite + migrations (agentes, leads)
leads/
  repositorio-leads.ts      — CRUD de leads (etapa, score, qualificado)
  espelho-cofre.ts          — grava/atualiza a nota do lead no Pipeline
  rotas-leads.ts
agentes/
  repositorio-agentes.ts    — CRUD agente (tipo sdr, chip_id, regras JSON, status)
  rotas-agentes.ts
analytics/
  fonte-ads.ts              — snapshot de campanhas + demografia + público
  rotas-analytics.ts
instagram/
  cliente-graph.ts          — chamadas à Graph API (comentários, DMs, responder)
  rotas-instagram.ts
```

## Frontend (`/home/bruno/kothar/frontend/`)

```
paginas/agentes/    — lista, criar SDR, vincular chip, regras do funil
paginas/analytics/  — dashboards de ads (campanhas, idade, gênero, público)
paginas/instagram/  — painel de comentários + DMs (visualizar + responder)
servicos/api-agentes.ts, api-leads.ts, api-analytics.ts, api-instagram.ts
```

Navegação: novo grupo "Operação" com Agentes, Analytics, Instagram.

## Critérios de aceite

1. Criar um agente SDR, vincular a um chip e definir regras → persistido no banco.
2. Criar/mover um lead → reflete na etapa do Funil e espelha nota no Pipeline.
3. Analytics exibe campanhas e demografia (idade/gênero) e público.
4. Instagram lista comentários/DMs e tem ação de responder (estrutura Graph API).
5. `tsc --noEmit` sem erros; rotas 200; console limpo.
