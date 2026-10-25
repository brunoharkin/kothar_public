---
name: structured-logging
description: >-
  Skill do Kothar: Structured Logging. Ativar quando necessário para execução da habilidade structured-logging.
---

# Structured Logging

> **Skill:** Kothar Structured Logging  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw JSONL logging + levels  

---

## 🎯 Objetivo

Sistema de logging estruturado em JSONL com níveis, redactação automática, e rotação de arquivos.

**Problema resolvido:** Sem logs, debugging é impossível.

---

## 📝 Formato JSONL

```json
{"ts":"2026-06-18T18:00:00.000Z","level":"info","traceId":"abc123","msg":"Tool call","project":"kothar","skill":"memory-nudge","meta":{"tool":"Read","params":{"file_path":"/home/bruno/test.txt"},"duration_ms":45,"success":true}}
{"ts":"2026-06-18T18:00:01.000Z","level":"warn","traceId":"abc123","msg":"Retry detected","project":"kothar","skill":"fault-tolerance","meta":{"retry_count":1,"error":"ECONNREFUSED"}}
{"ts":"2026-06-18T18:00:02.000Z","level":"error","traceId":"abc123","msg":"Tool failed","project":"kothar","skill":"fault-tolerance","meta":{"tool":"Bash","error":"Timeout exceeded","max_retries":3}}
```

---

## 🏗️ Estrutura do Log

```typescript
interface LogEntry {
  // Obrigatórios
  ts: string           // ISO8601
  level: LogLevel      // trace|debug|info|warn|error
  msg: string          // Mensagem legível
  
  // Identificação
  traceId?: string     // Para correlação
  spanId?: string      // Para correlação
  
  // Contexto
  project?: string     // Projeto atual
  skill?: string       // Skill que gerou
  
  // Metadados (flexível)
  meta?: {
    [key: string]: any
  }
  
  // OpenTelemetry
  otel?: {
    traceId: string
    spanId: string
  }
}

type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error'
```

---

## 📂 Estrutura de Arquivos

```
~/.kothar/logs/
├── .gitkeep
├── kothar-2026-06-18.jsonl    # Logs de hoje
├── kothar-2026-06-17.jsonl    # Ontem
├── kothar-2026-06-16.jsonl    # 2 dias atrás
├── kothar-2026-06-15.jsonl    # 3 dias atrás
└── kothar-2026-06-14.jsonl    # 4 dias atrás (próximo a rotacionar)
```

**Rotação:**
- Arquivos max 100MB
- Mantém 5 arquivos + atual
- Compacta arquivos antigos (.gz)

---

## 🎚️ Níveis de Log

| Nível | Uso | Exemplo |
|-------|-----|---------|
| `trace` | Detalhe máximo | Entrada/saída de cada função |
| `debug` | Desenvolvimento | Variáveis, estados intermediários |
| `info` | Operações normais | Tool calls, decisões |
| `warn` | Atenção necessária | Retries, warnings |
| `error` | Falhas | Erros de tool, exceptions |

---

## 🔧 Implementação

```javascript
class KotharLogger {
  constructor(config = {}) {
    this.config = {
      level: config.level || 'info',
      logDir: config.logDir || `${process.env.HOME}/.kothar/logs`,
      maxFileSize: config.maxFileSize || 100 * 1024 * 1024, // 100MB
      maxFiles: config.maxFiles || 5,
      redact: config.redact !== false, // Default true
      redactPatterns: config.redactPatterns || defaultRedactPatterns,
      ...config
    }
    
    this.traceId = null
    this.spanId = null
    this.project = null
    this.skill = null
    
    this.init()
  }
  
  init() {
    // Criar diretório se não existir
    fs.mkdirSync(this.config.logDir, { recursive: true })
    
    // Verificar rotação
    this.checkRotation()
  }
  
  // Criar entrada de log
  createEntry(level, msg, meta = {}) {
    const entry = {
      ts: new Date().toISOString(),
      level,
      msg,
      traceId: this.traceId,
      spanId: this.spanId,
      project: this.project,
      skill: this.skill,
      meta
    }
    
    // Redact sensitive data
    if (this.config.redact) {
      entry.msg = this.redact(entry.msg)
      if (entry.meta) {
        entry.meta = this.redactObject(entry.meta)
      }
    }
    
    return entry
  }
  
  // Escrever no arquivo
  write(entry) {
    const line = JSON.stringify(entry) + '\n'
    
    // Escrever no arquivo atual
    const logFile = this.getCurrentLogFile()
    fs.appendFileSync(logFile, line)
    
    // Também escrever no console seTTY
    if (process.stdout.isTTY) {
      this.writeTTY(entry)
    }
  }
  
  // Métodos de log
  trace(msg, meta) {
    if (this.shouldLog('trace')) {
      this.write(this.createEntry('trace', msg, meta))
    }
  }
  
  debug(msg, meta) {
    if (this.shouldLog('debug')) {
      this.write(this.createEntry('debug', msg, meta))
    }
  }
  
  info(msg, meta) {
    if (this.shouldLog('info')) {
      this.write(this.createEntry('info', msg, meta))
    }
  }
  
  warn(msg, meta) {
    if (this.shouldLog('warn')) {
      this.write(this.createEntry('warn', msg, meta))
    }
  }
  
  error(msg, meta) {
    if (this.shouldLog('error')) {
      this.write(this.createEntry('error', msg, meta))
    }
  }
  
  // Verificar se deve loggar
  shouldLog(level) {
    const levels = ['trace', 'debug', 'info', 'warn', 'error']
    const configLevel = levels.indexOf(this.config.level)
    const msgLevel = levels.indexOf(level)
    return msgLevel >= configLevel
  }
  
  // Obter arquivo de log atual
  getCurrentLogFile() {
    const date = new Date().toISOString().split('T')[0]
    return `${this.config.logDir}/kothar-${date}.jsonl`
  }
  
  // Verificar e fazer rotação
  checkRotation() {
    const logFile = this.getCurrentLogFile()
    
    try {
      const stats = fs.statSync(logFile)
      
      if (stats.size >= this.config.maxFileSize) {
        this.rotate(logFile)
      }
    } catch (e) {
      // Arquivo não existe ainda, ok
    }
    
    // Limpar arquivos antigos
    this.cleanOldLogs()
  }
  
  // Rotacionar arquivo
  rotate(oldFile) {
    const timestamp = Date.now()
    const newFile = `${oldFile}.${timestamp}`
    
    fs.renameSync(oldFile, newFile)
    
    // Compactar arquivo antigo
    gzipFile(newFile, `${newFile}.gz`)
    fs.unlinkSync(newFile)
    
    this.info('Log rotated', { oldFile, newFile })
  }
  
  // Limpar logs antigos
  cleanOldLogs() {
    const files = fs.readdirSync(this.config.logDir)
      .filter(f => f.endsWith('.gz'))
      .map(f => ({
        name: f,
        time: fs.statSync(`${this.config.logDir}/${f}`).mtime
      }))
      .sort((a, b) => b.time - a.time)
    
    // Manter apenas os N mais recentes
    files.slice(this.config.maxFiles).forEach(f => {
      fs.unlinkSync(`${this.config.logDir}/${f.name}`)
    })
  }
}
```

---

## 🔴 Redação Automática

```javascript
const defaultRedactPatterns = [
  // API Keys
  { pattern: /sk-[a-zA-Z0-9]{20,}/g, replacement: 'sk-[REDACTED]' },
  { pattern: /api[_-]?key["\s:=]+["']?([a-zA-Z0-9_-]{20,})/gi, replacement: 'api_key=[REDACTED]' },
  { pattern: /token["\s:=]+["']?([a-zA-Z0-9_.-]{20,})/gi, replacement: 'token=[REDACTED]' },
  
  // Senhas
  { pattern: /password["\s:=]+["']?([^\s"']{8,})/gi, replacement: 'password=[REDACTED]' },
  { pattern: /senha["\s:=]+["']?([^\s"']{4,})/gi, replacement: 'senha=[REDACTED]' },
  { pattern: /passwd["\s:=]+["']?([^\s"']{8,})/gi, replacement: 'passwd=[REDACTED]' },
  
  // JWT
  { pattern: /eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/g, replacement: 'jwt:[REDACTED]' },
  
  // Tokens Bearer
  { pattern: /Bearer\s+[a-zA-Z0-9_.-]{20,}/g, replacement: 'Bearer [REDACTED]' },
  
  // URLs com credenciais
  { pattern: /https?:\/\/[^:]+:[^@]+@/g, replacement: 'https://[REDACTED]@' },
  
  // IPs敏感的 (opcional)
  // { pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, replacement: '[IP]' }
]

function redact(text, patterns = defaultRedactPatterns) {
  let result = text
  for (const { pattern, replacement } of patterns) {
    result = result.replace(pattern, replacement)
  }
  return result
}

function redactObject(obj, patterns = defaultRedactPatterns) {
  const result = {}
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      result[key] = redact(value, patterns)
    } else if (typeof value === 'object' && value !== null) {
      result[key] = redactObject(value, patterns)
    } else {
      result[key] = value
    }
  }
  return result
}
```

---

## 🎨 Console TTY

```javascript
// Cores para console
const colors = {
  trace: '\x1b[90m',   // Gray
  debug: '\x1b[36m',   // Cyan
  info: '\x1b[32m',    // Green
  warn: '\x1b[33m',    // Yellow
  error: '\x1b[31m',   // Red
  reset: '\x1b[0m'
}

writeTTY(entry) {
  const color = colors[entry.level] || colors.reset
  const ts = new Date(entry.ts).toLocaleTimeString()
  const project = entry.project ? `[${entry.project}]` : ''
  const skill = entry.skill ? `<${entry.skill}>` : ''
  
  console.log(
    `${color}${ts} ${entry.level.toUpperCase().padEnd(5)} ${project} ${skill} ${entry.msg}${colors.reset}`,
    entry.meta ? JSON.stringify(entry.meta) : ''
  )
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `kothar logs --follow` | Follow logs em tempo real |
| `kothar logs --level error` | Filtrar só erros |
| `kothar logs --level warn` | Filtrar warnings e erros |
| `kothar logs --project kothar` | Filtrar por projeto |
| `kothar logs --trace-id abc123` | Filtrar por trace |
| `kothar logs --since "10:00"` | Logs desde horário |
| `kothar logs --grep "error"` | Grep nos logs |

---

## 📊 Exemplo de Saída

### Console
```
18:00:00 INFO  [kothar] <memory-nudge> Tool call duration=45ms success=true
18:00:01 WARN  [kothar] <fault-tolerance> Retry detected retry_count=1
18:00:02 ERROR [kothar] <fault-tolerance> Tool failed error="Timeout"
```

### Arquivo JSONL
```json
{"ts":"2026-06-18T18:00:00.000Z","level":"info","msg":"Tool call","project":"kothar","skill":"memory-nudge","meta":{"tool":"Read","duration_ms":45,"success":true}}
{"ts":"2026-06-18T18:00:01.000Z","level":"warn","msg":"Retry detected","project":"kothar","skill":"fault-tolerance","meta":{"retry_count":1}}
{"ts":"2026-06-18T18:00:02.000Z","level":"error","msg":"Tool failed","project":"kothar","skill":"fault-tolerance","meta":{"tool":"Bash","error":"Timeout"}}
```

---

## ✅ DoD (Definition of Done)

- [ ] Logs em JSONL format
- [ ] 5 níveis configuráveis
- [ ] Redação automática de credenciais
- [ ] Rotação: max 100MB, 5 files
- [ ] Console colorido se TTY
- [ ] Comandos de filtro funcionais

---

## 🔗 Integração

| Componente | Como usa structured-logging |
|------------|---------------------------|
| hooks-system | Hooks de logging |
| fault-tolerance | Log de retries |
| execution-metrics | Métricas como logs |
| trace-correlation | traceId nos logs |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
