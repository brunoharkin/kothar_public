# Memory Nudge System

> **Skill:** Kothar Memory Nudge  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** Kothar NousResearch `periodic nudges`  

---

## 🎯 Objetivo

Sistema de lembretes automáticos que nudga o Kothar (e Bruno) para salvar contexto relevante antes de perdê-lo.

**Problema resolvido:** Kothar perde contexto entre sessões, não lembra erros passados, não salva decisões importantes automaticamente.

---

## ⚙️ 5 Gatilhos de Nudge

### GATILHO 1: Timer (A cada 30min)

```javascript
// Pseudocódigo
if (session_duration >= 30 * 60 * 1000 && !nudged_recently) {
  trigger_nudge("session_review")
  last_nudge = now()
}
```

**Quando ativa:** A cada 30 minutos de conversa.

---

### GATILHO 2: Após Decisão Importante (R4)

```javascript
// Pseudocódigo
if (decision_taken && is_significant(decision)) {
  trigger_nudge("decision_save", { decision, context })
}
```

**Quando ativa:** Após Kothar ou Bruno tomar decisão importante:
- Mudança de arquitetura
- Decisão de negócio
- Priorização de features
- Commit de feature grande
- Deploy

---

### GATILHO 3: Após Erro Registrado

```javascript
// Pseudocódigo
if (error_registered) {
  trigger_nudge("error_lessons", { error_id, lessons })
}
```

**Quando ativa:** Quando Kothar registra um erro em `00_Memoria/Aprendizados/erros/`.

---

### GATILHO 4: Mudança de Projeto

```javascript
// Pseudocódigo
if (current_project !== previous_project) {
  trigger_nudge("project_switch", { from, to })
}
```

**Quando ativa:** Quando contexto muda de projeto (ex: de `disparo-em-massa` para `ratoflix`).

---

### GATILHO 5: Fim de Sessão

```javascript
// Pseudocódigo
if (session_ending && has_uncommitted_context) {
  trigger_nudge("session_save")
}
```

**Quando ativa:** Quando Bruno disser "vamos encerrar" ou sessão atingir timeout.

---

## 🔍 Lógica de "Vale a Pena Salvar?"

Antes de nudgar, Kothar avalia:

```
┌─────────────────────────────────────────────────────────────┐
│ AVALIADOR DE CONTEXTO                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. NOVIDADE?                                               │
│     - Já existe memória similar nos últimos 7 dias?         │
│     - Se sim → baixa prioridade                             │
│                                                              │
│  2. RELEVÂNCIA?                                             │
│     - Afeta decisão futura?                                  │
│     - É erro recorrente?                                    │
│     - É padrão de comunicação do Bruno?                     │
│                                                              │
│  3. PERSISTÊNCIA?                                          │
│     - Vai ser útil na próxima sessão?                       │
│     - Ou é contexto transitório?                             │
│                                                              │
│  SCORE = (novidade × 0.3) + (relevância × 0.4) + (persistência × 0.3) │
│                                                              │
│  Se SCORE >= 0.6 → NUDGE                                   │
│  Se SCORE < 0.6 → Silêncio (a menos que gatilho seja forte) │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 💬 Template de Nudge

### Nudge: Session Review (Timer)

```
---
🧠 NUDGE — Revisão de Sessão

Já estamos há 30min conversando. Tem algo que vale a pena salvar antes de encerrar?

Contexto atual:
- Projeto: [NOME]
- Última decisão: [DESCRIÇÃO]
- Pendências: [LISTA]

[Já salvo:]
- [x] Memória 1
- [x] Memória 2

[Salvar agora?]
- sim → salva resumo da sessão
- não → ignora
- editar → ajusta o que vai salvar
---
```

### Nudge: Decision Save (R4)

```
---
💡 NUDGE — Decisão Importante Detectada

Você acabou de tomar uma decisão importante:

**Decisão:** [RESUMO]
**Impacto:** [CURTO/MÉDIO/LONGO]
**Projeto:** [NOME]

Devo salvar isso como memória?

[salvar] [editar] [não salvar]
---
```

### Nudge: Error Lessons (Após Erro)

```
---
🔴 NUDGE — Erro Registrado

Acabei de registrar o erro #[ID]. Devo extrair lições aprendidas automaticamente?

**Erro:** [TÍTULO]
**Severidade:** [ALTA/MÉDIA/BAIXA]

Ação:
[extrair lições] → cria `erros/YYYY-MM-DD-erro-NNN-lessons.md`
[depois] → lembro você no fim da sessão
---
```

### Nudge: Project Switch

```
---
🔄 NUDGE — Mudança de Projeto

Mudando de **[PROJETO_A]** para **[PROJETO_B]**.

Antes de continuar, devo:
1. Salvar contexto do [PROJETO_A]? [sim/não]
2. Carregar contexto de [PROJETO_B]? [sim/não]
3. Ambos? [sim/não]
---
```

### Nudge: Session Save (Fim)

```
---
📋 NUDGE — Fim de Sessão

Encerrando sessão. Resumo do que não foi salvo:

**Contexto atual:**
- [ITEM 1]
- [ITEM 2]

**Pendências:**
- [ITEM 1]
- [ITEM 2]

[Salvar tudo] [Selecionar] [Descartar]
---
```

---

## 🔧 Implementação

### Estado Interno

```javascript
const memoryNudgeState = {
  last_nudge: null,           // timestamp do último nudge
  nudge_cooldown: 30 * 60,    // 30 minutos entre nudges
  session_start: null,        // início da sessão
  pending_saves: [],           // contextos pendentes
  decisions_since_last_save: [],
  errors_since_last_save: []
}
```

### Integração com Kothar

O Memory Nudge é executado como parte de R3 (Re-ler a cada 30min):

```markdown
## R3: Re-ler a cada 30 min
1. Re-ler Indice-Mestre + estado do projeto
2. ✅ NOVO: Verificar gatilhos de nudge
   - Timer (30min)?
   - Decisão importante?
   - Erro registrado?
   - Mudança de projeto?
3. Se gatilho ativo → avaliar score → nudgar se necessário
```

---

## 📂 Integração com Skills

| Skill | Como usa memory-nudge |
|-------|----------------------|
| `memory-search` | Busca em memórias para decidir se é novo |
| `memory-summarize` | Sumariza contexto antes de salvar |
| `skill-workshop` | Detecta padrões que merecem nudge |

---

## ⚠️ Regras de Ouro

1. **Nunca nudgar sem motivo.** Score >= 0.6 ou gatilho forte.
2. **Sempre dar opções.** Bruno pode aprovar, editar, ou negar.
3. **Respeitar cooldown.** Mínimo 30min entre nudges do mesmo tipo.
4. **Não nudgar no meio de código.** Se Kothar está codando, adiar nudge.

---

## ✅ DoD (Definition of Done)

- [ ] Nudge aparece automaticamente a cada 30min (se timer trigger)
- [ ] Usuário pode aprovar/negar save
- [ ] Memórias são salvas com frontmatter correto
- [ ] Cooldown é respeitado
- [ ] Todos os 5 gatilhos funcionam
- [ ] Nudge não interrompe codificação ativa

---

## 🔗 Referências

- Kothar NousResearch: periodic nudges
- OpenClaw skills: snapshots
- Honcho: user modeling

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
