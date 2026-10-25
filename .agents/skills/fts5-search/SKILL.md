---
name: fts5-search
description: >-
  Skill do Kothar: FTS5 Search. Ativar quando necessário para execução da habilidade fts5-search.
---

# FTS5 Search

> **Skill:** Kothar FTS5 Search  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** Kothar NousResearch FTS5 + LLM reranking  

---

## 🎯 Objetivo

Busca full-text em conversas passadas. Recupera contexto relevante de sessões anteriores.

**Problema resolvido:** Não consegue buscar em conversas passadas automaticamente.

---

## 🗄️ Estrutura

```
~/.kothar/transcripts/
├── 2026-06/
│   ├── session-2026-06-18-1400.jsonl   # Uma linha por mensagem
│   ├── session-2026-06-18-1430.jsonl
│   └── ...
├── 2026-05/
│   └── ...
└── index.db                           # SQLite FTS5
```

---

## 📝 Formato de Transcript

```typescript
interface TranscriptEntry {
  id: string              // UUID
  sessionId: string      // ID da sessão
  timestamp: string       // ISO8601
  role: 'user' | 'assistant' | 'system'
  content: string        // Texto da mensagem
  project?: string       // Projeto atual
  toolCalls?: ToolCall[] // Se foi tool call
  metadata: {
    tokens?: number
    model?: string
    traceId?: string
  }
}

interface ToolCall {
  tool: string
  params: object
  result?: object
  duration_ms?: number
  success: boolean
}
```

---

## 🔧 Implementação (SQLite FTS5)

```javascript
const Database = require('better-sqlite3')

class FTSSearch {
  constructor(config = {}) {
    this.config = {
      dbPath: config.dbPath || `${process.env.HOME}/.kothar/transcripts/index.db`,
      transcriptsDir: config.transcriptsDir || `${process.env.HOME}/.kothar/transcripts`,
      ...config
    }
    
    this.db = null
    this.init()
  }
  
  init() {
    // Criar diretórios
    fs.mkdirSync(this.config.transcriptsDir, { recursive: true })
    
    // Abrir/criar banco
    this.db = new Database(this.config.dbPath)
    
    // Criar schema FTS5
    this.db.exec(`
      CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts USING fts5(
        content,
        content_rowid='rowid',
        tokenize='porter unicode61'
      );
      
      CREATE TABLE IF NOT EXISTS transcripts (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        timestamp TEXT,
        role TEXT,
        project TEXT,
        metadata TEXT,
        content TEXT
      );
      
      CREATE INDEX IF NOT EXISTS idx_session ON transcripts(session_id);
      CREATE INDEX IF NOT EXISTS idx_timestamp ON transcripts(timestamp);
      CREATE INDEX IF NOT EXISTS idx_project ON transcripts(project);
    `)
  }
  
  // Indexar transcript
  index(sessionId, entries) {
    const insert = this.db.prepare(`
      INSERT INTO transcripts (id, session_id, timestamp, role, project, metadata, content)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `)
    
    const insertFts = this.db.prepare(`
      INSERT INTO transcripts_fts(rowid, content) VALUES (?, ?)
    `)
    
    const transaction = this.db.transaction((entries) => {
      for (const entry of entries) {
        const metadata = JSON.stringify(entry.metadata || {})
        
        const result = insert.run(
          entry.id,
          sessionId,
          entry.timestamp,
          entry.role,
          entry.project || null,
          metadata,
          entry.content
        )
        
        insertFts.run(result.lastInsertRowid, entry.content)
      }
    })
    
    transaction(entries)
  }
  
  // Buscar
  search(query, options = {}) {
    const {
      project = null,
      since = null,
      until = null,
      sessionId = null,
      limit = 10,
      rerank = true
    } = options
    
    // Query FTS5
    let sql = `
      SELECT 
        t.*,
        fts.rank,
        highlight(transcripts_fts, 0, '<mark>', '</mark>') as highlighted
      FROM transcripts_fts fts
      JOIN transcripts t ON t.rowid = fts.rowid
      WHERE transcripts_fts MATCH ?
    `
    
    const params = [query]
    
    // Filtros
    if (project) {
      sql += ` AND t.project = ?`
      params.push(project)
    }
    
    if (since) {
      sql += ` AND t.timestamp >= ?`
      params.push(since)
    }
    
    if (until) {
      sql += ` AND t.timestamp <= ?`
      params.push(until)
    }
    
    if (sessionId) {
      sql += ` AND t.session_id = ?`
      params.push(sessionId)
    }
    
    sql += ` ORDER BY rank LIMIT ?`
    params.push(limit)
    
    const results = this.db.prepare(sql).all(...params)
    
    // Reranking com LLM (opcional)
    if (rerank && results.length > 0) {
      return this.rerankResults(results, query)
    }
    
    return results
  }
  
  // Reranking com LLM
  async rerankResults(results, query) {
    const reranked = []
    
    for (const result of results) {
      const relevance = await this.evaluateRelevance(result.content, query)
      reranked.push({ ...result, relevance_score: relevance })
    }
    
    // Ordenar por score de relevância
    return reranked.sort((a, b) => b.relevance_score - a.relevance_score)
  }
  
  // Avaliar relevância com LLM
  async evaluateRelevance(content, query) {
    const prompt = `
Evaluate how relevant this transcript snippet is to the query.

Query: "${query}"

Snippet: "${content.slice(0, 500)}..."

Rate relevance 0-10:
- 10: Perfect match, directly answers query
- 7-9: Highly relevant, contains key information
- 4-6: Somewhat relevant, partial match
- 1-3: Minimally relevant
- 0: Not relevant at all

Respond with just the number.
`
    
    try {
      const response = await callLLM({ prompt, max_tokens: 5 })
      return parseInt(response.trim()) / 10
    } catch {
      return 0.5 // Default
    }
  }
  
  // Buscar por sessão
  getSession(sessionId) {
    const entries = this.db.prepare(`
      SELECT * FROM transcripts 
      WHERE session_id = ?
      ORDER BY timestamp
    `).all(sessionId)
    
    return entries.map(e => ({
      ...e,
      metadata: JSON.parse(e.metadata || '{}')
    }))
  }
  
  // Buscar sessões por data/projeto
  getSessions(options = {}) {
    const { project, since, until, limit = 50 } = options
    
    let sql = `SELECT DISTINCT session_id, MIN(timestamp) as first_message, MAX(timestamp) as last_message, project FROM transcripts WHERE 1=1`
    const params = []
    
    if (project) {
      sql += ` AND project = ?`
      params.push(project)
    }
    
    if (since) {
      sql += ` AND timestamp >= ?`
      params.push(since)
    }
    
    if (until) {
      sql += ` AND timestamp <= ?`
      params.push(until)
    }
    
    sql += ` GROUP BY session_id ORDER BY first_message DESC LIMIT ?`
    params.push(limit)
    
    return this.db.prepare(sql).all(...params)
  }
  
  // Estatísticas
  getStats() {
    const total = this.db.prepare(`SELECT COUNT(*) as count FROM transcripts`).get()
    const sessions = this.db.prepare(`SELECT COUNT(DISTINCT session_id) as count FROM transcripts`).get()
    const byProject = this.db.prepare(`
      SELECT project, COUNT(*) as count 
      FROM transcripts 
      GROUP BY project 
      ORDER BY count DESC
    `).all()
    
    return {
      total_entries: total.count,
      total_sessions: sessions.count,
      by_project: byProject
    }
  }
}
```

---

## 🔧 Transcript Storage

```javascript
class TranscriptStorage {
  constructor(config = {}) {
    this.config = {
      transcriptsDir: config.transcriptsDir || `${process.env.HOME}/.kothar/transcripts`,
      maxFileSize: config.maxFileSize || 100 * 1024, // 100KB
      compression: config.compression !== false,
      ...config
    }
    
    this.currentSession = null
    this.sessionFile = null
    this.buffer = []
  }
  
  // Iniciar sessão
  startSession(sessionId, project) {
    this.currentSession = {
      id: sessionId,
      project,
      startTime: new Date().toISOString()
    }
    
    // Criar arquivo
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '/')
    const dir = `${this.config.transcriptsDir}/${date}`
    fs.mkdirSync(dir, { recursive: true })
    
    const time = new Date().toISOString().replace(/[:.]/g, '-').slice(11, 16)
    this.sessionFile = `${dir}/session-${date}-${time}.jsonl`
    
    this.buffer = []
  }
  
  // Adicionar entrada
  add(role, content, metadata = {}) {
    const entry = {
      id: this.generateId(),
      sessionId: this.currentSession?.id,
      timestamp: new Date().toISOString(),
      role,
      content,
      project: this.currentSession?.project,
      metadata
    }
    
    this.buffer.push(entry)
    
    // Flush se buffer grande
    if (this.buffer.length >= 100) {
      this.flush()
    }
    
    return entry
  }
  
  // Flush buffer para arquivo
  flush() {
    if (!this.sessionFile || this.buffer.length === 0) return
    
    const lines = this.buffer.map(e => JSON.stringify(e)).join('\n') + '\n'
    fs.appendFileSync(this.sessionFile, lines)
    
    this.buffer = []
  }
  
  // Finalizar sessão
  endSession() {
    this.flush()
    
    // Indexar no FTS5
    if (this.currentSession && this.sessionFile) {
      const entries = this.readSessionFile()
      fts.index(this.currentSession.id, entries)
    }
    
    this.currentSession = null
    this.sessionFile = null
  }
  
  // Ler arquivo de sessão
  readSessionFile() {
    if (!this.sessionFile || !fs.existsSync(this.sessionFile)) return []
    
    const content = fs.readFileSync(this.sessionFile, 'utf8')
    return content.split('\n').filter(l => l.trim()).map(l => JSON.parse(l))
  }
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `recall "query"` | Buscar em conversas passadas |
| `recall --project nome` | Filtrar por projeto |
| `recall --since YYYY-MM-DD` | A partir de data |
| `recall --limit 20` | Limitar resultados |
| `sessions list` | Listar sessões |
| `sessions show id` | Ver sessão completa |
| `transcripts stats` | Estatísticas |

---

## 📝 Exemplo de Output

```
$ recall "ssh isolation"

┌─────────────────────────────────────────────────────────────┐
│ RESULTS: "ssh isolation" — 3 found                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 📄 session-2026-06-18-1430                                 │
│ 14:35 — "Detectei erro de isolamento de projetos via SSH"  │
│ Relevance: 0.95 ⭐                                          │
│                                                              │
│ 📄 session-2026-06-18-1400                                 │
│ 14:22 — "Precisamos validar chave SSH antes de clone"      │
│ Relevance: 0.87 ⭐                                          │
│                                                              │
│ 📄 session-2026-06-15-1000                                 │
│ 10:15 — "Erro-002: Ignorou padrão QR existente"           │
│ Relevance: 0.45                                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] Transcripts salvos automaticamente
- [ ] Busca por keyword funciona
- [ ] Filtros (projeto, data) funcionam
- [ ] LLM reranking melhora resultados
- [ ] Sessões são listáveis
- [ ] Estatísticas funcionam

---

## 🔗 Integração

| Componente | Como usa fts5-search |
|------------|---------------------|
| memory-nudge | Detecta contexto para recall |
| user-modeling | Usa busca para modelar |
| hooks-system | Hooks de transcript |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
