---
name: fault-tolerance
description: >-
  Skill do Kothar: Fault Tolerance. Ativar quando necessário para execução da habilidade fault-tolerance.
---

# Fault Tolerance

> **Skill:** Kothar Fault Tolerance  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw `retry + buffer reset`  

---

## 🎯 Objetivo

Sistema de retry automático com buffer reset e exponential backoff. Garante que operações transient failures se recuperam automaticamente.

**Problema resolvido:** Kothar trava em falhas, não recupera sozinho, não sabe quantas vezes tentou.

---

## 🔄 Retry Loop

```
┌─────────────────────────────────────────────────────────────┐
│ FAULT TOLERANCE LOOP                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Execute Tool]                                             │
│        │                                                    │
│        ▼                                                    │
│  ┌───────────┐                                              │
│  │ Sucesso? │                                              │
│  └─────┬─────┘                                              │
│        │                                                   │
│    ┌───┴───┐                                               │
│    │       │                                               │
│    ▼       ▼                                               │
│  [sim]   [não]                                             │
│    │       │                                                │
│    │       ▼                                                │
│    │  [Incrementa retry_count]                             │
│    │       │                                                │
│    │       ▼                                                │
│    │  [Max retries?] ──sim──→ [Falha total]               │
│    │       │                    │                          │
│    │      não                    │                          │
│    │       │                    ▼                          │
│    │       ▼                    [on_error hook]           │
│    │  [Reset buffers]                                   │
│    │       │                                               │
│    │       ▼                                               │
│    │  [Wait (exponential backoff)]                       │
│    │       │                                               │
│    │       ▼                                               │
│    │  [Retry]                                              │
│    │       │                                               │
│    │       └───────────────┘                              │
│    │                                                    │
│    ▼                                                    │
│  [Done]                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuração

```javascript
const faultToleranceConfig = {
  max_retries: 3,
  base_delay_ms: 1000,    // 1 segundo
  max_delay_ms: 10000,   // 10 segundos
  backoff_multiplier: 2,  // exponential
  jitter: 0.1,           // ±10% de randomness
  
  // Retryable errors
  retryable_errors: [
    'ECONNREFUSED',
    'ETIMEDOUT',
    'ECONNRESET',
    'ENOTFOUND',
    'ENETUNREACH',
    'EHOSTUNREACH',
    '503',              // Service Unavailable
    '502',              // Bad Gateway
    '429',              // Rate Limited
    'network_error',
    'timeout',
    'ECONNABORTED'
  ],
  
  // Non-retryable errors
  non_retryable: [
    '400',              // Bad Request
    '401',              // Unauthorized
    '403',              // Forbidden
    '404',              // Not Found
    '422',              // Unprocessable Entity
    '500',              // Internal Server Error
    'ENOSPC',           // No space left
    'EACCES',           // Permission denied
    'EEXIST'            // File exists
  ]
}
```

---

## 🔢 Exponential Backoff

```javascript
function calculateDelay(attempt, config) {
  // delay = base * (multiplier ^ attempt)
  let delay = config.base_delay_ms * Math.pow(config.backoff_multiplier, attempt)
  
  // Cap at max
  delay = Math.min(delay, config.max_delay_ms)
  
  // Add jitter (±10%)
  const jitterRange = delay * config.jitter
  delay = delay + (Math.random() * jitterRange * 2 - jitterRange)
  
  return Math.round(delay)
}

// Exemplos:
// Attempt 0: 1000ms
// Attempt 1: 2000ms
// Attempt 2: 4000ms
// Attempt 3: 8000ms (capped at 10000ms)
```

---

## 🔁 Buffer Reset

Quando terjadi retry, buffers e resumos em memória são resetados:

```javascript
class ToolExecutor {
  constructor() {
    this.buffers = {
      output: [],
      summaries: [],
      context: []
    }
  }
  
  async execute(tool, params) {
    const attempt = 0
    
    while (attempt <= faultToleranceConfig.max_retries) {
      try {
        const result = await tool.execute(params)
        return this.success(result)
      } catch (error) {
        if (this.shouldRetry(error)) {
          // BUFFER RESET - CRÍTICO!
          this.resetBuffers()
          
          const delay = calculateDelay(attempt, faultToleranceConfig)
          await this.wait(delay)
          
          attempt++
          this.onRetry(attempt, error)
        } else {
          return this.failure(error)
        }
      }
    }
    
    return this.totalFailure(attempt, error)
  }
  
  resetBuffers() {
    // Limpa tudo para evitar output duplicado
    this.buffers.output = []
    this.buffers.summaries = []
    this.buffers.context = []
    
    // Log do reset
    log.info('Buffers resetados para retry', {
      retry_count: this.attempt,
      traceId: this.traceId
    })
  }
}
```

---

## 🔍 Classificação de Erros

```javascript
function classifyError(error) {
  const errorStr = String(error)
  
  // Check se é retryable
  for (const pattern of faultToleranceConfig.retryable_errors) {
    if (errorStr.includes(pattern)) {
      return {
        shouldRetry: true,
        reason: `match_retryable_${pattern}`,
        category: 'transient'
      }
    }
  }
  
  // Check se é non-retryable
  for (const pattern of faultToleranceConfig.non_retryable) {
    if (errorStr.includes(pattern)) {
      return {
        shouldRetry: false,
        reason: `match_non_retryable_${pattern}`,
        category: 'permanent'
      }
    }
  }
  
  // Default: não retry (segurança)
  return {
    shouldRetry: false,
    reason: 'unknown_error_not_retryable',
    category: 'unknown'
  }
}
```

---

## 📊 Métricas

```javascript
const faultToleranceMetrics = {
  total_calls: 0,
  successful_first_try: 0,
  successful_after_retry: 0,
  total_failures: 0,
  retry_distribution: {
    retry_1: 0,
    retry_2: 0,
    retry_3: 0
  },
  error_distribution: {}, // { error_type: count }
  avg_retry_delay_ms: 0
}
```

---

## 🔧 Integração com Hooks

```javascript
// Hooks do fault tolerance
const faultToleranceHooks = {
  before_retry: (attempt, error) => {
    // Log antes de retry
    log.warn(`Retry #${attempt}`, {
      error: error.message,
      delay: calculateDelay(attempt)
    })
  },
  
  after_retry: (attempt, success, result) => {
    // Log após retry
    if (success) {
      log.info(`Recovery after ${attempt} retries`)
    }
  },
  
  on_max_retries: (error) => {
    // Notificar Bruno
    notify('Erro persistente após 3 tentativas', {
      error: error.message,
      context: getCurrentContext()
    })
  }
}
```

---

## ✅ DoD (Definition of Done)

- [ ] Retry automático funciona (max 3 tentativas)
- [ ] Buffer reset executado entre retries
- [ ] Exponential backoff calculado corretamente
- [ ] Erros transient são retryable
- [ ] Erros permanent não são retryable
- [ ] Métricas são gravadas
- [ ] Hooks são chamados nos momentos corretos

---

## 🔗 Integração

| Componente | Como usa fault-tolerance |
|------------|-------------------------|
| Tool Executor | Wraps todas as chamadas |
| Hooks System | before_retry, after_retry, on_max_retries |
| Execution Metrics | Conta retries |
| Stall Detector | Detecta sessões com muitos retries |

---

## 📝 Exemplo de Uso

```javascript
// Antes (sem fault tolerance)
try {
  const result = await tool.execute(params)
  return result
} catch (error) {
  throw error // Falha total
}

// Depois (com fault tolerance)
const result = await withFaultTolerance(async () => {
  return await tool.execute(params)
}, {
  maxRetries: 3,
  onRetry: (attempt, error) => {
    log.warn(`Retry ${attempt}: ${error.message}`)
  },
  onMaxRetries: (error) => {
    notify('Tool falhou permanentemente')
  }
})
```

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
