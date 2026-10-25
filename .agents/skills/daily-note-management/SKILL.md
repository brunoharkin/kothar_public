---
name: daily-note-management
description: >-
  Gerenciar notas diárias estruturadas
---

# Skill: Daily Note Management

## Funcionalidade
Cria, gerencia e organiza notas diárias em estrutura YYYY-MM/YYYY-MM-DD.

## Estrutura de Diário

### Path Pattern
```
00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md
```

**Exemplos**:
```
00_Memoria/Diarias/2026-05/2026-05-24.md
00_Memoria/Diarias/2026-05/2026-05-23.md
00_Memoria/Diarias/2026-04/2026-04-30.md
```

### Benefícios dessa estrutura
✅ Fácil navegação por mês  
✅ Controle diário e mensal  
✅ Organização temporal clara  
✅ Performance melhorada (arquivos separados)  

## Template de Nota do Dia

```markdown
# Interações - 2026-05-24

**Kothar iniciado em**: 2026-05-24 08:00:00  
**Status**: 🟢 Operacional

---

## Conversa 1 - 08:15
**Usuário**: [pergunta/solicitação]
**Kothar**: [resposta completa]
**Contexto**: 
  - Timestamp: 2026-05-24 08:15:30
  - Tags: #tag1 #tag2
  - Relacionado-a: [arquivo.md]

---

## Conversa 2 - 09:30
[similar structure]

---

## Resumo do Dia
[Opcional - resumo de temas abordados]
```

## Ferramentas Disponíveis

### 1. `get_daily_note(date?)`
Obtém nota do dia especificado ou hoje.

```
get_daily_note("2026-05-24")
→ Retorna: conteúdo da nota
```

### 2. `create_daily_note(date?)`
Cria nota nova em estrutura YYYY-MM/YYYY-MM-DD.

```
create_daily_note("2026-05-24")
→ Cria: 00_Memoria/Diarias/2026-05/2026-05-24.md
```

### 3. `append_to_daily_note(content)`
Adiciona conteúdo ao final da nota do dia.

### 4. `list_daily_notes(month?)`
Lista todas as notas de um mês.

```
list_daily_notes("2026-05")
→ Retorna: [2026-05-24, 2026-05-23, ...]
```

### 5. `get_month_summary(year-month)`
Gera resumo de um mês inteiro.

## Workflow Automático

```
Início da conversa
    ↓
check: existe 2026-05-24.md?
    ├─ Não → create_daily_note()
    └─ Sim → get_daily_note()
    ↓
append novo registro
    ↓
Sincronizar com Obsidian
```

## Exemplos de Uso

### Iniciar Dia
```javascript
// Ao primeiro contato do dia
const note = await create_daily_note("2026-05-24");
```

### Adicionar Conversa
```javascript
// Após cada interação
const content = `
## Conversa 1 - ${time}
**Usuário**: ${userMessage}
**Kothar**: ${response}
**Tags**: #tema1 #tema2
`;
await append_to_daily_note(content);
```

### Ver Histórico do Mês
```javascript
// Revisar padrões
const month = await list_daily_notes("2026-05");
// Retorna: [24.md, 23.md, 22.md, ...]
```

## Limite de Uso
✅ **SEM LIMITE** - Armazenamento local ilimitado

← [[catalogo-habilidades]]
