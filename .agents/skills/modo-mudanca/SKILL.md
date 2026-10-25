---
name: modo-mudanca
description: >-
  Quando Bruno pede mudança no design aprovado (trocar banco, framework, auth), Kothar mostra diff + impacto ANTES de aplicar. Design vira vivo, histórico fica registrado.
---

# Skill: Modo Mudança (diff + impacto)

> **Princípio:** quando Bruno pede ajuste no design aprovado, Kothar mostra **o que muda** (diff) + **impacto** (esforço/risco/componentes) ANTES de aplicar. Design vira vivo, com histórico de iterações.
>
> Bruno: "se nao ele vai alterando oque ele quer muda como troca o banco de dados que foi recomentado por outro ir modulando conforme eu solicita mais ele sempre ja estrutura o plano e viabiliza a ideia"

---

## 🔴 Gatilhos (frases do Bruno)

- "troca X por Y"
- "usa Z em vez de W"
- "muda a auth pra Clerk"
- "ao invés de Postgres, usa MongoDB"
- "remove a parte de X"
- "adiciona Y"

---

## 📋 Template de Resposta (diff + impacto)

```markdown
🔄 **Mudança solicitada:** [resumo em 1 linha]

📊 **Diff:**
- **Remover:** [lista do que sai]
- **Adicionar:** [lista do que entra]
- **Modificar:** [lista do que muda]

⚠️ **Impacto:**
- **Esforço:** [horas/dias estimados]
- **Risco:** [baixo / médio / alto]
- **Componentes afetados:** [N arquivos/módulos]
- **Mudança em DB schema?** [sim/não, se sim quais tabelas]
- **Mudança em deploy?** [sim/não, o que muda]
- **Custo:** [diferença em R$/mês, se aplicável]

🛠️ **Plano de aplicação:**
1. [Passo 1]
2. [Passo 2]
3. [Passo 3]

🔗 **Mudanças em cascata (verificar):**
- [dependência 1] — ainda funciona? [sim/não]
- [dependência 2] — ainda funciona? [sim/não]

✅ **Aprovo / Quero ajustar mais**

📝 **Histórico de mudanças do design:**
| Data | Mudança | Motivo | Status |
|---|---|---|---|
| YYYY-MM-DD HH:MM | Original: Next.js + Postgres | Aprovado | ✅ |
| YYYY-MM-DD HH:MM | Troca Postgres por MongoDB | Bruno pediu | 🔄 pendente |
```

---

## 🎯 Como aplicar (workflow)

### Passo 1: Bruno pede mudança
Ex: "troca o banco de Postgres pra MongoDB"

### Passo 2: Kothar PUXA o design.md atual
(não trabalha do zero — trabalha em cima do que já foi aprovado)

### Passo 3: Kothar gera o diff

```markdown
🔄 **Mudança solicitada:** Trocar Postgres por MongoDB

📊 **Diff:**
- **Remover:** Drizzle ORM, migrations SQL, RLS no Postgres
- **Adicionar:** Mongoose, schema NoSQL, índices MongoDB
- **Modificar:** todos os endpoints que faziam query SQL

⚠️ **Impacto:**
- **Esforço:** ~2-3 dias de refactor
- **Risco:** MÉDIO (autenticação, multi-tenant, RLS não tem equivalente direto em Mongo)
- **Componentes afetados:** 8 arquivos
- **Mudança em DB schema?** SIM — não relacional, precisa repensar modelagem
- **Mudança em deploy?** SIM — provisionar MongoDB Atlas (ou self-host)
- **Custo:** +R$ 0 a +R$ 100/mês (Atlas free tier existe)

🛠️ **Plano de aplicação:**
1. Provisionar MongoDB Atlas (free tier)
2. Modelar collections (re-verificar relacionamentos)
3. Substituir Drizzle por Mongoose nos 8 arquivos
4. Atualizar auth (Supabase Auth → Auth0, que tem suporte Mongo)
5. Testar multi-tenant (Mongo não tem RLS nativo — precisa validar no app)

🔗 **Mudanças em cascata (verificar):**
- Autenticação — Supabase Auth tem suporte a Mongo? Verificar
- Memória de longo prazo — mesma modelagem? OK
- Backup — Mongo Atlas tem backup automático, OK

✅ **Aprovo / Quero ajustar mais**

📝 **Histórico de mudanças do design:**
| Data | Mudança | Motivo | Status |
|---|---|---|---|
| 2026-06-10 18:00 | Original: Next.js + Postgres + Drizzle | Aprovado | ✅ |
| 2026-06-10 18:30 | Troca Postgres por MongoDB | Bruno pediu | 🔄 pendente |
```

### Passo 4: Bruno aprova ou pede ajuste

### Passo 5: Kothar aplica a mudança
- Atualiza o design.md (mantém histórico)
- Implementa seguindo o plano
- Valida com DoD

### Passo 6: Adiciona ao histórico do design
Tabela de mudanças cresce a cada iteração.

---

## 🧠 Princípio: Design Vivo

**O design.md NUNCA é estático.** Cada iteração vira entrada na tabela de histórico.

**Por quê:**
- Auditoria (por que mudamos de X pra Y?)
- Rastreabilidade (quando cada peça mudou?)
- Rollback (se mudança der ruim, sabe o que era antes)

---

## 🔴 Comportamento PROIBIDO

- ❌ Aplicar mudança sem mostrar diff
- ❌ Aplicar mudança sem estimar impacto
- ❌ Esquecer de atualizar histórico
- ❌ Mudar 1 coisa e mexer em 5 sem avisar
- ❌ "Já mudei tudo" sem confirmar

---

## 🛠️ Auto-correção

Se Bruno disser:
- "mudou mais do que pedi" → Kothar volta, reverte, pergunta
- "não me avisou do impacto" → Kothar mostra o que mudou
- "esqueceu de atualizar o design" → Kothar corrige

---

## 🔗 Skills usadas em conjunto

- `resposta-final-pronta.md` — primeiro design usa esse template
- `principio-menor-escopo.md` — mudança = escopo do Bruno, nada além
- `definition-of-done.md` — DoD aplicado após mudança
- `micro-rotinas.md` — R4 (registrar decisão) captura a mudança

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*"ir modulando conforme eu solicita... ele sempre ja estrutura o plano e viabiliza a ideia" — Bruno*
