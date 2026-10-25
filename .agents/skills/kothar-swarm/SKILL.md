---
name: kothar-swarm
description: >-
  Skill do Kothar: Orquestração Swarm Multi-Agente. Ativar quando a tarefa tocar
  Frontend E Backend simultaneamente, ou quando a complexidade for alta (>1 dia de trabalho).
  Divide o trabalho em papéis paralelos: Dev Frontend, Dev Backend, QA Testador.
  O Kothar Core assume o papel de Orquestrador + Revisor.
---

# Skill: Kothar Swarm Router — Orquestração Multi-Agente

> **Princípio:** Para tarefas que afetam mais de 1 camada ou alta complexidade, o Kothar atua como Orquestrador, delegando para subagentes paralelos.

## Quando Ativar o Swarm

```
✅ Ativar quando:
   - Feature toca Frontend + Backend simultaneamente
   - Refatoração extensa (>10 arquivos)
   - Complexidade estimada > 1 dia de trabalho
   - Build de sistema do zero

❌ NÃO ativar para:
   - Correção de bug simples (1 arquivo)
   - Ajuste de UI isolado
   - Pequena feature em 1 camada
```

---

## Papéis do Swarm

### Kothar Core (Orquestrador)
- Valida o design contra o Discovery aprovado
- Distribui tarefas entre os agentes
- Recusa código que viole "Menor Escopo"
- Sincroniza estado em `estado-atual.md`
- Faz o merge final e DoD

### Agente Dev Frontend
- Atua SOMENTE na camada `frontend/paginas/` e `frontend/componentes/`
- Produz UI/UX fiel ao design aprovado
- Não toca em lógica de backend
- Entrega: componentes + validações visuais + tests unitários de UI

### Agente Dev Backend
- Atua SOMENTE na camada `backend/` e `backend/banco-de-dados/`
- Implementa regra de negócio, APIs, schemas
- Não toca em frontend
- Entrega: endpoints + validações + tests de integração

### Agente QA (Testador)
- Avalia sintaxe, linters, testes e DoD dos outros agentes
- Roda segurança scan em todo código produzido
- Valida que nada fora do escopo foi tocado
- Entrega: relatório DoD binário

---

## Fluxo de Orquestração

```
1. Kothar Core lê o design.md travado
2. Divide em sub-tarefas por papel (Frontend/Backend/QA)
3. Agenda subagentes com escopo isolado
4. Subagentes trabalham no project-sandbox
5. QA valida cada entrega com DoD
6. Kothar Core revisa + merge
7. Relatório final para Bruno
```

---

## Sincronização de Estado

Todo estado é logado em `estado-atual.md` do projeto:
```markdown
## Estado Atual — [data]
### Swarm Ativo
- Frontend: [status] — [última ação]
- Backend: [status] — [última ação]
- QA: [status] — [última ação]

### Próximos Passos
[checklist do Kothar Core]
```

---

*Kothar v4.0 — Swarm Router | Ugarit Digital*

