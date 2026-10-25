---
name: gate-producao
description: >-
  Gate FINAL obrigatório antes de qualquer deploy em produção. Checklist binário de 15 itens
  de segurança que DEVE ser verificado antes de enviar código para ambiente de produção.
  Funciona como o gate-seguranca-credenciais mas cobre segurança geral: rate limiting,
  session store, headers, logs, portas e CORS. Sem exceções.
---

# Skill: Gate de Produção — Checklist de Segurança para Deploy

> **REGRA INEGOCIÁVEL.** Nenhum código vai para produção sem passar por este gate.
> Se QUALQUER item for ❌ → BLOQUEIO DE DEPLOY. Bruno deve aprovar cada exceção individualmente.

---

## 🔴 A Regra (em uma frase)

**Kothar NUNCA pode declarar "pronto para produção" sem verificar TODOS os 15 itens deste gate.**

---

## 📋 Checklist Obrigatório — 15 Itens

### Autenticação & Sessão
```
[ ] GP1 — Login tem rate limiting (max 5 tentativas / 15 min por IP)
        Verificar: middleware de rate limit configurado na rota de login.
        Se ausente → BLOQUEIO.

[ ] GP2 — Sessão armazenada server-side (Redis/Postgres/Memcached)
        Verificar: session store configurado, NÃO usa localStorage/sessionStorage.
        Se localStorage para sessão → BLOQUEIO.

[ ] GP3 — Token em HttpOnly Cookie com Secure + SameSite=Strict
        Verificar: set-cookie no backend com flags corretas.
        Se token em localStorage ou cookie sem HttpOnly → BLOQUEIO.

[ ] GP4 — Sessão tem expiração real no servidor (configurável, default 24h)
        Verificar: TTL configurado no session store.
        Se expiração apenas no cookie (sem invalidação server-side) → BLOQUEIO.

[ ] GP5 — Logout invalida sessão no servidor (não só deleta cookie local)
        Verificar: endpoint de logout destrói sessão no store.
        Se logout apenas limpa cookie → BLOQUEIO.
```

### Headers & Transporte
```
[ ] GP6 — HTTPS obrigatório (HTTP redireciona para HTTPS)
        Verificar: redirecionamento 301/302 de HTTP → HTTPS.
        Se HTTP aceita conexão sem redirecionar → BLOQUEIO.

[ ] GP7 — Headers de segurança configurados:
        - Strict-Transport-Security (HSTS)
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY (ou SAMEORIGIN se iframe próprio)
        - Referrer-Policy: strict-origin-when-cross-origin
        Verificar: curl -I no endpoint.
        Se QUALQUER header crítico ausente → BLOQUEIO.

[ ] GP8 — CORS restrito a domínios permitidos
        Verificar: Access-Control-Allow-Origin NÃO é wildcard (*) em produção.
        Se wildcard em produção → BLOQUEIO.
```

### Dados & Logs
```
[ ] GP9 — Zero console.log com dados de sessão/token/dados pessoais no frontend
        Verificar: grep 'console.log' no frontend, analisar conteúdo.
        Se console.log expõe dados sensíveis → BLOQUEIO.

[ ] GP10 — Logs de backend não expõem credenciais, tokens ou senhas
         Verificar: grep em logger.info/error/warn por variáveis sensíveis.
         Se log expõe credencial → BLOQUEIO.

[ ] GP11 — Input do usuário validado (Zod/Pydantic/Joi) em TODAS as rotas POST/PUT/PATCH
         Verificar: toda rota que recebe body tem middleware de validação.
         Se rota aceita body cru sem validação → BLOQUEIO.
```

### Infra & Portas
```
[ ] GP12 — Portas de debug/admin não expostas publicamente
         Verificar: lsof -i ou netstat para portas abertas.
         Se porta de debug acessível externamente → BLOQUEIO.

[ ] GP13 — .env não commitado (.gitignore verificado)
         Verificar: grep '.env' .gitignore + git status.
         Se .env no staging/commit → BLOQUEIO.

[ ] GP14 — Variáveis de ambiente de produção configuradas no servidor (não no código)
         Verificar: process.env.X usado sem fallback hardcoded.
         Se credencial hardcoded como fallback → BLOQUEIO.
```

### Resiliência
```
[ ] GP15 — Rate limiting em rotas públicas e de API
         Verificar: middleware de rate limit em rotas públicas.
         Se rota pública aceita requisições ilimitadas → BLOQUEIO.
```

---

## 🚦 Quando Aplicar Este Gate

```
□ Antes de git push para branch de produção (main/master)
□ Antes de deploy em VPS/servidor de produção
□ Antes de declarar "Pronto para produção" no DoD
□ Antes de atualizar container/image em produção
□ Em toda auditoria periódica de segurança
```

---

## 🛑 Procedimento quando falhar

```
1. PARAR o deploy imediatamente
2. Identificar quais itens falharam (listar com números GP1-GP15)
3. Mostrar para Bruno: "Gate de produção falhou em [GP1, GP7, GP15]"
4. Propor correção MÍNIMA para cada item
5. AGUARDAR Bruno aprovar
6. Aplicar correções
7. Re-rodar o gate COMPLETO (não só os itens que falharam)
8. Se todos ✅ → liberar deploy
```

---

## 📋 Comandos de Verificação Rápida

```bash
# GP9 — Console.log sensível no frontend
grep -rn 'console.log' --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" frontend/ | grep -iE '(token|session|senha|password|auth|user|email)'

# GP10 — Logs sensíveis no backend
grep -rn '(logger\.|console\.log|console\.error)' --include="*.ts" --include="*.js" --include="*.py" backend/ | grep -iE '(token|password|secret|key|senha)'

# GP12 — Portas expostas
lsof -i -P -n | grep LISTEN

# GP13 — .env no gitignore
grep -E '^\.env' .gitignore && echo '✅ .env ignorado' || echo '❌ .env NÃO está no .gitignore — BLOQUEIO'

# GP15 — Rate limit presente
grep -rn 'rateLimit\|rate_limit\|RateLimiter\|slowapi\|limit_req' --include="*.ts" --include="*.js" --include="*.py" backend/
```

---

## 🔗 Skills Relacionadas

- `gate-seguranca-credenciais` — Gate específico para credenciais no código
- `kothar-seguranca` — Regras intrínsecas de segurança
- `kothar-dod` — DoD de Deploy em Produção (PR1-PR10) referencia este gate
- `definition-of-done` — DoD por tipo de feature
- `kothar-auditoria-seguranca` — Auditoria profunda pós-deploy

---

## 📝 Histórico de Violações

| Data | Projeto | Itens Violados | O que aconteceu |
|---|---|---|---|
| 2026-10-15 | novo-site-ugarit | GP1, GP2, GP3, GP9 | Deploy em produção com localStorage para sessão, sem rate limiting, console.log com dados de sessão |

---

*Skill criada em 2026-10-17 — Bruno Harkin / Kothar v4.0*
*Qualquer exceção precisa de aprovação EXPLÍCITA de Bruno.*
