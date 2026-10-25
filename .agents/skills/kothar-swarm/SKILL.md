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
- **SEGURANÇA:** Verifica que TODOS os subagentes aplicaram as regras de segurança antes de aceitar merge

### Agente Dev Frontend
- Atua SOMENTE na camada `frontend/paginas/` e `frontend/componentes/`
- Produz UI/UX fiel ao design aprovado
- Não toca em lógica de backend
- Entrega: componentes + validações visuais + tests unitários de UI

**🔒 REGRAS DE SEGURANÇA OBRIGATÓRIAS (Dev Frontend):**
```
❌ PROIBIDO: localStorage/sessionStorage para tokens, sessão ou dados de auth
❌ PROIBIDO: console.log com dados de sessão, tokens, senhas ou dados pessoais
❌ PROIBIDO: innerHTML ou dangerouslySetInnerHTML com dados do usuário sem sanitização
❌ PROIBIDO: Expor IPs, URLs de API internas ou dados de infraestrutura no código frontend
❌ PROIBIDO: Armazenar credenciais ou chaves de API no código frontend
✅ OBRIGATÓRIO: Tokens de autenticação gerenciados via HttpOnly Cookie (setado pelo backend)
✅ OBRIGATÓRIO: Validação de formulários com feedback visual antes de enviar ao backend
✅ OBRIGATÓRIO: Estados de erro que NÃO exponham stack traces ou dados internos
✅ OBRIGATÓRIO: Limpar console.log de debug antes de entregar
```

### Agente Dev Backend
- Atua SOMENTE na camada `backend/` e `backend/banco-de-dados/`
- Implementa regra de negócio, APIs, schemas
- Não toca em frontend
- Entrega: endpoints + validações + tests de integração

**🔒 REGRAS DE SEGURANÇA OBRIGATÓRIAS (Dev Backend):**
```
❌ PROIBIDO: Endpoint público ou de autenticação SEM rate limiting
❌ PROIBIDO: Aceitar req.body sem validação (Zod/Pydantic/Joi obrigatório)
❌ PROIBIDO: SQL com interpolação direta (usar queries parametrizadas)
❌ PROIBIDO: Logar senhas, tokens ou dados sensíveis
❌ PROIBIDO: Sessão/auth via localStorage — usar session store server-side (Redis/Postgres)
❌ PROIBIDO: Retornar stack traces ou erros internos na resposta da API
❌ PROIBIDO: CORS com wildcard (*) em produção
✅ OBRIGATÓRIO: Rate limiting em login (max 5 tentativas / 15 min por IP)
✅ OBRIGATÓRIO: Rate limiting geral em rotas públicas (max 100 req / 15 min)
✅ OBRIGATÓRIO: Headers de segurança (HSTS, X-Content-Type-Options, X-Frame-Options)
✅ OBRIGATÓRIO: Token em HttpOnly Cookie (Secure + SameSite=Strict)
✅ OBRIGATÓRIO: Sessão com expiração real no servidor
✅ OBRIGATÓRIO: Logout que invalida sessão no servidor (não só deleta cookie)
✅ OBRIGATÓRIO: Input validado em TODAS as rotas POST/PUT/PATCH
```

### Agente QA (Testador)
- Avalia sintaxe, linters, testes e DoD dos outros agentes
- Roda segurança scan em todo código produzido
- Valida que nada fora do escopo foi tocado
- Entrega: relatório DoD binário

**🔒 CHECKLIST DE SEGURANÇA OBRIGATÓRIO (Agente QA):**
```
VERIFICAR EM TODO CÓDIGO PRODUZIDO PELOS SUBAGENTES:
[ ] Rate limiting presente em rotas públicas e de autenticação?
[ ] localStorage/sessionStorage usado para tokens ou sessão? → REJEITAR
[ ] console.log expõe dados sensíveis? → REJEITAR
[ ] Headers de segurança configurados no backend?
[ ] CORS restrito (sem wildcard *)?
[ ] Input validado em rotas POST/PUT/PATCH?
[ ] SQL usa queries parametrizadas (sem interpolação)?
[ ] Portas de debug/admin expostas publicamente?
[ ] Credenciais hardcoded no código? → REJEITAR
[ ] Stack traces expostos nas respostas de erro? → REJEITAR

SE QUALQUER ITEM FALHAR → DEVOLVER PARA O AGENTE RESPONSÁVEL.
NÃO ACEITAR ENTREGA COM FALHA DE SEGURANÇA.
```

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

