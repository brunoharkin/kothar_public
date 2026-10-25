---
name: timeout-manager
description: >-
  Skill do Kothar: Timeout Manager. Ativar quando necessário para execução da habilidade timeout-manager.
---

# Timeout Manager

> **Skill:** Kothar Timeout Manager  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Dependência:** `hooks-system.md`  

---

## 🎯 Objetivo

Sistema de timeout multi-camada que previne operações de ficarem travadas indefinidamente.

**Problema resolvido:** Kothar trava em operações lentas sem limite de tempo.

---

## 🕐 Camadas de Timeout

```
┌─────────────────────────────────────────────────────────────┐
│ TIMEOUT LAYERS                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ LAYER 4: Session Timeout (2 horas)                  │    │
│  │  - Sessão inteira expira                           │    │
│  │  - Backup de estado antes de morrer               │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ LAYER 3: Idle Timeout (30 minutos)                  │    │
│  │  - Sessão sem atividade expira                      │    │
│  │  - Nudge antes de expirar (5 min warning)          │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ LAYER 2: Tool Timeout (por tipo)                    │    │
│  │  - Cada tool tem seu limite                         │    │
│  │  - Timeout por operação                             │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ LAYER 1: Request Timeout (HTTP provider)            │    │
│  │  - Timeout do provider de IA                       │    │
│  │  - Normalmente 60-120 segundos                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Timeouts por Tool

```javascript
const toolTimeouts = {
  // Tools rápidas (I/O local)
  Read: 30 * 1000,        // 30s
  Write: 60 * 1000,       // 60s
  Edit: 60 * 1000,        // 60s
  
  // Tools médias (processamento)
  Bash: 120 * 1000,       // 2 min
  Agent: 300 * 1000,      // 5 min
  Workflow: 600 * 1000,   // 10 min
  
  // Tools lentas (rede externa)
  WebFetch: 30 * 1000,    // 30s
  WebSearch: 60 * 1000,   // 60s
  
  // Tools especiais
  BashLong: 600 * 1000,   // 10 min (builds, etc)
  BashDangerous: 30 * 1000 // 30s (com allowlist)
}
```

---

## ⏱️ Implementação

```javascript
class TimeoutManager {
  constructor(config) {
    this.config = {
      session: config.sessionTimeout || 2 * 60 * 60 * 1000,  // 2h
      idle: config.idleTimeout || 30 * 60 * 1000,           // 30min
      idleWarning: config.idleWarning || 5 * 60 * 1000,     // 5min antes
      ...config.toolTimeouts
    }
    
    this.sessionStart = Date.now()
    this.lastActivity = Date.now()
    this.activeTimeouts = new Map()
  }
  
  // Atualizar last activity
  touch() {
    this.lastActivity = Date.now()
  }
  
  // Verificar todos os timeouts
  async checkTimeouts() {
    const now = Date.now()
    const issues = []
    
    // Layer 1: Session timeout
    const sessionAge = now - this.sessionStart
    if (sessionAge >= this.config.session) {
      issues.push({
        layer: 'session',
        message: 'Sessão atingiu timeout máximo (2h)',
        action: 'Encerrar sessão com backup'
      })
    }
    
    // Layer 2: Idle timeout
    const idleTime = now - this.lastActivity
    if (idleTime >= this.config.idle) {
      issues.push({
        layer: 'idle',
        message: 'Sessão ociosa por 30min',
        action: 'Encerrar ou nudgar'
      })
    } else if (idleTime >= this.config.idle - this.config.idleWarning) {
      issues.push({
        layer: 'idle_warning',
        message: `Sessão ociosa há ${Math.round(idleTime / 60000)}min`,
        action: 'Nudgar usuário'
      })
    }
    
    // Layer 3: Active operation timeouts
    for (const [id, op] of this.activeTimeouts) {
      const opAge = now - op.startTime
      if (opAge >= op.timeout) {
        issues.push({
          layer: 'operation',
          operation: id,
          message: `Operação ${id} travou há ${Math.round(opAge / 1000)}s`,
          action: 'Cancelar operação'
        })
      }
    }
    
    return issues
  }
  
  // Iniciar timeout para uma operação
  startOperationTimeout(operationId, toolName) {
    const timeout = this.getToolTimeout(toolName)
    
    const timer = setTimeout(() => {
      this.onTimeout(operationId, toolName)
    }, timeout)
    
    this.activeTimeouts.set(operationId, {
      startTime: Date.now(),
      timeout,
      toolName,
      timer
    })
    
    return timer
  }
  
  // Cancelar timeout de uma operação
  cancelOperationTimeout(operationId) {
    const op = this.activeTimeouts.get(operationId)
    if (op) {
      clearTimeout(op.timer)
      this.activeTimeouts.delete(operationId)
    }
  }
  
  // Callback quando timeout expira
  onTimeout(operationId, toolName) {
    log.error(`Timeout: ${toolName}`, { operationId })
    
    // Executar ações
    this.activeTimeouts.delete(operationId)
    
    // Hook de timeout
    hooks.execute('on_tool_timeout', {
      operationId,
      toolName
    })
    
    throw new TimeoutError(`Tool ${toolName} exceeded timeout`)
  }
}
```

---

## ⏰ Timeout Decorator

```javascript
// Decorator para adicionar timeout a qualquer função
function withTimeout(fn, timeoutMs, name = 'anonymous') {
  return async (...args) => {
    const operationId = `${name}_${Date.now()}`
    timeoutManager.startOperationTimeout(operationId, name)
    
    try {
      const result = await Promise.race([
        fn(...args),
        new Promise((_, reject) => 
          setTimeout(() => reject(new TimeoutError(name)), timeoutMs)
        )
      ])
      
      timeoutManager.cancelOperationTimeout(operationId)
      return result
    } catch (error) {
      timeoutManager.cancelOperationTimeout(operationId)
      throw error
    }
  }
}

// Uso
const safeRead = withTimeout(readFile, 30000, 'Read')
const safeBash = withTimeout(executeBash, 120000, 'Bash')
```

---

## 🔔 Notificações

```javascript
// Antes de timeout de idle
const idleWarningNotification = {
  layer: 'idle_warning',
  message: '⏰ Sessão ociosa há 25min. Vou encerrar em 5min se não houver atividade.',
  actions: ['Continuar sessão', 'Encerrar agora', 'Salvar e encerrar']
}

// Timeout de tool
const toolTimeoutNotification = {
  layer: 'operation',
  message: '⏰ Tool travou. Timeout após Xs.',
  actions: ['Esperar mais', 'Cancelar']
}

// Timeout de sessão
const sessionTimeoutNotification = {
  layer: 'session',
  message: '⏰ Sessão atingiu limite de 2h. Salvando estado...',
  actions: ['Salvar e encerrar']
}
```

---

## 📊 Métricas

```javascript
const timeoutMetrics = {
  timeouts_triggered: {
    session: 0,
    idle: 0,
    idle_warning: 0,
    operation: {}
  },
  avg_operation_duration: {},
  slow_tools: [] // Tools que costumam dar timeout
}
```

---

## ✅ DoD (Definition of Done)

- [ ] Timeout de sessão (2h) funciona
- [ ] Timeout de idle (30min) funciona
- [ ] Warning de idle (5min antes) funciona
- [ ] Timeouts por tool são respeitados
- [ ] Timeout pode ser cancelado
- [ ] Métricas são gravadas

---

## 🔗 Integração

| Componente | Como usa timeout-manager |
|------------|------------------------|
| hooks-system | Hooks de timeout |
| fault-tolerance | Cancela em timeout |
| stall-detector | Verifica timeouts |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
