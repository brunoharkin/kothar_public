---
name: recomendador-stack
description: Critérios de recomendação de stack (escala + time-to-market + custo). Tabela de recomendação por cenário. Aplicado em CADA lacuna detectada.
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: discovery
---

# Skill: Recomendador de Stack (focado em escala)

> **Princípio:** toda recomendação de stack passa por 7 critérios objetivos. Sem "depende", sem "você escolhe". Kothar recomenda com justificativa.
>
> Bruno: "focada em escala... as recomentacoes que nao vai deix quebra oque estou fazendo"

---

## 🔴 Os 7 Critérios de Recomendação

**Toda recomendação de stack DEVE ser avaliada por:**

1. **Custo inicial** — grátis até onde? VPS? serverless? 
2. **Time-to-market** — conheço a stack? tem template? docs em PT-BR?
3. **Escala** — 10 usuários? 1k? 100k? aguenta sem reescrever?
4. **Time disponível** — 1 dev solo? equipe? dá pra contratar?
5. **Manutenção** — comunidade ativa? updates? risco de deprecated?
6. **Lock-in** — consigo migrar fácil? open source? vendor lock?
7. **Compliance** — LGPD? dados no Brasil? criptografia?

**Recomendação final = melhor trade-off entre esses 7 critérios pro contexto de Bruno.**

---

## 📊 Tabela de Recomendação por Cenário

### Cenário 1: MVP rápido, 1 dev solo, sem budget
| Camada | Recomendação | Por quê |
|---|---|---|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Mais mercado, dev rápido |
| Backend | Next.js API Routes (mesmo projeto) | Zero infra separada |
| DB | Supabase (Postgres + Auth + Storage) | Grátis até 500MB, escala |
| Auth | Supabase Auth | Incluso |
| Deploy | Vercel | Next.js nativo, grátis até hobby |
| Pagamentos | Stripe (test mode) | Validar modelo sem custo |
| **Custo mensal:** R$ 0 até 500 usuários | — | — |

### Cenário 2: SaaS B2B, multi-tenant, médio porte
| Camada | Recomendação | Por quê |
|---|---|---|
| Frontend | Next.js 14 (App Router) | SSR bom pra SEO + performance |
| UI | Tailwind + shadcn/ui | Customizável, sem lock-in |
| Backend | Fastify + TypeScript + Zod | Rápido, type-safe |
| DB | Postgres (Neon serverless) + Drizzle | Type-safety, escala horizontal |
| Auth | Clerk ou Supabase Auth | Multi-tenant nativo |
| Multi-tenant | Row-level security (RLS) no Postgres | Isolamento garantido |
| Pagamentos | Stripe (B2B) | Subscription nativo |
| Deploy | Vercel (frontend) + Railway (backend) | Zero-config |
| Observabilidade | Sentry + logs estruturados | Stack padrão |
| **Custo mensal:** R$ 100-500 até 1k usuários | — | — |

### Cenário 3: App interno de time (10-50 users)
| Camada | Recomendação | Por quê |
|---|---|---|
| Frontend | Next.js 14 (Vite se preferir) | Simples |
| Backend | Next.js API Routes ou Fastify | Depende do tamanho |
| DB | SQLite (local) ou Postgres (VPS) | Custo zero |
| Auth | NextAuth ou Supabase Auth | Depende |
| Deploy | VPS única (Docker) | Tudo num lugar |
| **Custo mensal:** R$ 50-150 (VPS) | — | — |

### Cenário 4: IA-heavy, 1k+ usuários
| Camada | Recomendação | Por quê |
|---|---|---|
| Frontend | Next.js 14 | Padrão |
| Backend | Fastify (separado do frontend) | IA não satura app |
| DB | Postgres (Neon) | Serverless, escala |
| Cache/fila | Redis (Upstash) | Curto prazo |
| IA (inferência) | Claude API (Sonnet qualidade, Haiku velocidade) | Fallback nativo |
| IA (GPU dedicada) | RunPod / Vast.ai (RTX 3090) sob demanda | Paga por hora |
| Memória longo prazo | Postgres (conversas) | Hist Jur Jur Jur |
| **Custo mensal:** R$ 400-1500 | — | — |

### Cenário 5: Mobile-first, 10k+ usuários
| Camada | Recomendação | Por quê |
|---|---|---|
| Frontend | React Native + Expo | Compartilha codebase |
| UI | Tamagui ou Nativewind | Cross-platform |
| Backend | Fastify + TypeScript | Rápido |
| DB | Supabase (Postgres) | Sync tempo real |
| Auth | Supabase Auth | Incluso |
| Push | Expo Push | Grátis até 1k |
| **Custo mensal:** R$ 500-2000 | — | — |

### Cenário 6: Jurídico / Saúde / Área regulada
| Camada | Recomendação | Por quê |
|---|---|---|
| Servidor | BR (Locaweb VPS, AWS São Paulo) | LGPD |
| DB | Postgres criptografado at-rest | Compliance |
| Logs | Estruturados + auditoria | Rastreabilidade |
| Backup | Diário + 30d retenção | Compliance |
| Auth | MFA obrigatório | Segurança |
| Termo | Aceite + log de consentimento | LGPD |
| **Custo mensal:** R$ 300-1000 (compliance tem custo) | — | — |

---

## 📋 Como aplicar (workflow)

### Passo 1: Bruno faz pedido
Ex: "cria MVP de agente pra advocacia"

### Passo 2: Kothar identifica cenário
- 1 dev solo? (cenário 1 ou 3)
- B2B? (cenário 2)
- IA-heavy? (cenário 4)
- Área regulada? (cenário 6)
- Pode ser múltiplos

### Passo 3: Kothar aplica 7 critérios
Cada camada da stack: 1 linha de justificativa baseada em 1+ dos 7 critérios.

### Passo 4: Kothar popula template de resposta-final-pronta

```markdown
💡 **Stack recomendada (focada em escala):**
- **Frontend:** Next.js 14 + Tailwind + shadcn/ui — time-to-market baixo, dev fácil de contratar
- **Backend:** Fastify + TypeScript + Zod — rápido, type-safe, 1 dev dá conta
- **DB:** Postgres (Neon serverless) + Drizzle — type-safety, escala horizontal
- **Auth:** Supabase Auth + RLS — multi-tenant nativo, grátis até 50k MAU
- **IA:** Claude API (Sonnet) — melhor pra texto jurídico PT-BR
- **Deploy:** Vercel (frontend) + Railway (backend) — zero-config
- **Memória:** Redis (Upstash) p/ curto + Postgres p/ longo — separa concerns
- **Servidor:** BR (Locaweb/AWS SP) — LGPD compliance
- **Custo mensal estimado:** R$ 200-500 até 1k usuários
```

---

## 🔴 Comportamento PROIBIDO

- ❌ Listar opções sem ranking
- ❌ Dizer "depende do que você quer"
- ❌ Recomendar sem justificativa dos 7 critérios
- ❌ Misturar cenários (MVP rápido + IA pesada = stack inconsistente)

---

## 🔗 Skills usadas em conjunto

- `resposta-final-pronta.md` — popula template com stack
- `analise-de-lacunas.md` — identifica qual cenário se aplica
- `amarracao-logica.md` — completa o mapa
- `definition-of-done.md` — DoD inclui "stack está documentada"

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*"recomentacoes... focada em escala" — Bruno*
*"as recomentacoes que nao vai deix quebra oque estou fazendo" — Bruno*
