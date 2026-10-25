# Skill Gating

> **Skill:** Kothar Skill Gating  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Dependência:** `skill-workshop.md`  

---

## 🎯 Objetivo

Sistema de gating (habilitar/desabilitar) de skills por projeto, configuração, ou condição.

**Problema resolvido:** Skills são carregadas globalmente, mesmo quando não são relevantes para o projeto atual.

---

## 🎛️ Tipos de Gating

### 1. Gating por Projeto

```yaml
# Configuração por projeto
skill_gating:
  projeto: "disparo-em-massa"
  enabled_skills:
    - frontend-ugarit
    - bug-analyst
    - security
    - ga4
  disabled_skills:
    - cold-email  # Não relevant para disparo
```

### 2. Gating por Configuração

```yaml
# Habilitar skill apenas se bin/env/config existir
skill_gating:
  rules:
    - skill: "cyber-neo"
      requires:
        bins: ["nmap", "sqlmap"]
        
    - skill: "mercadopago-mcp"
      requires:
        env: ["MERCADO_PAGO_TOKEN"]
        
    - skill: "ga4"
      requires:
        config: "GA4_PROPERTY_ID"
```

### 3. Gating por Condição

```yaml
skill_gating:
  rules:
    - skill: "churn-prevention"
      when: "user_has_subscription"
      
    - skill: "ab-testing"
      when: "project_type == 'saas'"
```

---

## 🔧 Lógica de Gating

```
┌─────────────────────────────────────────────────────────────┐
│ SKILL GATING LOGIC                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Load Skills] ──→ [For Each Skill] ──→ [Check Rules]       │
│                                          │                   │
│                                    ┌─────┴─────┐             │
│                                    │           │             │
│                                    ▼           ▼             │
│                              [passou]    [falhou]            │
│                                    │           │             │
│                                    ▼           ▼             │
│                              [carrega]    [ignora]            │
│                                                              │
│  CHECK RULES:                                               │
│  1. Projeto no allowlist?                                    │
│  2. Não no blocklist?                                       │
│  3. Requisitos (bins/env/config) satisfeitos?               │
│  4. Condição (when) é true?                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Implementação

```javascript
class SkillGating {
  constructor(config) {
    this.config = config
    this.rules = config.skill_gating?.rules || []
  }
  
  shouldLoad(skill, context) {
    const project = context.project
    const skillName = skill.name
    
    // 1. Check project allowlist
    const allowedProjects = this.config.allowed_projects?.[skillName]
    if (allowedProjects && !allowedProjects.includes(project)) {
      return { load: false, reason: 'not_in_project_allowlist' }
    }
    
    // 2. Check project blocklist
    const blockedProjects = this.config.blocked_projects?.[skillName]
    if (blockedProjects?.includes(project)) {
      return { load: false, reason: 'in_project_blocklist' }
    }
    
    // 3. Check requirements
    const rule = this.rules.find(r => r.skill === skillName)
    if (rule?.requires) {
      const reqCheck = this.checkRequirements(rule.requires)
      if (!reqCheck.passed) {
        return { load: false, reason: `missing_${reqCheck.missing}` }
      }
    }
    
    // 4. Check condition
    if (rule?.when) {
      if (!this.evaluateCondition(rule.when, context)) {
        return { load: false, reason: 'condition_not_met' }
      }
    }
    
    return { load: true, reason: 'all_checks_passed' }
  }
  
  checkRequirements(requires) {
    if (requires.bins) {
      for (const bin of requires.bins) {
        if (!this.commandExists(bin)) {
          return { passed: false, missing: `bin_${bin}` }
        }
      }
    }
    
    if (requires.env) {
      for (const env of requires.env) {
        if (!process.env[env]) {
          return { passed: false, missing: `env_${env}` }
        }
      }
    }
    
    if (requires.config) {
      if (!this.config[requires.config]) {
        return { passed: false, missing: `config_${requires.config}` }
      }
    }
    
    return { passed: true }
  }
  
  evaluateCondition(condition, context) {
    // Parse and evaluate condition string
    // Example: "project_type == 'saas'"
    try {
      return eval(condition.replace(/context\./g, ''))
    } catch {
      return false
    }
  }
}
```

---

## 📂 Configuração

### Arquivo: `.claude/settings.json`

```json
{
  "kothar": {
    "skill_gating": {
      "default_project": "kothar",
      "allowed_projects": {
        "frontend-ugarit": ["disparo-em-massa", "ratoflix", "bioleads"],
        "bug-analyst": ["disparo-em-massa", "ratoflix"],
        "security": ["*"],  // Todas
        "ga4": ["disparo-em-massa", "bioleads"],
        "mercadopago-mcp": ["disparo-em-massa"]
      },
      "blocked_projects": {},
      "rules": [
        {
          "skill": "cyber-neo",
          "requires": {
            "bins": ["node", "npm"]
          }
        },
        {
          "skill": "mercadopago-mcp",
          "requires": {
            "env": ["MERCADO_PAGO_TOKEN"]
          }
        }
      ]
    }
  }
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `skills list` | Lista todas as skills |
| `skills list --project nome` | Skills do projeto |
| `skills list --loaded` | Só skills carregadas |
| `skills enable nome` | Habilita skill |
| `skills disable nome` | Desabilita skill |
| `skills status nome` | Status de uma skill |

---

## 📊 Output Example

```
$ kothar skills list --project disparo-em-massa

┌────────────────────────┬──────────┬────────────┐
│ Skill                  │ Status   │ Reason     │
├────────────────────────┼──────────┼────────────┤
│ kothar                 │ ✅ LOAD  │ sempre     │
│ frontend-ugarit        │ ✅ LOAD  │ projeto    │
│ bug-analyst            │ ✅ LOAD  │ projeto    │
│ security               │ ✅ LOAD  │ projeto    │
│ ga4                    │ ✅ LOAD  │ projeto    │
│ mercadopago-mcp        │ ✅ LOAD  │ env ok     │
│ cold-email             │ ❌ BLOCK | não projeto│
│ churn-prevention       │ ❌ BLOCK | não projeto│
│ competitor-profiling   │ ❌ BLOCK | não projeto│
└────────────────────────┴──────────┴────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] Skills são filtradas por projeto
- [ ] Requirements (bins/env/config) funcionam
- [ ] Condições (when) são avaliadas
- [ ] Comandos de list/enable/disable funcionam
- [ ] Output é legível e informativo

---

## 🔗 Integração

| Componente | Como usa skill-gating |
|------------|----------------------|
| Kothar init | Filtra skills por projeto |
| Skill Workshop | Proposta só para skills relevantes |
| Memory Search | Prioriza skills do projeto |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
