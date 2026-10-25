---
name: analise-de-lacunas
description: Checklist de 15 dimensões que todo pedido vago pode ter escondido. Kothar aplica ANTES de recomendar stack. Lacunas viram bullets no template de resposta-final-pronta.
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: discovery
---

# Skill: Análise de Lacunas

> **Princípio:** antes de recomendar stack ou implementar, Kothar verifica 15 dimensões que podem estar escondidas no pedido. As que faltam viram **lacunas com recomendação**.
>
> Bruno: "tem muitas lacunas como qual modelo vai usar banco de dados que vai usar memoria do agente estrutura qual fremeork vai ser usado"

---

## 🎯 As 15 Dimensões (checklist)

### 1. Modelo de IA (se aplicável)
- Qual modelo? (GPT-4, Claude, Llama, Gemini, local)
- Cloud ou local?
- Custo por token aceitável?
- Resposta rápida (Haiku) ou qualidade (Sonnet)?

### 2. Banco de Dados
- Relacional (Postgres, MySQL) ou NoSQL (MongoDB)?
- Serverless (Neon, Supabase) ou tradicional (VPS)?
- Necessita transações? (Postgres é mais seguro)

### 3. ORM / Query Builder
- Type-safe (Drizzle, Prisma)?
- SQL puro?
- Velocidade de dev vs performance?

### 4. Stack Frontend
- React/Next.js? Vue/Nuxt? SvelteKit? Vanilla?
- SSR (Next.js, SvelteKit) ou SPA (Vite)?
- Tailwind? CSS-in-JS? shadcn/ui?

### 5. Autenticação
- Login com e-mail/senha? Magic link? OAuth (Google/GitHub)?
- Quanto custa em escala? (Supabase Auth, Clerk, Auth0)
- Multi-tenant desde o início?

### 6. Multi-tenancy
- 1 usuário? 1 empresa? N empresas?
- Isolamento de dados (row-level security, schema por tenant)?
- Plano gratuito ou pago por tenant?

### 7. Multi-canal
- Web only? Mobile? WhatsApp? E-mail? Telegram?
- Bot/assistente em mais de 1 lugar?

### 8. Pagamentos
- Gratuito? Freemium? Assinatura? Pay-per-use?
- Stripe? Asaas? Mercado Pago? Pix manual?
- B2B (assinatura mensal) ou B2C (compra única)?

### 9. Deploy
- Vercel (Next.js nativo)? Railway? Fly.io? VPS?
- Docker necessário?
- CI/CD (GitHub Actions)?

### 10. Observabilidade
- Logs estruturados? (Pino, Winston)
- Métricas? (Sentry, DataDog)
- Alertas? (quando algo cai)

### 11. Compliance / LGPD
- Dados sensíveis? (CPF, prontuário, jurídico)
- Criptografia at-rest + in-transit?
- Retenção de dados? (90d? 1 ano? infinito)
- Direito ao esquecimento?
- Servidor no Brasil?

### 12. Mobile
- Responsivo (mesmo código)? PWA? React Native?
- Notificações push?
- App Store (custódia) ou só PWA?

### 13. Memória / Estado
- Curto prazo (Redis, in-memory)
- Longo prazo (Postgres, MongoDB)
- Agente de IA precisa lembrar de conversas passadas?

### 14. UX / Fluxo do Usuário
- Qual é o passo-a-passo do usuário?
- Onde fica loading? Onde aparece erro?
- Estados: vazio, carregando, sucesso, erro
- Mobile-first ou desktop-first?

### 15. Operações / DevOps
- Quem vai manter? (1 dev? equipe?)
- Backup automático?
- Plano de disaster recovery?
- Monitoramento de uptime?

---

## 📋 Como aplicar

### Passo 1: Bruno faz pedido
Ex: "cria MVP de agente pra escritório de advocacia"

### Passo 2: Kothar verifica as 15
Mentalmente, Kothar checa cada uma. As que NÃO foram respondidas viram **lacunas com recomendação**.

### Passo 3: Kothar popula o template
```
🔍 **Lacunas detectadas (15 dimensões):**
- [L1] Modelo de IA — não especificado → **Recomendo: Claude API**
- [L4] Stack frontend — não especificado → **Recomendo: Next.js 14**
- [L5] Autenticação — não especificado → **Recomendo: Supabase Auth**
- (apenas as que faltam)
```

### Passo 4: Bruno aprova ou ajusta
Bruno pode:
- ✅ Aprovar todas as recomendações
- 🔄 Trocar peça por peça ("usa OpenAI em vez de Claude")
- ➕ Adicionar restrição não prevista

---

## 📊 Tabela de "lacunas comuns" + recomendação padrão

| Lacuna | Recomendação padrão (se nada for dito) | Justificativa |
|---|---|---|
| Modelo de IA | Claude API (Sonnet qualidade) | Melhor pra texto longo/PT-BR |
| Banco de dados | Postgres + Drizzle ORM | Type-safe, escala horizontal |
| Frontend | Next.js 14 (App Router) | Mais mercado, dev fácil de contratar |
| UI | Tailwind + shadcn/ui | Customizável, sem lock-in |
| Auth | Supabase Auth + RLS | Grátis até 50k, multi-tenant |
| Deploy | Vercel (Next.js) + Railway (backend) | Zero-config |
| Memória curto prazo | Redis (Upstash) | Serverless, grátis até X |
| LGPD | Criptografia + servidor BR | Compliance obrigatório |
| Pagamentos B2B | Stripe + trial 14d | Padrão de mercado |
| Mobile | PWA | Custa menos que RN |
| Observabilidade | Sentry + logs estruturados | Stack padrão |

**Essas são as defaults. Kothar recomenda com confiança. Bruno pode trocar.**

---

## 🎯 Regra de Ouro

> **Se Bruno não falou, Kothar recomenda com base em escala e mercado.** Não pergunta "o que você quer?". Recomenda com justificativa. Bruno aprova ou troca.

---

## 🔴 Comportamento PROIBIDO

- ❌ Listar 15 dimensões sem recomendar
- ❌ Dizer "depende do que você quer"
- ❌ Apresentar 3 opções sem ranking
- ❌ Pular dimensões importantes por preguiça

---

## 🔗 Skills usadas em conjunto

- `resposta-final-pronta.md` — popula template
- `recomendador-stack.md` — justifica cada recomendação
- `amarracao-logica.md` — completa o mapa
- `definition-of-done.md` — DoD por tipo

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*"tem muitas lacunas como qual modelo vai usar banco de dados que vai usar memoria do agente estrutura qual fremeork vai ser usado" — Bruno*
