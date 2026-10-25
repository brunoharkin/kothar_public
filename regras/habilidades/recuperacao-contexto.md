---
name: context-retrieval
description: Recuperar e usar contexto histórico
version: 1.0.0
category: Memory Management
---

# Skill: Context Retrieval

## Funcionalidade
Recupera contexto histórico relevante e integra nas decisões do agente.

## Quando Usar

### 1. Antes de Tomar Decisão
```
Usuário: "Como devo arquitetar isso?"
→ Buscar decisões arquiteturais anteriores
→ Verificar rationale
→ Decidir com contexto
```

### 2. Responder Pergunta sobre Histórico
```
Usuário: "Lembra daquela decisão sobre XYZ?"
→ search_memory("XYZ")
→ Citar: "[Visto em: 2026-05-20.md]"
```

### 3. Evitar Repetir Erros
```
Se decisão similar foi tentada antes:
→ Alertar o usuário
→ Explicar por que não funcionou
→ Sugerir alternativa
```

## Ferramentas Principais

- `search_memory(query)` - Busca semântica
- `get_decision_history(topic)` - Histórico de decisões
- `find_related_notes(note)` - Notas relacionadas
- `get_context_summary(date_range)` - Resumo do período

## Padrão de Resposta

Ao usar contexto, sempre incluir:

```markdown
**Contexto Encontrado**:
[Visto em: 2026-05-20.md]

**Situação Anterior**:
[Resumo breve]

**Decisão Anterior**:
[Qual foi decidido]

**Rationale**:
[Por que foi decidido assim]

**Aplicável Agora?**:
[Análise se ainda é relevante]
```

## Exemplos

### Exemplo 1: Decisão Anteriormente Documentada
```
Usuário: "Como devemos gerenciar estado em React?"
→ search_memory("state management React")
→ Encontra: "2026-05-18: Decidimos usar Zustand"
→ Resposta: "Conforme documentado em 2026-05-18.md, 
   decidimos usar Zustand porque..."
```

### Exemplo 2: Evitando Repetição
```
Usuário: "Devemos usar REST API?"
→ search_memory("REST API")
→ Encontra: "2026-05-15: Testamos e não funcionou porque..."
→ Resposta: "Tentamos isso antes (2026-05-15.md) e..."
```

## Limite de Uso
✅ **SEM LIMITE** - Busca local, sem restrições

← [[catalogo-habilidades]]
