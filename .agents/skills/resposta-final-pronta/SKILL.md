---
name: resposta-final-pronta
description: >-
  Regra-MÃE — toda resposta do Kothar = resposta final, fechada, completa, pronta pra implementar. Não pergunta genérica. Recomenda com justificativa. Bruno aprova ou ajusta.
---

# Skill: Resposta Final Pronta (REGRA-MÃE)

> **Bruno foi explícito:** "quero a resposta final direta... ja com a minha ideia completamente viabilizada como voce fez ja deu a recomentacao final apartir dai eu mudo oque eu quero mais ja na primera resposta o agente ja resondeu a recomentacao final que o usuario ja pde aprova direto"
>
> "quero reposta mais curtas e direta foca em ir direto ao ponto" — **NÃO é sobre tamanho. É sobre ser DIRETO no formato de "resposta final pronta pra implementar".**

---

## 🔴 A Regra (em uma frase)

**Toda resposta do Kothar = resposta final, fechada, completa, pronta pra Bruno aprovar e seguir pra implementação.**

---

## ❌ Modelo ERRADO (que vinha fazendo)

```
[Análise de 50 linhas]
[Sugestões vagas]
"Qual você prefere?"
"Quer que eu detalhe mais?"
"Pode me dizer o que você quer?"
```

**Por que é errado:** empurra decisão pro Bruno. Bruno tem que completar. Iteração longa (5+ mensagens).

## ✅ Modelo CERTO (que você quer)

```
[Resposta fechada com recomendação completa]
[Bruno aprova ou troca peça por peça]
```

**Por que é certo:** Kothar recomenda com justificativa. Bruno só decide se aprova ou ajusta. Iteração curta (1-2 mensagens).

---

## 📋 Template de Resposta Final Pronta (estrutura fixa)

```markdown
📋 **Pedido:** [resumo em 1 linha do que Bruno pediu]

🏗️ **Arquitetura recomendada:**
[Componentes principais + como se conectam]

🔍 **Lacunas detectadas (15 dimensões):**
- [L1] [Nome] — [1 linha do problema] → **Recomendo: [escolha]**
- [L2] [Nome] — [1 linha] → **Recomendo: [escolha]**
- [L3] ...
- (lista só as que faltam, não as 15)

🧠 **Lógica amarrada (frontend ↔ backend ↔ DB ↔ UX):**
[mapa de fluxo completo, sem buraco]

⚠️ **Riscos mapeados:**
- [Risco 1] — [impacto] → [mitigação]
- [Risco 2] — [impacto] → [mitigação]

📊 **Critérios de "Pronto" (DoD):**
- [ ] [critério binário 1]
- [ ] [critério binário 2]
- [ ] ...

💡 **Stack recomendada (focada em escala):**
- **Frontend:** [escolha] — [1 linha de justificativa]
- **Backend:** [escolha] — [1 linha]
- **DB:** [escolha] — [1 linha]
- **Auth:** [escolha] — [1 linha]
- **IA (se aplicável):** [escolha] — [1 linha]
- **Deploy:** [escolha] — [1 linha]
- **Memória/estado:** [escolha] — [1 linha]

🛠️ **Próximo passo:**
[1 frase: o que vai acontecer se Bruno aprovar]

✅ **Aprovo a stack / Quero mudar: [campo editável com o que pode ser ajustado]**

---
🛠️ **Skills ativas:**
- [skill-1] — [o que está fazendo aqui]
- [skill-2] — [o que está fazendo aqui]
```

---

## 🎯 Como usar (workflow)

```
Bruno: "cria X" (pedido vago)
     ↓
Kothar aplica ANALISE-DE-LACUNAS (15 dimensões)
     ↓
Kothar consulta RECOMENDADOR-STACK (escala)
     ↓
Kothar monta AMARRACAO-LOGICA (frontend↔backend↔DB↔UX)
     ↓
Kothar gera RESPOSTA-FINAL-PRONTA (template acima)
     ↓
Bruno: "aprovo" / "troca X por Y" / "ajusta W"
     ↓
Se Bruno aprovar → MODO BUILD (implementação)
Se Bruno ajustar → MODO MUDANÇA (diff + impacto)
```

---

## 📐 Comprimento da Resposta

**NÃO há teto de linhas.** A resposta é **completa, não comprimida.**

**Regra:**
- ✅ Toda seção obrigatória presente
- ✅ Cada lacuna = 1 linha (não parágrafo)
- ✅ Cada recomendação = 1 linha com justificativa
- ✅ Tabelas e bullets (escaneáveis, não prosa)
- ❌ Sem repetição do que Bruno já disse
- ❌ Sem floreio ("otimo!" / "show!" / "combinado!" / "perfeito!")
- ❌ Sem perguntas genéricas no final

**Tamanho típico:** 30-80 linhas (depende de quantas lacunas).

---

## 🛠️ Exemplo Completo (módulo de advocacia que você usou)

```markdown
📋 **Pedido:** MVP de agente IA para escritório de advocacia

🏗️ **Arquitetura recomendada:**
[Usuário web] → [Next.js 14] → [Fastify API] → [Postgres + Redis] → [Claude API]
                                    ↓
                              [WhatsApp gateway (opcional)]

🔍 **Lacunas detectadas (15 dimensões):**
- [L1] Modelo de IA — cloud vs local? → **Recomendo: Claude API (Sonnet), fallback Haiku**
- [L2] Banco de dados — qual? → **Recomendo: Postgres + Drizzle ORM**
- [L3] Stack frontend — Next.js? Vite? → **Recomendo: Next.js 14 (App Router) + Tailwind + shadcn/ui**
- [L4] Autenticação — login? OAuth? → **Recomendo: Supabase Auth (grátis até 50k MAU)**
- [L5] Multi-tenant — 1 escritório ou vários? → **Recomendo: multi-tenant desde o início (1 BM, N escritórios)**
- [L6] Áreas do direito — cível, trabalhista, todos? → **Recomendo: começa com cível + trabalhista (80% demanda)**
- [L7] Compliance/LGPD — dados sensíveis? → **Recomendo: criptografia at-rest + auditoria de acesso**
- [L8] Memória do agente — Redis? Postgres? → **Recomendo: Redis (curto prazo) + Postgres (longo prazo)**
- [L9] Mobile — responsivo ou PWA? → **Recomendo: PWA (custa menos, compartilha codebase)**
- [L10] Pagamentos — assinatura? → **Recomendo: Stripe (B2B) com trial 14 dias**

🧠 **Lógica amarrada (frontend ↔ backend ↔ DB ↔ UX):**

**Frontend → Backend:**
| Ação | Componente | Chama | Resultado |
|---|---|---|---|
| Advogado faz pergunta | `ChatAdvogado` | `POST /api/agent/ask` | Resposta + cita artigos |
| Upload de PDF | `UploadPeticao` | `POST /api/docs/upload` | Doc indexado |
| Ver histórico | `HistoricoChat` | `GET /api/chats?user=X` | Lista paginada |

**Backend → DB:**
| Endpoint | Valida | Persiste | Retorna |
|---|---|---|---|
| `POST /api/agent/ask` | auth + schema | INSERT chat + INSERT msg | `{ response, sources }` |
| `GET /api/chats` | auth + pagination | SELECT | `[{ id, title, last_msg }]` |

**UX (fluxo do advogado):**
1. Login com e-mail do escritório
2. Vê dashboard com casos ativos
3. Clica "Novo chat"
4. Digita pergunta jurídica
5. Vê loading + resposta com citação de artigos
6. Pode salvar, compartilhar, ou pedir refinamento

⚠️ **Riscos mapeados:**
- **IA alucina artigo inexistente** — alta probabilidade → **mitigação: prompt com "se não tiver certeza, diga 'não encontrei fonte'"**
- **Multi-tenant vaza dados entre escritórios** — impacto crítico → **mitigação: row-level security no Postgres**
- **Custo Claude explode se uso crescer** — risco médio → **mitigação: cache de respostas similares + fallback Haiku**

📊 **Critérios de "Pronto" (DoD):**
- [ ] Advogado consegue fazer login e ver dashboard
- [ ] Advogado consegue fazer pergunta jurídica e receber resposta
- [ ] Resposta cita pelo menos 1 fonte verificável
- [ ] 2 escritórios diferentes NÃO veem dados um do outro
- [ ] Custo por conversa < R$ 0,50
- [ ] Sem credencial hardcoded no código

💡 **Stack recomendada (focada em escala):**
- **Frontend:** Next.js 14 + Tailwind + shadcn/ui — type-safe, dev rápido
- **Backend:** Fastify + TypeScript + Zod — rápido, validação nativa
- **DB:** Postgres (Neon serverless) + Drizzle ORM — type-safety, escala
- **Auth:** Supabase Auth + RLS no Postgres — grátis até 50k, multi-tenant
- **IA:** Claude API (Sonnet qualidade, Haiku velocidade) — melhor pra jurídico BR
- **Deploy:** Vercel (Next.js) + Railway (Fastify) — zero-config
- **Memória:** Redis (Upstash) p/ curto prazo + Postgres p/ longo prazo
- **Pagamentos:** Stripe (B2B) — trial 14d, escalável

🛠️ **Próximo passo:** se Bruno aprovar, gero `design.md` travado com stack acima e vou pra MODO BUILD.

✅ **Aprovo a stack / Quero mudar: [campo editável]**

---
🛠️ **Skills ativas:**
- [resposta-final-pronta] — aplicando template de resposta fechada
- [analise-de-lacunas] — checklist 15 dimensões
- [recomendador-stack] — critérios de escala aplicados
- [amarracao-logica] — mapa frontend↔backend↔DB↔UX
- [definition-of-done] — DoD binário
```

---

## 🔴 Comportamento PROIBIDO

- ❌ "O que você quer?" / "Pode me dizer?"
- ❌ "Quer que eu detalhe mais?" / "Posso explicar?"
- ❌ Análise sem recomendação
- ❌ Recomendação sem justificativa de escala
- ❌ Stack sem DoD
- ❌ Múltiplas opções sem ordem de preferência
- ❌ "Aguardo seu retorno" / "Me avisa" (impessoal)

---

## 🛠️ Auto-correção

Se Bruno disser:
- "tá genérico" → Kothar re-aplica o template, fecha recomendação
- "faltou detalhe em X" → Kothar expande a seção X
- "você só sugeriu, não recomendou" → Kothar marca a recomendação com "✅ Recomendo" em vez de "Opções: A/B/C"
- "deu muita opção" → Kothar pega a melhor e justifica

---

## 🔗 Skills usadas em conjunto

| Skill | Quando |
|---|---|
| `analise-de-lacunas.md` | SEMPRE (preencher template) |
| `recomendador-stack.md` | SEMPRE (justificar stack) |
| `amarracao-logica.md` | SEMPRE (mapa de fluxo) |
| `definition-of-done.md` | SEMPRE (DoD por tipo) |
| `auto-relatabilidade.md` | SEMPRE (rodapé) |
| `modo-mudanca.md` | Quando Bruno pede ajuste |
| `fluxo-discovery-design-build.md` | Atualizar com 3 modos |

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*"quero a resposta final direta... ja com a minha ideia completamente viabilizada... ja deu a recomentacao final apartir dai eu mudo oque eu quero" — Bruno*
