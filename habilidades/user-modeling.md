# User Modeling

> **Skill:** Kothar User Modeling  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** Kothar NousResearch Honcho dialectic user modeling  

---

## 🎯 Objetivo

Sistema de extração e armazenamento de preferências de Bruno automaticamente. Modelo se aprofunda entre sessões.

**Problema resolvido:** Kothar não aprende preferências de Bruno automaticamente.

---

## 🧠 Modelo de Usuário

```typescript
interface UserModel {
  // Identificação
  name: string           // "Bruno Harkin"
  operator: string       // "Founder Ugarit Digital"
  
  // Metadados
  created: string        // YYYY-MM-DD
  updated: string        // YYYY-MM-DD
  version: number        // 1.0, 1.1, etc
  
  // Preferências de comunicação
  communication: {
    responseStyle: 'closed' | 'open' | 'balanced'  // Prefere respostas fechadas?
    detailLevel: 'summary' | 'detailed' | 'comprehensive'
    tone: 'formal' | 'casual' | 'direct'
    language: 'pt-BR' | 'en' | 'mixed'
    metrics: boolean      // Gosta de métricas e números?
    codeFirst: boolean    // Quer ver código antes de teoria?
  }
  
  // Padrões de trabalho
  workflow: {
    discovery: boolean    // Quer discovery antes de implementar?
    design: boolean       // Quer design antes de código?
    approval: 'explicit' | 'implicit' | 'deferred'
    commitStyle: string  // Como prefere commits
  }
  
  // Erros recorrentes
  errorPatterns: {
    pattern: string      // "isolamento de projeto"
    occurrences: number
    lastOccurrence: string
    status: 'aware' | 'corrected' | 'recurring'
  }[]
  
  // Preferências técnicas
  technical: {
    stack: string[]      // ["React", "Node", "PostgreSQL"]
    projects: { [key: string]: string }
    frameworks: string[]
  }
  
  // Histórico de interações
  interactionHistory: {
    date: string
    type: 'approval' | 'rejection' | 'correction' | 'feedback'
    description: string
    extractedPreference: string
  }[]
}
```

---

## 🔄 Ciclo Dialético

```
┌─────────────────────────────────────────────────────────────┐
│ DIALECTIC LOOP                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. INTERACTION                                            │
│     Bruno faz algo: aprova, rejeita, corrige, comenta       │
│              │                                                │
│              ▼                                                │
│  2. EXTRACT                                                 │
│     Kothar extrai preferência do contexto                    │
│              │                                                │
│              ▼                                                │
│  3. EVALUATE                                                │
│     Kothar avalia confiança da extração                     │
│     - Score >= 0.8? → Alta confiança                       │
│     - Score 0.5-0.8? → Média confiança                     │
│     - Score < 0.5? → Baixa confiança                        │
│              │                                                │
│              ▼                                                │
│  4. UPDATE                                                  │
│     Atualiza USER.md com nova preferência                   │
│     Confidence >= 0.8? → Marca como "learned"              │
│              │                                                │
│              ▼                                                │
│  5. CONFIRM (se baixa confiança)                          │
│     Pergunta a Bruno: "Você prefere X?"                    │
│              │                                                │
│        ┌─────┴─────┐                                      │
│        │           │                                        │
│       [sim]     [não]                                     │
│        │           │                                        │
│        ▼           ▼                                        │
│   [Update+]  [Discard+]                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementação

```javascript
class UserModeling {
  constructor(config = {}) {
    this.config = {
      userFile: config.userFile || `${process.env.HOME}/.claude/projects/-home-bruno-kothar/memory/user/USER.md`,
      minConfidence: config.minConfidence || 0.7,
      threshold: config.threshold || 3, // 3 confirmações = learned
      ...config
    }
    
    this.model = this.loadModel()
  }
  
  // Carregar modelo
  loadModel() {
    if (fs.existsSync(this.config.userFile)) {
      return this.parseModel(fs.readFileSync(this.config.userFile, 'utf8'))
    }
    
    return this.createDefaultModel()
  }
  
  // Criar modelo padrão
  createDefaultModel() {
    return {
      name: 'Bruno Harkin',
      operator: 'Founder Ugarit Digital',
      created: new Date().toISOString().split('T')[0],
      updated: new Date().toISOString().split('T')[0],
      version: 1,
      communication: {
        responseStyle: 'balanced',
        detailLevel: 'detailed',
        tone: 'direct',
        language: 'pt-BR',
        metrics: false,
        codeFirst: false
      },
      workflow: {
        discovery: true,
        design: true,
        approval: 'explicit',
        commitStyle: 'direct'
      },
      errorPatterns: [],
      technical: {
        stack: [],
        projects: {},
        frameworks: []
      },
      interactionHistory: []
    }
  }
  
  // Extrair preferência de interação
  extract(interaction) {
    const { type, description, context } = interaction
    
    const extracted = {
      preference: null,
      confidence: 0,
      source: 'interaction',
      timestamp: new Date().toISOString()
    }
    
    switch (type) {
      case 'approval':
        extracted.preference = this.extractFromApproval(description, context)
        extracted.confidence = 0.8
        break
        
      case 'rejection':
        extracted.preference = this.extractFromRejection(description, context)
        extracted.confidence = 0.7
        break
        
      case 'correction':
        extracted.preference = this.extractFromCorrection(description, context)
        extracted.confidence = 0.9
        break
        
      case 'feedback':
        extracted.preference = this.extractFromFeedback(description, context)
        extracted.confidence = 0.5
        break
    }
    
    return extracted
  }
  
  // Extrair de aprovação
  extractFromApproval(description, context) {
    // "Sim, faça isso" → Aprova a abordagem
    // "Go, pode fazer" → Confirmação positiva
    
    if (description.includes('sim') || description.includes('go') || description.includes('faça')) {
      return {
        category: 'workflow',
        key: 'approval',
        value: 'explicit',
        description: 'Confirmação explícita para aprovar ações'
      }
    }
    
    return null
  }
  
  // Extrair de rejeição
  extractFromRejection(description, context) {
    // "não" → Rejeita a abordagem
    // "para" → Pausa ação
    
    if (description.includes('não') || description.includes('para') || description.includes('cancela')) {
      return {
        category: 'workflow',
        key: 'approval',
        value: 'explicit',
        description: 'Precisa de aprovação explícita antes de agir'
      }
    }
    
    // Detectar o que foi rejeitado
    if (context?.proposed) {
      return {
        category: 'communication',
        key: 'detailLevel',
        value: 'summary',
        description: 'Prefere menos detalhes nas propostas'
      }
    }
    
    return null
  }
  
  // Extrair de correção
  extractFromCorrection(description, context) {
    // "corrigir" → Erro cometido
    // "não faça isso" → Não gosta dessa abordagem
    
    if (context?.error) {
      return {
        category: 'errorPatterns',
        key: context.error.type,
        value: context.error.description,
        description: `Erro recorrente: ${context.error.description}`
      }
    }
    
    return null
  }
  
  // Extrair de feedback
  extractFromFeedback(description, context) {
    // Feedback genérico
    if (description.includes('métrica') || description.includes('número')) {
      return {
        category: 'communication',
        key: 'metrics',
        value: true,
        description: 'Gosta de métricas e dados quantitativos'
      }
    }
    
    if (description.includes('código') || description.includes('mostra')) {
      return {
        category: 'workflow',
        key: 'codeFirst',
        value: true,
        description: 'Prefere ver código antes de explicações'
      }
    }
    
    return null
  }
  
  // Atualizar modelo
  update(extracted) {
    if (!extracted.preference) return
    
    const { category, key, value, description } = extracted.preference
    
    // Encontrar histórico
    const historyEntry = {
      ...extracted,
      description
    }
    this.model.interactionHistory.push(historyEntry)
    
    // Atualizar categoria
    if (category === 'errorPatterns') {
      this.updateErrorPattern(key, value, description)
    } else if (this.model[category] && key in this.model[category]) {
      // Atualizar com contagem
      const current = this.model[category][key]
      const count = this.countOccurrences(key, value)
      
      if (count >= this.config.threshold) {
        this.model[category][key] = value
        log.info('User preference learned', { category, key, value, count })
      }
    }
    
    this.model.updated = new Date().toISOString().split('T')[0]
    this.model.version++
    
    this.saveModel()
  }
  
  // Atualizar padrão de erro
  updateErrorPattern(pattern, description, fullDescription) {
    const existing = this.model.errorPatterns.find(e => e.pattern === pattern)
    
    if (existing) {
      existing.occurrences++
      existing.lastOccurrence = new Date().toISOString().split('T')[0]
      existing.status = existing.occurrences >= this.config.threshold ? 'recurring' : 'aware'
    } else {
      this.model.errorPatterns.push({
        pattern,
        description: fullDescription,
        occurrences: 1,
        lastOccurrence: new Date().toISOString().split('T')[0],
        status: 'aware'
      })
    }
  }
  
  // Contar ocorrências
  countOccurrences(key, value) {
    return this.model.interactionHistory.filter(
      h => h.preference?.key === key && h.preference?.value === value
    ).length
  }
  
  // Salvar modelo
  saveModel() {
    const content = this.modelToMarkdown(this.model)
    fs.writeFileSync(this.config.userFile, content)
  }
  
  // Converter para markdown
  modelToMarkdown(model) {
    return `---
name: ${model.name}
operator: ${model.operator}
created: ${model.created}
updated: ${model.updated}
version: ${model.version}
---

# Modelo de Usuário — ${model.name}

## Comunicação

| Preferência | Valor |
|------------|-------|
| Estilo de resposta | ${model.communication.responseStyle} |
| Nível de detalhe | ${model.communication.detailLevel} |
| Tom | ${model.communication.tone} |
| Idioma | ${model.communication.language} |
| Gosta de métricas | ${model.communication.metrics ? '✅ Sim' : '❌ Não'} |
| Código primeiro | ${model.communication.codeFirst ? '✅ Sim' : '❌ Não'} |

## Fluxo de Trabalho

| Preferência | Valor |
|------------|-------|
| Discovery antes de implementar | ${model.workflow.discovery ? '✅ Sim' : '❌ Não'} |
| Design antes de código | ${model.workflow.design ? '✅ Sim' : '❌ Não'} |
| Aprovação | ${model.workflow.approval} |
| Estilo de commit | \`${model.workflow.commitStyle}\` |

## Padrões de Erro

${model.errorPatterns.map(e => `- **${e.pattern}**: ${e.description} (${e.occurrences}x, status: ${e.status})`).join('\n') || '_Nenhum padrão registrado_'}
`
  }
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `model show` | Mostrar modelo atual |
| `model update` | Forçar update |
| `model history` | Ver histórico de interações |
| `model edit` | Editar manualmente |

---

## ✅ DoD (Definition of Done)

- [ ] Extrai preferências de interações
- [ ] Atualiza USER.md automaticamente
- [ ] Confiança é calculada
- [ ] Threshold = 3 para "learned"
- [ ] Padrões de erro são rastreados
- [ ] Bruno pode editar manualmente

---

## 🔗 Integração

| Componente | Como usa user-modeling |
|------------|----------------------|
| memory-nudge | Detecta contexto para modelar |
| dialectic-loop | Ciclo de aprendizado |
| hooks-system | Hooks de interação |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
