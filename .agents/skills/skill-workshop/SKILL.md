---
name: skill-workshop
description: >-
  Skill do Kothar: Skill Workshop. Ativar quando necessário para execução da habilidade skill-workshop.
---

# Skill Workshop

> **Skill:** Kothar Skill Workshop  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw `skills workshop` with proposals  

---

## 🎯 Objetivo

Pipeline de proposta/aprovação para criação de skills. Kothar detecta padrões reutilizáveis e propõe skills ao Bruno antes de criar.

**Problema resolvido:** Kothar cria skills erradas, viola escopo, não pergunta antes de criar.

---

## 🔄 Pipeline Completo

```
┌─────────────────────────────────────────────────────────────┐
│ SKILL WORKSHOP PIPELINE                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DETECTAR                                                │
│     Kothar detecta padrão reutilizável 2+ vezes             │
│           │                                                  │
│           ▼                                                  │
│  2. AVALIAR                                                 │
│     Vale a pena criar skill? (score >= 0.7)                 │
│           │                                                  │
│     ┌─────┴─────┐                                           │
│     │           │                                           │
│     ▼           ▼                                           │
│   [sim]       [não] → Descarta, fim                        │
│     │                                                        │
│     ▼                                                        │
│  3. CRIAR PROPOSTA                                          │
│     Gera `propostas/YYYY-MM-DD-proposta-NNN.md`            │
│     Template completo com nome, trigger, conteúdo           │
│           │                                                  │
│           ▼                                                  │
│  4. APRESENTAR AO BRUNO                                     │
│     "Detectei padrão reutilizável. Criar skill X?           │
│      [yes] [edit] [no]"                                    │
│           │                                                  │
│     ┌─────┼─────┐                                           │
│     │     │     │                                           │
│     ▼     ▼     ▼                                           │
│   [yes] [edit] [no]                                        │
│     │     │     │                                           │
│     │     ▼     ▼                                           │
│     │   [Brun0 │                                           │
│     │   edita  │                                           │
│     │   + yes] │                                           │
│     │     │    │                                           │
│     ▼     ▼    ▼                                           │
│  5. APLICAR                                                  │
│     Cria skill em `habilidades/`                            │
│     Atualiza índice                                         │
│           │                                                  │
│           ▼                                                 │
│  6. REGISTRAR                                               │
│     Log da criação                                           │
│     Métrica de skill criada                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Gatilho: Quando Detectar?

### Condição: Padrão Reutilizável 2+ Vezes

```javascript
const patternDetector = {
  // Padrão: mesma ação em contextos similares
  patterns: {
    'criar-modal-qr': {
      count: 0,
      contexts: [],
      trigger: 'usuário cria modal com QR code'
    },
    'validar-input': {
      count: 0,
      contexts: [],
      trigger: 'usuário valida campo de input'
    },
    'persistir-decisao': {
      count: 0,
      contexts: [],
      trigger: 'usuário toma decisão importante'
    }
  },
  
  onAction(action, context) {
    for (const [name, pattern] of Object.entries(this.patterns)) {
      if (matches(action, pattern.trigger)) {
        pattern.count++
        pattern.contexts.push({ action, context, timestamp: now() })
        
        if (pattern.count >= 2) {
          this.proposeSkill(name, pattern)
        }
      }
    }
  }
}
```

### Exemplos de Detecção

| Padrão | Quando Ativa | Exemplo |
|--------|-------------|---------|
| `reutilizar-componente` | Copiou código 2+ vezes | Modal QR copiado 4x |
| `validar-schema` | Validou JSON/schema 2+ vezes | Validação de config |
| `log-decisao` | Logou decisão 2+ vezes | Log de decisão técnica |
| `validar-projeto` | Verificou projeto 2+ vezes | Isolamento validado |

---

## 📝 Template de Proposta

```markdown
---
name: proposta-skill-NNN
type: skill-proposal
created: YYYY-MM-DD HH:MM
status: pending
pattern: nome-do-padrao
confidence: 0-100
---

# Proposta de Skill: [NOME DA SKILL]

## Resumo
[1-2 linhas do que a skill faz]

## Gatilho
[Quando esta skill deve ser ativada]

## Justificativa
[Por que isto merece ser uma skill]

## Detecções
Este padrão foi detectado **X vezes**:
1. [Contexto 1] — [data]
2. [Contexto 2] — [data]

## Conteúdo Proposed

\`\`\`markdown
---
name: [nome-da-skill]
description: [resumo de uma linha]
version: 1.0
created: YYYY-MM-DD
trigger: [quando ativar]
---

# [Nome da Skill]

## Objetivo
[O que faz]

## Quando Usar
[_trigger]

## Como Funciona
[Implementação]

## Exemplos
\`\`\`javascript
// Exemplo 1
\`\`\`

## DoD
- [ ] Critério 1
- [ ] Critério 2
\`\`\`

---

## Aprovação

| Opção | Ação |
|-------|------|
| **yes** | Cria skill conforme proposto |
| **edit** | [Brun0 edita conteúdo, depois yes] |
| **no** | Descarta proposta |

---

*Proposta criada por Kothar v1.3.0 em YYYY-MM-DD*
```

---

## 📂 Estrutura de Diretórios

```
Cofre/01_Kothar/
├── propostas/                    # [NOVO]
│   ├── README.md
│   ├── 2026-06-18-proposta-001.md
│   ├── 2026-06-18-proposta-002.md
│   └── ...
├── habilidades/
│   ├── skill-workshop.md        # [ESTE ARQUIVO]
│   ├── skill-gating.md         # [PRÓXIMO]
│   └── [outras skills...]
└── ...
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `kothar workshop list` | Lista propostas pendentes |
| `kothar workshop inspect N` | Mostra detalhes da proposta N |
| `kothar workshop apply N` | Aplica proposta N |
| `kothar workshop reject N` | Rejeita proposta N |
| `propostas` | Alias para workshop list |

---

## 📊 Status de Propostas

```javascript
const proposalStatus = {
  pending: 'Aguardando aprovação do Bruno',
  approved: 'Aprovada, pronta para aplicar',
  edited: 'Editada por Bruno, pronta para aplicar',
  applied: 'Skill criada com sucesso',
  rejected: 'Rejeitada pelo Bruno',
  expired: 'Expirou (30 dias sem ação)'
}
```

---

## ✅ DoD (Definition of Done)

- [ ] Kothar detecta padrões reutilizáveis automaticamente
- [ ] Proposta é criada com template completo
- [ ] Bruno pode aprovar/editar/rejeitar
- [ ] Skill é criada se aprovado
- [ ] Métricas são registradas
- [ ] Propostas pendentes são listáveis

---

## 🔗 Integração

| Skill | Como usa skill-workshop |
|-------|-------------------------|
| `memory-nudge` | Detecta padrões que merecem memória |
| `fault-tolerance` | Detecta erros recorrentes |
| `command-allowlist` | Detecta comandos repetidos |

---

## ⚠️ Regras de Ouro

1. **Score >= 0.7 para propor.** Não poluir com propostas fracas.
2. **Nunca criar skill sem proposta.** Sempre perguntar primeiro.
3. **Template completo.** Proposta sem conteúdo = rejeita.
4. **Expiração 30 dias.** Propostas velhas são descartadas.

---

## 📈 Métricas

```javascript
const workshopMetrics = {
  proposals_created: 0,
  proposals_approved: 0,
  proposals_rejected: 0,
  proposals_expired: 0,
  skills_created: 0,
  avg_approval_time: 0, // em horas
  patterns_detected: {} // { pattern_name: count }
}
```

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
