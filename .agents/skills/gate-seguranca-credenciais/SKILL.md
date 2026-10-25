---
name: gate-seguranca-credenciais
description: >-
  Regra INEGOCIÁVEL. Credenciais NO CÓDIGO = bloqueio total. Kothar deve scanar ANTES de qualquer commit, push ou declaração de pronto.
---

# Skill: Gate de Segurança Anti-Credenciais

> **REGRA INEGOCIÁVEL.** Se Kothar encontrar credencial em código = BLOQUEIO TOTAL.
> Não importa o estágio (desenvolvimento, teste, produção, "vou corrigir depois").
> Bruno foi explícito: credenciais expostas no código = erro que NÃO pode acontecer.

---

## 🔴 A Regra (em uma frase)

**Kothar NUNCA pode:**
- ❌ Commitar código com credencial hardcoded
- ❌ Fazer push de código com credencial hardcoded
- ❌ Declarar "Pronto" se houver credencial exposta
- ❌ Dizer "depois eu corrijo" — credencial exposta = CORRIGIR AGORA

---

## 🔍 O que é "credencial" (lista exaustiva)

```
- process.env.X hardcoded (deveria ser process.env.X sem valor)
- Strings que começam com: sk_, pk_, ghp_, gho_, AKIA, xoxb, xoxp
- Qualquer string que case com: api_key, apikey, api-key
- Qualquer string que case com: secret, password, passwd, pwd
- URLs com credencial embutida: postgres://user:pass@host
- Tokens de acesso/sessão
- JWT hardcoded
- PRIVATE_KEY, PUBLIC_KEY em código
- Cookies de sessão em código (.ts, .js, .tsx, .jsx, .py, .env, .yml)
- .env commitado (deveria estar no .gitignore)
- .pem, .key, .crt, .pfx commitados
- Comentários com credencial ("senha do banco é XXX")
```

---

## 🛑 Quando aplicar o gate (checklist)

**ANTES de cada uma destas ações:**

```
□ git add / git commit
□ git push
□ Criar arquivo de configuração
□ Declarar "Pronto" em qualquer DoD
□ Responder "está tudo certo" sobre deploy
□ Editar .env, .env.example
□ Compartilhar código (screenshot, gist, paste)
```

---

## 🚦 Procedimento quando encontrar credencial

```
1. PARAR imediatamente a ação atual
2. Identificar o arquivo e linha exata
3. Mostrar pra Bruno: "Encontrei credencial em [arquivo:linha]"
4. Propor correção (variável de ambiente)
5. AGUARDAR Bruno aprovar
6. Corrigir
7. Re-scanar pra confirmar que sumiu
8. Continuar o que estava fazendo
```

**NÃO continue o trabalho sem resolver.** Credencial exposta = prioridade #1.

---

## 📋 Comando de scan (Kothar DEVE rodar ANTES de commit/push)

```bash
# Scan geral
grep -rEn "(sk_[a-zA-Z0-9]{20,}|pk_[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9a-zA-Z]+|api[_-]?key|secret|password|passwd)" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.env" --include="*.yml" --include="*.yaml" \
  backend/ frontend/ 2>/dev/null

# Scan específico de URL com credencial
grep -rEn "(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@" --include="*.ts" --include="*.js" --include="*.env" backend/ frontend/ 2>/dev/null

# Verificar se .env está no .gitignore
grep -E "^\.env$" .gitignore && echo "✅ .env ignorado" || echo "❌ .env NÃO está no .gitignore — BLOQUEIO"
```

**Se QUALQUER um retornar match = BLOQUEIO.**

---

## ✅ Como armazenar credenciais (forma correta)

```
1. Criar arquivo .env (na raiz do projeto)
2. Adicionar .env ao .gitignore
3. Criar .env.example com as MESMAS chaves mas valores VAZIOS
4. Em código, usar: process.env.MINHA_VARIAVEL (sem valor literal)
5. No deploy, configurar as variáveis no painel do provedor (Vercel, Railway, etc)
```

**Exemplo ERRADO:**
```typescript
// ❌ NUNCA FAZER ISSO
const dbUrl = "postgres://user:senha123@host:5432/db"
const apiKey = "sk-abc123def456ghi789"
```

**Exemplo CERTO:**
```typescript
// ✅ SEMPRE ASSIM
const dbUrl = process.env.DATABASE_URL
const apiKey = process.env.OPENAI_API_KEY

if (!dbUrl) throw new Error("DATABASE_URL não configurada")
if (!apiKey) throw new Error("OPENAI_API_KEY não configurada")
```

---

## 📝 Como documentar credenciais no cofre

**NUNCA no código (vai pro git).** Sempre em nota do Obsidian:

```
00_Memoria/Credenciais/{projeto}/
├── producao.md     ← valores REAIS de produção
├── homologacao.md  ← valores de homologação
└── .gitignore      ← garante que não vaza
```

**OU** em gerenciador de senhas (1Password, Bitwarden, etc).

---

## 🚨 Casos de violação recente (do histórico)

| Data | Caso | O que aconteceu | Como evitar agora |
|---|---|---|---|
| 2026-06-10 | Bruno reportou que Kothar deixou credenciais expostas no código | Múltiplas ocorrências, sem scan | Esta skill + scan obrigatório |

**Bruno foi explícito:** "isso já é uma regra que não poderia ser quebrada". Por isso essa skill é **crítica**.

---

## 🔗 Skills relacionadas

- `principio-menor-escopo.md` — escopo não inclui "deixar credencial exposta"
- `definition-of-done.md` — item obrigatório em todo DoD
- `fluxo-discovery-design-build.md` — gate de segurança na fase Verify
- `seguranca.md` — skill irmã (scanner de vulnerabilidades gerais)
- `feedback-anti-puxa-saco.md` (memória automática) — gate global

---

*Skill INEGOCIÁVEL criada em 2026-06-10 — Bruno Harkin / Kothar*
*Qualquer exceção precisa de aprovação EXPLÍCITA de Bruno.*
