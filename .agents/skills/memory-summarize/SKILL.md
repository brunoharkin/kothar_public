---
name: memory-summarize
description: >-
  Skill do Kothar: Memory Summarize. Ativar quando necessário para execução da habilidade memory-summarize.
---

# Memory Summarize

> **Skill:** Kothar Memory Summarize  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Dependência:** `memory-nudge.md`, `memory-search.md`  

---

## 🎯 Objetivo

Sistema de sumarização compressiva para memórias longas. Extrai keywords e gera resumos otimizados para busca.

**Problema resolvido:** Memórias muito longas poluem o índice; Kothar precisa resumir para manter busca eficiente.

---

## 📏 Regras de Sumarização

### Limites por Tipo

| Tipo | Limite | Razão |
|------|--------|-------|
| `user` | 500 chars | Preferências devem ser concisas |
| `feedback` | 1000 chars | Contexto importante para padrões |
| `project` | 2000 chars | Contexto de projeto pode ser denso |
| `reference` | 3000 chars | Pode conter muito contexto |
| `decision` | 800 chars | Decisões devem ser diretas |
| `error` | 1500 chars | Erros precisam de detalhes |

---

## 🔄 Algoritmo de Sumarização

```
┌─────────────────────────────────────────────────────────────┐
│ SUMARIZADOR DE MEMÓRIA                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Texto longo + tipo de memória                       │
│                                                              │
│  1. ANÁLISE INICIAL                                        │
│     - Conta tokens/caracteres                               │
│     - Identifica se precisa resumir                          │
│                                                              │
│  2. EXTRAÇÃO DE ESTRUTURA                                   │
│     - Headings (##, ###) → mantidos se importantes         │
│     - Listas → resumidas se > 5 itens                       │
│     - Código → preserved (não resumir)                        │
│     - Links → preserved                                     │
│                                                              │
│  3. EXTRAÇÃO DE KEYWORDS                                   │
│     - Nomes próprios (PascalCase)                           │
│     - Tecnologias (React, Node, etc)                        │
│     - Ações (deploy, commit, etc)                           │
│     - Problemas (bug, erro, etc)                            │
│                                                              │
│  4. GERAÇÃO DE RESUMO                                       │
│     - Primeira frase: essencial                             │
│     - Último parágrafo: conclusão                           │
│     - Meio: compressão inteligente                          │
│                                                              │
│  OUTPUT:                                                    │
│     - summary: texto resumido                               │
│     - keywords: [array de keywords]                         │
│     - original_length: número                               │
│     - summary_length: número                                 │
│     - compression_ratio: número                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Template de Memória Sumarizada

### Antes (original grande)

```markdown
---
name: deploy-ratoflix-complexo
description: Deploy do Ratoflix envolve múltiplos passos complexos
metadata:
  type: project
  project: ratoflix
---

# Deploy Ratoflix — Processo Completo

## Pré-requisitos

1. Backup do banco de dados (não pular!)
2. Verificar variáveis de ambiente
3. Testar localmente
4. Comunicar equipe

## Passos do Deploy

### 1. Backup
```bash
pg_dump ratoflix > backup-$(date +%Y%m%d).sql
```
Este backup deve ser armazenado em local seguro.

### 2. Build
```bash
npm run build
```
O build pode demorar 5-10 minutos dependendo da conexão.

### 3. Deploy
```bash
pm2 restart ratoflix
```
Depois do restart, verificar logs.

### 4. Verificação
- [ ] Homepage carrega?
- [ ] Login funciona?
- [ ] API responde?

## Problemas Conhecidos

Se o login não funcionar, verificar:
- JWT_SECRET está setado
- DATABASE_URL está correto
- Session não expirou

... (mais 2000 chars de detalhes) ...
```

### Depois (sumarizado)

```markdown
---
name: deploy-ratoflix-complexo
description: Deploy Ratoflix: backup → build → pm2 restart → verificar
metadata:
  type: project
  project: ratoflix
  keywords: [deploy, pm2, backup, postgres, ratoflix]
  summary_length: 450
  compressed: true
---

# Deploy Ratoflix — Processo

## Resumo
Deploy simples: backup (pg_dump) → build (npm) → pm2 restart → verificar (homepage, login, API).

## Problemas Conhecidos
- Login falhando? Verificar JWT_SECRET, DATABASE_URL, session.
- Build lento? Normal (5-10min).

## Referência
\`\`\`bash
pg_dump ratoflix > backup.sql
npm run build
pm2 restart ratoflix
\`\`\`

---

*Sumarizado automaticamente em 2026-06-18 (original: 3500 chars → 450 chars)*
```

---

## 🏷️ Extração de Keywords

### Padrões Recognizados

```javascript
const keywordPatterns = {
  // Tecnologias (detectadas por contexto)
  technologies: /\b(React|Node|Python|PostgreSQL|MongoDB|Redis|Docker|Kubernetes)\b/gi,
  
  // Ações comuns
  actions: /\b(deploy|commit|push|pull|merge|build|test|debug|fix|criar|editar|deletar)\b/gi,
  
  // Problemas
  problems: /\b(bug|erro|falha|crash|timeout|memory leak|race condition)\b/gi,
  
  // Nomes de projetos (PascalCase)
  projects: /\b[A-Z][a-z]+[A-Z][a-z]+\b/g,
  
  // Variáveis/constantes (SCREAMING_SNAKE_CASE)
  constants: /\b[A-Z_]{3,}\b/g,
  
  // URLs/domínios
  urls: /https?:\/\/[^\s]+/g,
  
  // Comandos (começam com $ ou \`bash|sh|npm|git)
  commands: /\`(bash|sh|npm|git|pnpm|yarn|docker|kubectl) [^\`]+/g
}
```

### Resultado da Extração

```javascript
const extracted = {
  keywords: ["deploy", "pm2", "backup", "postgres", "ratoflix", "npm", "build"],
  technologies: ["PostgreSQL", "Node"],
  actions: ["deploy", "build", "restart"],
  problems: [],
  projects: ["Ratoflix"],
  commands: ["pg_dump", "npm run build", "pm2 restart"]
}
```

---

## 🔧 Funções de Sumarização

### sumarize(text, options)

```javascript
/**
 * Sumariza texto mantendo estrutura e keywords
 * @param {string} text - Texto original
 * @param {Object} options - Opções de sumarização
 * @param {number} options.maxLength - Tamanho máximo (default por tipo)
 * @param {string} options.type - Tipo da memória
 * @param {boolean} options.preserveCode - Manter código? (default: true)
 * @returns {Object} { summary, keywords, stats }
 */
function summarize(text, options = {}) {
  const { maxLength = 1000, type = 'default', preserveCode = true } = options
  
  // 1. Extrair código (preserved)
  const codeBlocks = extractCodeBlocks(text)
  
  // 2. Extrair keywords
  const keywords = extractKeywords(text)
  
  // 3. Comprimir texto não-código
  const compressedText = compressText(removeCode(text), maxLength)
  
  // 4. Reconstruir com código
  const summary = reconstruct(compressedText, codeBlocks, preserveCode)
  
  return {
    summary,
    keywords,
    stats: {
      original_length: text.length,
      summary_length: summary.length,
      compression_ratio: (1 - summary.length / text.length).toFixed(2)
    }
  }
}
```

### extractKeywords(text)

```javascript
/**
 * Extrai keywords relevantes do texto
 * @param {string} text - Texto para extrair
 * @returns {string[]} Array de keywords
 */
function extractKeywords(text) {
  const keywords = new Set()
  
  for (const [patternName, pattern] of Object.entries(keywordPatterns)) {
    const matches = text.match(pattern) || []
    matches.forEach(m => keywords.add(m.toLowerCase()))
  }
  
  // Adicionar primeiras e últimas palavras (importância posicional)
  const words = text.split(/\s+/).slice(0, 10)
  words.forEach(w => {
    if (w.length > 3 && !stopWords.includes(w)) {
      keywords.add(w.toLowerCase())
    }
  })
  
  return Array.from(keywords).slice(0, 10) // Max 10 keywords
}
```

---

## 📋 Integração com memory-nudge

Quando memory-nudge detecta contexto para salvar:

```javascript
// 1. memory-nudge detecta contexto
const context = {
  type: 'decision',
  content: 'Mudar de Proton para VPS MAX porque... [texto longo de 5000 chars]'
}

// 2. memory-summarize entra em ação
const { summary, keywords } = summarize(context.content, {
  type: 'decision',
  maxLength: 800
})

// 3. Gera memória otimizada
const memory = {
  name: 'migracao-proton-para-max',
  description: summary.slice(0, 100), // Primeira linha do resumo
  content: summary,
  keywords,
  metadata: {
    type: 'decision',
    compressed: true,
    original_length: context.content.length
  }
}
```

---

## ✅ DoD (Definition of Done)

- [ ] Limites por tipo são respeitados
- [ ] Código é preservado na sumarização
- [ ] Keywords são extraídas automaticamente
- [ ] MEMORY.md é atualizado com keywords
- [ ] Estatísticas de compressão são gravadas
- [ ] Sumarização não perde informação essencial

---

## 🔗 Integração

| Skill | Como usa memory-summarize |
|-------|---------------------------|
| `memory-nudge` | Sumariza antes de salvar |
| `memory-search` | Usa keywords para busca |
| `skill-workshop` | Resume propostas de skills |
| `user-modeling` | Comprime preferências aprendidas |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
