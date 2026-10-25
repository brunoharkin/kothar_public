← [[catalogo-habilidades]]

# Segurança — Kothar Security Shield

> **v2.0 — Atualizado em 2026-06-10** com gate explícito + link pra skill operacional

## O que é

Ferramenta ativa de segurança do Kothar. Bloqueia credenciais antes de chegarem ao código, escaneia projetos inteiros por vulnerabilidades e mantém regras de segurança em todo trabalho de desenvolvimento.

## 🔴 REGRA INEGOCIÁVEL (2026-06-10)

**Credenciais NUNCA no código.** Ver skill operacional completa:
- `01_Kothar/habilidades/gate-seguranca-credenciais.md` (scanner + comandos)
- `01_Kothar/instrucoes/evolucao/regra-credenciais-expostas.md` (regra-mãe)

**Bruno foi explícito:** "isso já é uma regra que não poderia ser quebrada". Esta skill é **crítica**.

## Ferramenta

**Scanner:** `/home/bruno/.local/bin/kothar-sec-scan`

```bash
kothar-sec-scan .               # escaneia projeto inteiro
kothar-sec-scan arquivo.ts      # escaneia arquivo específico
kothar-sec-scan --hook          # modo hook automático
```

**Scanner manual** (ver `gate-seguranca-credenciais.md` para lista completa):
```bash
grep -rEn "(sk_[a-zA-Z0-9]{20,}|pk_[a-zA-Z0-9]{20,}|api[_-]?key|secret|password)" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.env" \
  backend/ frontend/
```

## Proteções Ativas

| Proteção | Como funciona |
|---|---|
| **Credenciais no código** | Hook PreToolUse bloqueia escrita antes de acontecer + scanner manual em commit/push |
| **Secrets do usuário** | Usados via env var, nunca escritos em código |
| SQL Injection | Detecção de concatenação direta em queries |
| XSS | Detecção de innerHTML/eval com input externo |
| Command Injection | Detecção de interpolação em exec/spawn |
| .env exposto | Verifica .gitignore antes de criar .env |

## Credenciais do Usuário

Quando Bruno compartilha uma API key ou senha no chat:
1. O Kothar **usa** a credencial para configurar o projeto
2. Armazena **apenas** no `.env` local (nunca em código)
3. Cria `.env.example` com a chave mas valor vazio
4. **Não menciona** o valor real novamente no chat

## Hook Automático

Configurado em `~/.claude/settings.json`:
- **PreToolUse (Write/Edit)** — escaneia conteúdo antes de escrever
- Credencial detectada → **bloqueia** a escrita e explica como usar env var

## 🆕 Gate Pré-Commit (adicionado 2026-06-10)

**ANTES de qualquer `git commit` ou `git push`:**
1. Rodar `kothar-sec-scan` (modo `--hook`)
2. Verificar `.env` no `.gitignore`
3. Se QUALQUER credencial for detectada → **BLOQUEIO TOTAL**
4. Não declarar "Pronto" sem scan limpo

Ver `01_Kothar/habilidades/gate-seguranca-credenciais.md` para o procedimento completo.

## Skill completa
`.claude/skills/security/SKILL.md` + `01_Kothar/habilidades/gate-seguranca-credenciais.md`
