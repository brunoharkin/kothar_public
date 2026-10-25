---
name: hooks-system
description: >-
  Skill do Kothar: Hooks System. Ativar quando necessário para execução da habilidade hooks-system.
---

# Hooks System

> **Skill:** Kothar Hooks System  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Dependência:** `fault-tolerance.md`  

---

## 🎯 Objetivo

Sistema de hooks para interceptar e modificar comportamento em pontos específicos do ciclo de execução.

**Problema resolvido:** Não há forma de executar lógica custom em before/after de operações.

---

## 🪝 Tipos de Hooks

### Hooks de Ciclo de Vida

| Hook | Quando | Uso |
|------|--------|-----|
| `session_start` | Início de sessão | Carregar contexto |
| `session_end` | Fim de sessão | Salvar estado |
| `tool_call` | Antes de toda tool | Validação, logging |
| `tool_result` | Após toda tool | Processamento, métricas |
| `error` | Em qualquer erro | Tratamento específico |
| `retry` | Antes de retry | Logging, ajuste |

### Hooks de Tool

| Hook | Quando | Uso |
|------|--------|-----|
| `before_tool_call` | Antes de executar | Validar params, logging |
| `after_tool_call` | Após executar | Processar resultado, métricas |
| `on_tool_error` | Em erro de tool | Tratamento, retry |

### Hooks de Kothar

| Hook | Quando | Uso |
|------|--------|-----|
| `before_respond` | Antes de responder | Injetar contexto |
| `after_respond` | Após responder | Logging, métricas |
| `on_nudge` | Antes de nudge | Filtrar, modificar |

---

## 🔧 Registro de Hooks

```javascript
class HooksSystem {
  constructor() {
    this.hooks = {
      session_start: [],
      session_end: [],
      tool_call: [],
      tool_result: [],
      error: [],
      retry: [],
      before_tool_call: [],
      after_tool_call: [],
      on_tool_error: [],
      before_respond: [],
      after_respond: [],
      on_nudge: []
    }
  }
  
  // Registrar um hook
  register(event, callback, options = {}) {
    const { priority = 50, once = false } = options
    
    this.hooks[event].push({
      callback,
      priority,      // 0-100, maior = executa primeiro
      once,          // Executa só uma vez
      executed: false
    })
    
    // Ordenar por prioridade
    this.hooks[event].sort((a, b) => b.priority - a.priority)
  }
  
  // Executar hooks de um evento
  async execute(event, context = {}) {
    const handlers = this.hooks[event] || []
    const results = []
    
    for (const handler of handlers) {
      // Pular se "once" e já executou
      if (handler.once && handler.executed) {
        continue
      }
      
      try {
        const result = await handler.callback(context)
        handler.executed = true
        results.push({ handler, result, success: true })
      } catch (error) {
        results.push({ handler, error, success: false })
        
        // Hook de erro? Tratar
        if (event === 'error') {
          // Não deixar erro de hook quebrar tudo
          log.error(`Hook error in ${event}:`, error)
        }
      }
    }
    
    return results
  }
}
```

---

## 📝 Hooks Pré-configurados

### 1. Logging Hook

```javascript
const loggingHook = {
  name: 'structured-logging',
  event: 'before_tool_call',
  priority: 90,
  callback: async (context) => {
    log.info('Tool call', {
      tool: context.tool,
      params: context.params,
      traceId: context.traceId,
      ts: Date.now()
    })
  }
}

const loggingResultHook = {
  name: 'structured-logging',
  event: 'after_tool_call',
  priority: 90,
  callback: async (context) => {
    log.info('Tool result', {
      tool: context.tool,
      duration_ms: Date.now() - context.startTime,
      success: context.success,
      traceId: context.traceId
    })
  }
}
```

### 2. Metrics Hook

```javascript
const metricsHook = {
  name: 'execution-metrics',
  event: 'after_tool_call',
  priority: 80,
  callback: async (context) => {
    await recordMetric({
      tool_name: context.tool,
      success: context.success,
      duration_ms: Date.now() - context.startTime,
      retry_count: context.retryCount || 0,
      error_type: context.error?.type || null,
      session_id: context.sessionId,
      project: context.project
    })
  }
}
```

### 3. Security Hook

```javascript
const securityHook = {
  name: 'command-allowlist',
  event: 'before_tool_call',
  priority: 100, // Executa primeiro!
  callback: async (context) => {
    if (context.tool === 'Bash') {
      const allowed = checkAllowlist(context.params.command)
      if (!allowed.allowed) {
        throw new Error(`Comando bloqueado: ${allowed.reason}`)
      }
    }
  }
}
```

### 4. Context Hook

```javascript
const contextHook = {
  name: 'project-sandbox',
  event: 'session_start',
  priority: 100,
  callback: async (context) => {
    const project = detectProject()
    const sandbox = loadSandbox(project)
    
    return {
      ...context,
      project: sandbox.project,
      pwd: sandbox.pwd,
      sshKey: sandbox.sshKey,
      memory: sandbox.memory
    }
  }
}
```

---

## 🔄 Pipeline de Execução

```
┌─────────────────────────────────────────────────────────────┐
│ TOOL CALL PIPELINE COM HOOKS                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. [Execute before_tool_call hooks]                        │
│                    │                                         │
│                    ▼                                         │
│  2. [Tool executa]                                          │
│                    │                                         │
│                    ▼                                         │
│  3. [Sucesso?]                                             │
│          │              │                                    │
│          ▼              ▼                                    │
│       [sim]          [não]                                  │
│          │              │                                    │
│          │              ▼                                    │
│          │     4. [Execute on_tool_error hooks]            │
│          │              │                                    │
│          │              ▼                                    │
│          │     5. [shouldRetry?]                           │
│          │              │                                    │
│          │       ┌─────┴─────┐                             │
│          │       │           │                             │
│          │      [sim]       [não]                          │
│          │       │           │                             │
│          │       ▼           ▼                              │
│          │  6. [retry]   7. [failure]                      │
│          │       │           │                             │
│          │       └─────┬─────┘                             │
│          │             │                                   │
│          │             ▼                                    │
│          │   [Execute retry hooks]                         │
│          │             │                                   │
│          │             └─────────────┘                      │
│          │                                                   │
│          ▼                                                   │
│  8. [Execute after_tool_call hooks]                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Registro de Hooks Custom

```javascript
// Exemplo: Hook para detectar comandos repetidos
kothar.hooks.register('before_tool_call', async (context) => {
  if (context.tool === 'Bash') {
    const cmd = context.params.command
    const history = await getCommandHistory()
    
    // Detectar repetição
    const repeats = history.filter(h => h.command === cmd).length
    if (repeats >= 3) {
      log.warn(`Comando repetido ${repeats}x: ${cmd}`)
      
      // Notificar
      notify({
        type: 'repetitive_command',
        command: cmd,
        repeats: repeats
      })
    }
  }
}, { priority: 75 })
```

---

## ⚙️ Configuração

```javascript
const hooksConfig = {
  // Quais hooks estão ativos
  enabled: {
    logging: true,
    metrics: true,
    security: true,
    context: true
  },
  
  // Prioridades padrão
  defaultPriority: 50,
  
  // Parar em erro de hook?
  stopOnHookError: false,
  
  // Timeout por hook (ms)
  hookTimeout: 5000
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `hooks list` | Lista todos os hooks registrados |
| `hooks enable nome` | Habilita hook |
| `hooks disable nome` | Desabilita hook |
| `hooks debug` | Log detalhado de hooks |

---

## ✅ DoD (Definition of Done)

- [ ] Hooks podem ser registrados com priority
- [ ] Hooks são executados em ordem de prioridade
- [ ] Hooks "once" executam só uma vez
- [ ] Erro em hook não quebra execução principal
- [ ] Métricas são gravadas automaticamente
- [ ] Logging é automático

---

## 🔗 Integração

| Componente | Como usa hooks |
|------------|---------------|
| fault-tolerance | Hooks de retry |
| structured-logging | before/after logging |
| execution-metrics | Métricas automáticas |
| command-allowlist | before_tool_call |
| project-sandbox | session_start |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
