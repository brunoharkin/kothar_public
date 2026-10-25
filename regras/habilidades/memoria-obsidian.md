---
name: obsidian-memory
description: Registrar e recuperar interações no Obsidian
version: 1.0.0
category: Memory Management
---

# Skill: Obsidian Memory

## Funcionalidade
Gerencia a memória persistente do Kothar no Obsidian, armazenando e recuperando contexto de interações.

## Ferramentas Disponíveis

### 1. `register_interaction`
Registra uma nova interação no documento do dia.

**Uso**:
```
register_interaction(
  userMessage="Sua pergunta aqui",
  agentResponse="Resposta do Kothar",
  context={
    timestamp="2026-05-24T14:30:00Z",
    category="desenvolvimento",
    tags=["#obsidian", "#mcp", "#setup"]
  }
)
```

### 2. `search_memory`
Busca notas relevantes na memória com busca semântica.

**Uso**:
```
search_memory(
  query="como configurar obsidian mcp",
  maxResults=5
)
```

### 3. `get_daily_note`
Obtém a nota do dia atual.

**Retorna**:
```
{
  content: string,
  created: timestamp,
  path: "00_Memoria/Diarias/2026-05/2026-05-24.md"
}
```

### 4. `create_daily_note`
Cria nota do dia se não existir.

**Retorna**:
```
{
  path: "00_Memoria/Diarias/2026-05/2026-05-24.md",
  initialized: true
}
```

### 5. `link_to_note`
Cria link entre notas para rastreabilidade.

**Uso**:
```
link_to_note(
  sourcePath="2026-05-24.md",
  targetPath="decisoes/escolher-mcp.md",
  relationship="mencionado-em"
)
```

## Workflow Recomendado

```
1. Ao iniciar: 
   get_daily_note() → criar se não existir

2. Durante conversa: 
   register_interaction() após cada resposta

3. Antes de decidir: 
   search_memory(query relevante)

4. Ao encerrar: 
   link_to_note() para relacionar contextos
```

## Estrutura de Armazenamento

```
00_Memoria/
├── Diarias/
│   ├── 2026-05/
│   │   ├── 2026-05-24.md  ← hoje
│   │   ├── 2026-05-23.md
│   │   └── ...
│   ├── 2026-04/
│   └── ...
├── Decisoes/
├── Aprendizados/
├── Projetos/
└── Skills/
```

## Limite de Uso
✅ **SEM LIMITE** - Local-first, offline ilimitadamente

## Voltar
← [[catalogo-habilidades]]
