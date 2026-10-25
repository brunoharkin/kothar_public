---
name: memory-search
description: >-
  Skill do Kothar: Memory Search. Ativar quando necessário para execução da habilidade memory-search.
---

# Memory Search

> **Skill:** Kothar Memory Search  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Dependência:** `memory-nudge.md`  

---

## 🎯 Objetivo

Sistema de busca em memórias salvas. Permite encontrar contexto relevante de sessões passadas.

**Problema resolvido:** Kothar não consegue lembrar decisões, preferências, ou erros do passado automaticamente.

---

## 📋 Formato de Memória

Toda memória segue este padrão:

```markdown
---
name: slug-descritivo
description: Resumo de uma linha — usado para decidir relevância
metadata:
  type: user | feedback | project | reference | decision | error
  project: nome-do-projeto | null
  date: YYYY-MM-DD
  updated: YYYY-MM-DD
  tags: [tag1, tag2, tag3]
  confidence: 0-100
---

# Título da Memória

Conteúdo completo aqui...

## Por que salvei isso?

[Explicação breve de quando usar esta memória]

## Como aplicar?

[Instruções de uso, padrões, exceções]

---

**Relacionado:** [[nome-da-outra-memoria]]
```

### Tipos de Memória

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `user` | Preferências de Bruno | "Prefere respostas fechadas" |
| `feedback` | Correções feitas | "Erro de isolamento" |
| `project` | Contexto de projeto | "Ratoflix usa X como auth" |
| `reference` | Recursos externos | "Link para docs da API" |
| `decision` | Decisões tomadas | "Mudar de Proton para MAX" |
| `error` | Erros catalogados | "Erro-009: SSH contamination" |

---

## 🗂️ Estrutura de Diretórios

```
~/.claude/projects/-home-bruno-kothar/memory/
├── MEMORY.md              # Índice principal
├── user/                  # Memórias de usuário
│   ├── comunicacao-preferida.md
│   ├── tom-de-resposta.md
│   └── padroes-de-erro.md
├── feedback/              # Feedbacks recebidos
│   ├── feedback-anti-puxa-saco.md
│   ├── feedback-ratoflix-bugs.md
│   └── regras-ouro-kothar.md
├── project/               # Contextos de projeto
│   ├── disparo-em-massa/
│   ├── ratoflix/
│   └── bioleads/
├── reference/             # Referências
├── decision/               # Decisões
│   ├── migracao-vps-max.md
│   └── escolha-stack.md
└── error/                 # Erros catalogados
    ├── erros/
    │   ├── 2026-06-10-erro-001.md
    │   └── 2026-06-18-erro-009.md
    └── analises/
```

---

## 🔍 Tipos de Busca

### 1. Busca por Keyword

```javascript
// Pseudocódigo
function searchByKeyword(keyword) {
  const results = []
  
  for (const memory of allMemories) {
    const score = fuzzyMatch(keyword, memory.content)
    if (score > 0.6) {
      results.push({ memory, score })
    }
  }
  
  return results.sort((a, b) => b.score - a.score)
}
```

**Exemplo de uso:**
```
Bruno: "lembra o que discutimos sobre ssh?"
Kothar: searching... → encontrou "2026-06-18-erro-009-contaminacao-projetos-ssh.md"
```

### 2. Busca por Projeto

```javascript
// Pseudocódigo
function searchByProject(projectName) {
  return memories.filter(m => 
    m.metadata.project === projectName ||
    m.name.includes(projectName)
  )
}
```

**Exemplo de uso:**
```
Bruno: "o que temos salvo sobre ratoflix?"
Kothar: searching... → encontrou 3 memórias de projeto Ratoflix
```

### 3. Busca por Tipo

```javascript
// Pseudocódigo
function searchByType(type) {
  return memories.filter(m => m.metadata.type === type)
}
```

**Exemplo de uso:**
```
Bruno: "quais decisões importantes tomamos?"
Kothar: searching... → encontrou 5 memórias tipo "decision"
```

### 4. Busca por Data

```javascript
// Pseudocódigo
function searchByDateRange(startDate, endDate) {
  return memories.filter(m => 
    m.metadata.date >= startDate &&
    m.metadata.date <= endDate
  )
}
```

**Exemplo de uso:**
```
Bruno: "o que salvamos esta semana?"
Kothar: searching... → encontrou memórias dos últimos 7 dias
```

### 5. Busca por Tag

```javascript
// Pseudocódigo
function searchByTags(tags) {
  return memories.filter(m => 
    tags.every(tag => m.metadata.tags.includes(tag))
  )
}
```

**Exemplo de uso:**
```
Bruno: "memórias sobre ssh e isolamento"
Kothar: searching... → encontrou memórias com tags ["ssh", "isolamento"]
```

---

## 🔄 Busca Combinada

Múltiplos critérios podem ser combinados:

```javascript
// Pseudocódigo
function search(query) {
  const { keyword, project, type, dateRange, tags } = parseQuery(query)
  
  let results = allMemories
  
  if (keyword) results = fuzzyMatch(keyword, results)
  if (project) results = results.filter(m => m.metadata.project === project)
  if (type) results = results.filter(m => m.metadata.type === type)
  if (dateRange) results = dateFilter(results, dateRange)
  if (tags) results = tagFilter(results, tags)
  
  return rerankByRelevance(results, query)
}
```

---

## 📊 Reranking por Relevância

Após busca inicial, resultados são reranqueados:

```javascript
const rerankFactors = {
  recency: 0.3,      // Memórias recentes pesam mais
  frequency: 0.2,    // Memórias referenciadas outras vezes
  type: 0.2,         // user > feedback > decision > project
  project: 0.2,      // Mesmo projeto atual = mais relevante
  confidence: 0.1    // Alta confiança = mais relevante
}
```

---

## 📝 Template de MEMORY.md (Índice)

```markdown
# Índice de Memórias — Kothar

> **Última atualização:** 2026-06-18  
> **Total de memórias:** XX  

---

## 🔍 Como usar

Busque por:
- **keyword:** `search "ssh isolation"`
- **projeto:** `search --project disparo`
- **tipo:** `search --type error`
- **data:** `search --since 2026-06-01`
- **tags:** `search --tags isolamento,ssh`

---

## 📂 Por Tipo

### User (X memórias)
- [comunicacao-preferida](user/comunicacao-preferida.md)
- [tom-de-resposta](user/tom-de-resposta.md)

### Feedback (X memórias)
- [feedback-anti-puxa-saco](feedback/feedback-anti-puxa-saco.md)

### Project (X memórias)
- [ratoflix](project/ratoflix/)
- [disparo-em-massa](project/disparo-em-massa/)

### Decision (X memórias)
- [migracao-vps-max](decision/migracao-vps-max.md)

### Error (X memórias)
- [erro-009](error/erros/2026-06-18-erro-009.md)

---

## 🕐 Recentes (últimos 7 dias)

| Data | Nome | Tipo | Projeto |
|------|------|------|--------|
| 2026-06-18 | SSH contamination | error | kothar |
| 2026-06-16 | Handover Ratoflix | project | ratoflix |

---

*Índice gerado automaticamente — edite manualmente se necessário*
```

---

## 🔧 Comandos de Busca

| Comando | Descrição |
|---------|-----------|
| `search "keyword"` | Busca por palavra-chave |
| `search --project nome` | Filtra por projeto |
| `search --type tipo` | Filtra por tipo (user/feedback/project/decision/error) |
| `search --since YYYY-MM-DD` | A partir de data |
| `search --until YYYY-MM-DD` | Até data |
| `search --tags tag1,tag2` | Por tags |
| `recall "query"` | Alias para search (estilo Kothar NousResearch) |

---

## ✅ DoD (Definition of Done)

- [ ] Busca por keyword funciona com fuzzy match
- [ ] Filtros (projeto, tipo, data, tags) funcionam
- [ ] Índice MEMORY.md é gerado automaticamente
- [ ] Reranking por relevância funciona
- [ ] Comandos de busca estão documentados
- [ ] Memórias novas são indexadas automaticamente

---

## 🔗 Integração

| Skill | Como usa memory-search |
|-------|------------------------|
| `memory-nudge` | Verifica se memória já existe antes de criar |
| `memory-summarize` | Extrai keywords para indexação |
| `user-modeling` | Busca padrões em feedbacks passados |
| `kothar init (R1)` | Carrega contexto relevante na inicialização |

---

## 📂 Estrutura de Arquivos a Criar

```
~/.claude/projects/-home-bruno-kothar/memory/
├── MEMORY.md                    # [ATUALIZAR]
├── user/
│   ├── MEMORY.md               # [CRIAR]
│   └── .gitkeep
├── feedback/
│   ├── MEMORY.md               # [CRIAR]
│   └── .gitkeep
├── project/
│   ├── MEMORY.md               # [CRIAR]
│   └── .gitkeep
├── decision/
│   ├── MEMORY.md               # [CRIAR]
│   └── .gitkeep
└── error/
    ├── MEMORY.md               # [CRIAR]
    └── .gitkeep
```

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
