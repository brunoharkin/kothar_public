# Skill: Auto Plan Mode

> **Skill:** Ativação Automática do Modo Plan  
> **Versão:** 1.0  
> **Data:** 2026-08-24  
> **Dependência:** `regras/core/reasoning.md`  

---

## 🎯 Objetivo

Quando Kothar detecta que vai criar/implementar algo, **automaticamente** ativa o modo Plan antes de agir. Este é um gate de qualidade que garante planejamento antes de execução.

## Quando Ativar Automaticamente

```
MODOS QUE ATIVAM PLAN AUTOMATICAMENTE:

1. "cria" / "implementa" / "adiciona" / "construa"
   → Feature nova: ENTERPLANMODE obrigatório

2. "refatora" / "reorganiza" / "migra"
   → Mudança estrutural: ENTERPLANMODE obrigatório

3. "corrige" / "conserta" / "resolve" (bug complexo)
   → Se afeta mais de 2 arquivos: ENTERPLANMODE

4. "projeta" / "desenha" / "arquiteta"
   → Já é modo plan: manter

5. "sincroniza" / "organiza" / "estrutura"
   → Se envolve mais de 1 pasta: ENTERPLANMODE
```

## Template de Ativação

```javascript
// Quando detectar gatilho, injetar automaticamente:

if (isPlanModeTrigger(request)) {
    console.log("🎯 PLANO DETECTADO — Ativando modo Plan...")
    
    // O Agente Plan entra em ação:
    // 1. Analisa o pedido
    // 2. Identifica componentes afetados
    // 3. Cria plano de implementação
    // 4. Retorna para aprovação antes de agir
    
    activatePlanMode(request)
}
```

## Regras do Plano

| Regra | Descrição |
|-------|-----------|
| **Antes de Editar** | Plano deve estar approved |
| **Antes de 3+ arquivos** | Plano detalhado obrigatório |
| **Antes de DB migration** | Plano + backup + rollback |
| **Antes de API pública** | Plano + testes + documentação |

## Checkpoints Integrados

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTO PLAN WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Bruno: "cria sistema de login"                            │
│                      ↓                                       │
│  [DETECTA GATILHO]                                         │
│  → "cria" = feature nova                                  │
│  → "sistema de login" = múltiplos arquivos                │
│                      ↓                                       │
│  ════════════════════════════════════════════════════════   │
│  ║         ENTERPLANMODE ATIVADO                        ║   │
│  ════════════════════════════════════════════════════════   │
│                      ↓                                       │
│  1. Entra em modo Plan                                     │
│  2. Analisa componentes necessários                        │
│  3. Define escopo positivo/negativo                       │
│  4. Identifica dependências                               │
│  5. Cria plano estruturado                                │
│                      ↓                                       │
│  [APRESENTA A BRUNO]                                       │
│  Bruno aprova ou ajusta                                    │
│                      ↓                                       │
│  [SAI DO PLAN MODE]                                       │
│  Volta para modo dev com plano approved                     │
│                      ↓                                       │
│  AGIR com plano em mãos                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Exemplos de Detecção

| Pedido | Ação |
|--------|------|
| "cria endpoint de users" | AUTO → Plan |
| "corrige bug no login" | AUTO → Plan (se >2 arquivos) |
| "faz deploy" | DIRETO (comando) |
| "mostra logs" | DIRETO (leitura) |
| "implementa webhook" | AUTO → Plan |
| "refatora auth" | AUTO → Plan |

## Skill de Detecção

```javascript
const PLAN_TRIGGERS = {
    strong: ['cria', 'implementa', 'adiciona', 'construa', 'projeta', 'desenha'],
    medium: ['refatora', 'migra', 'reorganiza', 'sincroniza', 'estrutura'],
    weak: ['corrige', 'conserta', 'resolve']
}

function shouldActivatePlan(request) {
    const text = request.toLowerCase()
    const words = text.split(' ')
    
    // Strong triggers: sempre plan
    if (PLAN_TRIGGERS.strong.some(t => words.includes(t))) {
        return true
    }
    
    // Medium triggers: plan se envolver +1 arquivo
    if (PLAN_TRIGGERS.medium.some(t => text.includes(t))) {
        return true // Detectar escopo
    }
    
    // Weak triggers: plan se +2 arquivos afetados
    if (PLAN_TRIGGERS.weak.some(t => text.includes(t))) {
        return detectScope() > 2 // Análise de escopo
    }
    
    return false
}
```

## Checkpoint CP6 (do core-loop)

```
Quando Plano é apresentado:
═════════════════════════════════════════════════════
📋 PLANO: [resumo]
🏗️  ARQUITETURA: [componentes]
⚠️  RISCOS: [mapeados]
📊 Dificuldade: [fácil/médio/difícil]

Aprova? (sim/não/editar)
═════════════════════════════════════════════════════
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
