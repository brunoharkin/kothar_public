# Execution Metrics

> **Skill:** Kothar Execution Metrics  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw `TTFB + durationMs + requestPayloadBytes`  

---

## 🎯 Objetivo

Sistema de coleta de métricas de execução por tool call e sessão.

**Problema resolvido:** Não sabe quanto tempo cada operação demora, não mede qualidade.

---

## 📊 Métricas por Tool Call

```typescript
interface ToolMetric {
  // Identificação
  id: string                    // UUID
  traceId: string              // Para correlação
  sessionId: string            // Sessão atual
  project: string              // Projeto atual
  
  // Tool info
  tool: string                 // Nome da tool
  toolParams: object           // Params (redacted)
  
  // Timing
  startTime: number            // Timestamp Unix ms
  endTime: number              // Timestamp Unix ms
  duration_ms: number          // Duração em ms
  
  // Resultado
  success: boolean
  error_type?: string          // 'timeout' | 'network' | 'logic' | etc
  error_message?: string
  
  // Retry
  retry_count: number
  retry_delays_ms: number[]    // Delays entre retries
  
  // Size (para tools de rede)
  request_bytes?: number
  response_bytes?: number
  
  // Provider (se aplicável)
  provider?: string
  model?: string
  tokens_used?: number
  ttfb_ms?: number            // Time to first byte
}
```

---

## 📂 Estrutura de Arquivos

```
~/.kothar/metrics/
├── sessions/
│   ├── session-2026-06-18-1400.jsonl    # Uma linha por tool call
│   └── session-2026-06-18-1430.jsonl
├── quality/
│   ├── daily-2026-06-18.json            # Score diário
│   └── weekly-2026-06-week25.json       # Score semanal
└── summary/
    └── summary.json                      # Aggregate geral
```

---

## 🔧 Implementação

```javascript
class ExecutionMetrics {
  constructor(config = {}) {
    this.config = {
      metricsDir: config.metricsDir || `${process.env.HOME}/.kothar/metrics`,
      sessionFile: null, // Criado por sessão
      ...config
    }
    
    this.metrics = []
    this.sessionId = this.generateSessionId()
    this.sessionStart = Date.now()
    
    this.init()
  }
  
  init() {
    // Criar diretórios
    fs.mkdirSync(`${this.config.metricsDir}/sessions`, { recursive: true })
    fs.mkdirSync(`${this.config.metricsDir}/quality`, { recursive: true })
    
    // Criar arquivo da sessão
    const date = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 16)
    this.config.sessionFile = `${this.config.metricsDir}/sessions/session-${date}.jsonl`
  }
  
  // Iniciar medição de uma tool
  startTool(tool, params = {}, traceId = null) {
    const metric = {
      id: this.generateId(),
      traceId: traceId || this.generateTraceId(),
      sessionId: this.sessionId,
      project: currentProject,
      tool,
      toolParams: this.redactParams(params),
      startTime: Date.now(),
      retry_count: 0,
      retry_delays_ms: []
    }
    
    this.currentMetric = metric
    return metric.id
  }
  
  // Finalizar medição
  endTool(metricId, result) {
    const metric = this.currentMetric
    if (!metric || metric.id !== metricId) {
      log.warn('Metric not found', { metricId })
      return
    }
    
    metric.endTime = Date.now()
    metric.duration_ms = metric.endTime - metric.startTime
    metric.success = result.success
    metric.error_type = result.error?.type || null
    metric.error_message = result.error?.message || null
    
    if (result.tokens_used) metric.tokens_used = result.tokens_used
    if (result.ttfb_ms) metric.ttfb_ms = result.ttfb_ms
    if (result.request_bytes) metric.request_bytes = result.request_bytes
    if (result.response_bytes) metric.response_bytes = result.response_bytes
    
    // Salvar
    this.saveMetric(metric)
    
    // Limpar
    this.currentMetric = null
    
    return metric
  }
  
  // Registrar retry
  recordRetry(metricId, delayMs) {
    const metric = this.currentMetric
    if (metric && metric.id === metricId) {
      metric.retry_count++
      metric.retry_delays_ms.push(delayMs)
    }
  }
  
  // Salvar métrica
  saveMetric(metric) {
    const line = JSON.stringify(metric) + '\n'
    fs.appendFileSync(this.config.sessionFile, line)
    this.metrics.push(metric)
  }
  
  // Calcular score de qualidade
  calculateQualityScore(sessionId = null) {
    const metrics = sessionId 
      ? this.metrics.filter(m => m.sessionId === sessionId)
      : this.metrics
    
    if (metrics.length === 0) {
      return { score: 0, reasons: ['no_data'] }
    }
    
    const total = metrics.length
    const successful = metrics.filter(m => m.success).length
    const failed = total - successful
    
    // Componentes do score
    const successRate = successful / total  // 40% do score
    const avgDuration = this.avg(metrics.map(m => m.duration_ms))
    const durationScore = this.durationScore(avgDuration) // 30% do score
    const errorRate = failed / total
    const errorScore = 1 - errorRate  // 30% do score
    
    const score = Math.round(
      (successRate * 40) +
      (durationScore * 30) +
      (errorScore * 30)
    )
    
    return {
      score,
      total,
      successful,
      failed,
      avg_duration_ms: Math.round(avgDuration),
      success_rate: Math.round(successRate * 100),
      components: {
        success_rate: { value: Math.round(successRate * 100), weight: 40 },
        duration: { value: durationScore * 100, weight: 30 },
        error_rate: { value: errorScore * 100, weight: 30 }
      }
    }
  }
  
  durationScore(avgMs) {
    // Quanto menor, melhor
    if (avgMs < 1000) return 1.0      // <1s = 100%
    if (avgMs < 5000) return 0.8      // <5s = 80%
    if (avgMs < 10000) return 0.6     // <10s = 60%
    if (avgMs < 30000) return 0.4    // <30s = 40%
    return 0.2                         // >30s = 20%
  }
  
  avg(arr) {
    return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0
  }
  
  // Estatísticas
  getStats(since = null) {
    const metrics = since
      ? this.metrics.filter(m => m.startTime >= since)
      : this.metrics
    
    const byTool = {}
    for (const m of metrics) {
      if (!byTool[m.tool]) byTool[m.tool] = []
      byTool[m.tool].push(m)
    }
    
    const toolStats = {}
    for (const [tool, toolMetrics] of Object.entries(byTool)) {
      const durations = toolMetrics.map(m => m.duration_ms)
      const successes = toolMetrics.filter(m => m.success)
      
      toolStats[tool] = {
        calls: toolMetrics.length,
        success_rate: Math.round((successes.length / toolMetrics.length) * 100),
        avg_ms: Math.round(this.avg(durations)),
        min_ms: Math.min(...durations),
        max_ms: Math.max(...durations),
        p95_ms: this.percentile(durations, 95),
        total_ms: durations.reduce((a, b) => a + b, 0)
      }
    }
    
    return {
      session_id: this.sessionId,
      session_duration_ms: Date.now() - this.sessionStart,
      total_calls: metrics.length,
      successful_calls: metrics.filter(m => m.success).length,
      failed_calls: metrics.filter(m => !m.success).length,
      by_tool: toolStats
    }
  }
  
  percentile(arr, p) {
    const sorted = [...arr].sort((a, b) => a - b)
    const idx = Math.ceil((p / 100) * sorted.length) - 1
    return sorted[idx] || 0
  }
}
```

---

## 📊 Score de Qualidade

```
┌─────────────────────────────────────────────────────────────┐
│ QUALITY SCORE                                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Score: 87/100                                             │
│                                                              │
│  Componentes:                                                │
│  ├─ Taxa de sucesso: 95%  (40% peso) → 38pts             │
│  ├─ Duração média:  1.2s  (30% peso) → 28pts             │
│  └─ Taxa de erro:    5%    (30% peso) → 21pts             │
│                                                              │
│  Comparação:                                                 │
│  ├─ Ontem:  82/100                                        │
│  ├─ Média:  85/100                                        │
│  └─ Meta:   90/100                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `kothar metrics show` | Métricas da sessão atual |
| `kothar metrics quality` | Score de qualidade |
| `kothar metrics history` | Histórico de sessões |
| `kothar metrics stats` | Estatísticas por tool |
| `kothar metrics export` | Exportar como JSON |

---

## 📝 Exemplo de Output

```
$ kothar metrics show

┌─────────────────────────────────────────────────────────────┐
│ SESSION METRICS — 2026-06-18 14:30                         │
├─────────────────────────────────────────────────────────────┤
│ Total calls:    47                                          │
│ Successful:     45 (95.7%)                                 │
│ Failed:         2 (4.3%)                                   │
│ Duration:       12m 34s                                    │
│ Avg per call:   320ms                                       │
│                                                              │
│ BY TOOL:                                                       │
│ ├─ Read       12 calls  avg 45ms   100% success          │
│ ├─ Bash       8 calls   avg 1.2s   87% success          │
│ ├─ Write      10 calls  avg 89ms   100% success          │
│ ├─ Agent      5 calls   avg 45s   100% success          │
│ └─ Edit       12 calls  avg 156ms  100% success          │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] Métricas gravadas para cada tool call
- [ ] TTFB medido
- [ ] Duration medido
- [ ] Score de qualidade calculado
- [ ] Estatísticas por tool
- [ ] Histórico de sessões

---

## 🔗 Integração

| Componente | Como usa execution-metrics |
|------------|-------------------------|
| hooks-system | Hook after_tool_call |
| fault-tolerance | Métricas de retry |
| quality-score | Score de sessão |
| trace-correlation | traceId nas métricas |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
