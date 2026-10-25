---
name: trace-correlation
description: >-
  Skill do Kothar: Trace Correlation. Ativar quando necessário para execução da habilidade trace-correlation.
---

# Trace Correlation

> **Skill:** Kothar Trace Correlation  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw OpenTelemetry + traceId  

---

## 🎯 Objetivo

Sistema de traceId para correlacionar logs e métricas de uma operação específica.

**Problema resolvido:** Não consegue filtrar todos os logs de uma operação.

---

## 🔗 Conceito

```
┌─────────────────────────────────────────────────────────────┐
│ TRACE CORRELATION                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Operation A                                                │
│  ├── traceId: abc123                                        │
│  │   ├── log: "Starting tool"         [traceId=abc123]     │
│  │   ├── log: "Tool params"           [traceId=abc123]     │
│  │   ├── metric: {traceId=abc123}                          │
│  │   └── log: "Tool completed"       [traceId=abc123]     │
│  │                                                          │
│  Operation B                                                │
│  └── traceId: def456                                        │
│      ├── log: "Starting tool"         [traceId=def456]     │
│      └── log: "Tool failed"           [traceId=def456]     │
│                                                              │
│  RESULT: Filtrar por traceId=abc123 → só Operation A        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Formato

```typescript
interface Trace {
  id: string              // traceId
  operations: Operation[] // Lista de operações
  startTime: number
  endTime?: number
  duration?: number
  status: 'active' | 'completed' | 'failed'
  
  // Metadados
  project?: string
  sessionId?: string
  trigger?: string       // 'user_request' | 'scheduled' | 'hook'
}

interface Operation {
  id: string              // spanId
  parentId?: string       // parent spanId (para nested)
  traceId: string
  name: string           // 'Read' | 'Bash' | 'Agent'
  startTime: number
  endTime?: number
  duration?: number
  status: 'active' | 'completed' | 'failed'
  
  // Detalhes
  params?: object        // Redacted
  result?: object
  error?: ErrorInfo
  
  // Nested operations
  children?: Operation[]
}
```

---

## 🔧 Implementação

```javascript
class TraceManager {
  constructor(config = {}) {
    this.config = {
      tracesDir: config.tracesDir || `${process.env.HOME}/.kothar/traces`,
      maxTraces: config.maxTraces || 1000,
      retentionDays: config.retentionDays || 7,
      ...config
    }
    
    this.activeTraces = new Map()
    this.currentTrace = null
    this.currentSpan = null
    
    this.init()
  }
  
  init() {
    fs.mkdirSync(this.config.tracesDir, { recursive: true })
  }
  
  // Gerar traceId
  generateTraceId() {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 16)
  }
  
  // Gerar spanId
  generateSpanId() {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 8)
  }
  
  // Iniciar trace
  startTrace(name, meta = {}) {
    const traceId = this.generateTraceId()
    
    const trace = {
      id: traceId,
      name,
      operations: [],
      startTime: Date.now(),
      status: 'active',
      meta,
      project: currentProject,
      sessionId: getSessionId()
    }
    
    this.activeTraces.set(traceId, trace)
    this.currentTrace = trace
    
    // Injetar no logger
    logger.setTraceId(traceId)
    
    // Injetar nas métricas
    metrics.setTraceId(traceId)
    
    log.info('Trace started', { traceId, name, ...meta })
    
    return traceId
  }
  
  // Iniciar span (operação dentro do trace)
  startSpan(name, meta = {}) {
    const spanId = this.generateSpanId()
    const parentId = this.currentSpan?.id
    
    const span = {
      id: spanId,
      parentId,
      traceId: this.currentTrace?.id,
      name,
      startTime: Date.now(),
      status: 'active',
      meta,
      children: []
    }
    
    if (this.currentTrace) {
      this.currentTrace.operations.push(span)
    }
    
    if (this.currentSpan) {
      this.currentSpan.children.push(span)
    }
    
    this.currentSpan = span
    
    log.debug('Span started', { spanId, traceId: span.traceId, name })
    
    return spanId
  }
  
  // Finalizar span
  endSpan(spanId, result = {}, error = null) {
    const span = this.findSpan(spanId)
    if (!span) {
      log.warn('Span not found', { spanId })
      return
    }
    
    span.endTime = Date.now()
    span.duration = span.endTime - span.startTime
    span.status = error ? 'failed' : 'completed'
    span.result = this.redactResult(result)
    span.error = error ? this.formatError(error) : null
    
    log.debug('Span ended', { 
      spanId, 
      duration: span.duration,
      status: span.status 
    })
    
    // Restaurar parent span
    this.currentSpan = this.activeSpans.get(span.parentId)
    
    return span
  }
  
  // Finalizar trace
  endTrace(traceId, status = 'completed') {
    const trace = this.activeTraces.get(traceId)
    if (!trace) {
      log.warn('Trace not found', { traceId })
      return
    }
    
    trace.endTime = Date.now()
    trace.duration = trace.endTime - trace.startTime
    trace.status = status
    
    // Salvar
    this.saveTrace(trace)
    
    // Limpar
    this.activeTraces.delete(traceId)
    this.currentTrace = null
    this.currentSpan = null
    
    // Limpar do logger
    logger.setTraceId(null)
    metrics.setTraceId(null)
    
    log.info('Trace ended', { 
      traceId, 
      duration: trace.duration,
      status,
      operations: trace.operations.length
    })
    
    return trace
  }
  
  // Buscar span
  findSpan(spanId) {
    if (!this.currentTrace) return null
    
    const search = (spans) => {
      for (const span of spans) {
        if (span.id === spanId) return span
        if (span.children) {
          const found = search(span.children)
          if (found) return found
        }
      }
      return null
    }
    
    return search(this.currentTrace.operations)
  }
  
  // Salvar trace
  saveTrace(trace) {
    const file = `${this.config.tracesDir}/trace-${trace.id}.json`
    fs.writeFileSync(file, JSON.stringify(trace, null, 2))
    
    // Atualizar índice
    this.updateIndex(trace)
  }
  
  // Filtrar logs por traceId
  async getLogsForTrace(traceId) {
    const logs = []
    const logDir = `${process.env.HOME}/.kothar/logs`
    const files = fs.readdirSync(logDir).filter(f => f.endsWith('.jsonl'))
    
    for (const file of files) {
      const content = fs.readFileSync(`${logDir}/${file}`, 'utf8')
      for (const line of content.split('\n')) {
        if (!line.trim()) continue
        const entry = JSON.parse(line)
        if (entry.traceId === traceId) {
          logs.push(entry)
        }
      }
    }
    
    return logs.sort((a, b) => new Date(a.ts) - new Date(b.ts))
  }
  
  // Filtrar métricas por traceId
  async getMetricsForTrace(traceId) {
    const metricsDir = `${process.env.HOME}/.kothar/metrics/sessions`
    const files = fs.readdirSync(metricsDir).filter(f => f.endsWith('.jsonl'))
    
    const metrics = []
    for (const file of files) {
      const content = fs.readFileSync(`${metricsDir}/${file}`, 'utf8')
      for (const line of content.split('\n')) {
        if (!line.trim()) continue
        const metric = JSON.parse(line)
        if (metric.traceId === traceId) {
          metrics.push(metric)
        }
      }
    }
    
    return metrics.sort((a, b) => a.startTime - b.startTime)
  }
  
  // Buscar por traceId
  async get(traceId) {
    const trace = this.activeTraces.get(traceId)
    if (trace) return trace
    
    // Buscar em arquivo
    const file = `${this.config.tracesDir}/trace-${traceId}.json`
    if (fs.existsSync(file)) {
      return JSON.parse(fs.readFileSync(file, 'utf8'))
    }
    
    return null
  }
}
```

---

## 🔧 Decorator de Trace

```javascript
// Decorator para adicionar tracing a qualquer função
function withTrace(fn, name) {
  return async (...args) => {
    const spanId = traceManager.startSpan(name, { args: args.length })
    
    try {
      const result = await fn(...args)
      traceManager.endSpan(spanId, { result })
      return result
    } catch (error) {
      traceManager.endSpan(spanId, {}, error)
      throw error
    }
  }
}

// Uso
const tracedRead = withTrace(readFile, 'Read')
const tracedBash = withTrace(executeBash, 'Bash')
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `kothar trace list` | Lista traces ativos |
| `kothar trace show <id>` | Mostra trace completo |
| `kothar trace logs <id>` | Logs do trace |
| `kothar trace metrics <id>` | Métricas do trace |
| `kothar trace export <id>` | Exporta trace completo |
| `kothar logs --trace-id <id>` | Filtra logs por trace |

---

## 📝 Exemplo de Output

```
$ kothar trace show abc123

┌─────────────────────────────────────────────────────────────┐
│ TRACE abc123 — started 14:30:15                              │
├─────────────────────────────────────────────────────────────┤
│ Name:       "Deploy Ratoflix"                              │
│ Duration:   45.2s                                          │
│ Status:     ✅ completed                                    │
│ Operations: 12                                              │
│                                                              │
│ SPANS:                                                       │
│ ├─ Read           45ms   ✅                               │
│ ├─ Bash (build)  12.3s  ✅                               │
│ ├─ Bash (deploy)  8.1s  ✅                               │
│ └─ Write          89ms   ✅                               │
│                                                              │
│ LOGS:                                                        │
│ ├─ 14:30:15 INFO  Trace started                          │
│ ├─ 14:30:15 DEBUG Read starting                           │
│ ├─ 14:30:15 DEBUG Read completed 45ms                     │
│ ├─ 14:30:16 INFO  Bash starting (build)                  │
│ └─ ...                                                      │
│                                                              │
│ [Use 'kothar trace logs abc123' for full log]              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] traceId único por operação
- [ ] Todos os logs incluem traceId
- [ ] Filtro por traceId funciona
- [ ] Trace mostra operações + logs + métricas
- [ ] Compatible com formato OpenTelemetry

---

## 🔗 Integração

| Componente | Como usa trace-correlation |
|------------|-------------------------|
| structured-logging | traceId em todo log |
| execution-metrics | traceId em métricas |
| fault-tolerance | trace em retries |
| hooks-system | Hook de trace |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
