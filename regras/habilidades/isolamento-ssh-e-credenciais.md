---
name: isolamento-ssh-e-credenciais
description: Regra CRÍTICA - ISOLAMENTO TOTAL de chaves SSH e credenciais API por projeto. Cada projeto = chave única + credenciais isoladas.
metadata:
  tipo: skill-seguranca
  data: 2026-08-25
  criticidade: critica
  versao: 1.0
  obrigatoria: true
---

# 🛡️ ISOLAMENTO CRÍTICO DE CHAVES SSH E CREDENCIAIS

> **REGRA CRÍTICA.** Cada projeto DEVE ter suas próprias chaves SSH e credenciais API, completamente isoladas. Misturar = COMPROMETIMENTO DE SEGURANÇA.

---

## 🔴 REGRA DE OURO ABSOLUTA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🏛️ PRINCÍPIO DE ISOLAMENTO KOTHAR v3.0                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  1️⃣  CADA PROJETO = 1 CHAVE SSH ÚNICA                                     ║
║  2️⃣  CADA PROJETO = 1 ARQUIVO .env ISOLADO                                ║
║  3️⃣  CADA PROJETO = 1 ENTRADA NO ~/.ssh/config                             ║
║  4️⃣  NUNCA COMPARTILHAR CHAVES ENTRE PROJETOS                               ║
║  5️⃣  NUNCA COLOCAR CREDENCIAIS NO CÓDIGO                                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 ESTRUTURA DE DIRETÓRIOS

```
~/.ssh/
├── id_ed25519                  # Chave DEFAULT (pessoal)
├── id_ed25519.pub
├── config                      # Configuração SSH (um Host por projeto)
│
├── id_ed25519_kothar           # KOTHAR
├── id_ed25519_kothar.pub
│
├── id_ed25519_crm_sophia       # CRM SOPHIA
├── id_ed25519_crm_sophia.pub
│
├── id_ed25519_chronodesk       # CHRONODESK
├── id_ed25519_chronodesk.pub
│
├── id_ed25519_orby_ia          # ORBY.IA
├── id_ed25519_orby_ia.pub
│
├── id_ed25519_cofre            # COFRE
├── id_ed25519_cofre.pub
│
└── id_ed25519_monitor_admin    # MONITOR ADMIN
└── id_ed25519_monitor_admin.pub

~/.envs/                        # CREDENCIAIS ISOLADAS
├── kothar.env
├── crm_sophia.env
├── chronodesk.env
├── orby_ia.env
├── cofre.env
└── monitor_admin.env
```

---

## 🔑 QUANDO CRIAR CHAVE SSH PARA PROJETO

### ✅ FAZER (Procedimento Correto)

```bash
# 1. IDENTIFICAR o projeto
#    Pergunte: "Qual projeto precisa desta chave?"

# 2. CRIAR chave com NOME DO PROJETO
ssh-keygen -t ed25519 \
  -C "bruno@ugarit.digital" \
  -f ~/.ssh/id_ed25519_NOME_DO_PROJETO \
  -N ""

# 3. MOSTRAR a chave pública para adicionar ao GitHub
cat ~/.ssh/id_ed25519_NOME_DO_PROJETO.pub

# 4. CONFIGURAR SSH CONFIG
#    Adicionar entrada no ~/.ssh/config

# 5. CONFIGURAR o remote do git
git remote set-url origin git@NOME-DO-HOST:org/repo.git
```

### ❌ NUNCA FAZER

```bash
# ❌ NÃO USAR a chave default para projetos
ssh-keygen  # Sem -f = usa id_ed25519 default

# ❌ NÃO REUTILIZAR chave de outro projeto
# Se já existe ~/.ssh/id_ed25519_crm_sophia, NÃO usar para outro projeto

# ❌ NÃO COLOCAR no mesmo arquivo
cat ~/.ssh/id_ed25519 >> ~/.ssh/config  # ERRADO!

# ❌ NÃO COMMITAR chave privada
git add ~/.ssh/id_ed25519_meu_projeto
```

---

## 📝 MODELO: ~/.ssh/config (um Host por projeto)

```bash
# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR - Sistema de Orquestração
# ═══════════════════════════════════════════════════════════════════════════════

Host github-kothar
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_kothar
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# CRM SOPHIA
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-crm-sophia
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_crm_sophia
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# CHRONODESK
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-chronodesk
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_chronodesk
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# ORBY.IA
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-orby-ia
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_orby_ia
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# COFRE (Vault Obsidian)
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-cofre
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_cofre
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# MONITOR ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-monitor-admin
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_monitor_admin
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# NOVO SITE UGARIT
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com-novo-site-ugarit
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_novo_site_ugarit
    IdentitiesOnly yes

# ═══════════════════════════════════════════════════════════════════════════════
# CHAVE DEFAULT (pessoal)
# ═══════════════════════════════════════════════════════════════════════════════

Host github.com
    HostName github.com
    User git
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
```

---

## 🔐 QUANDO RECEBER CREDENCIAL API (do Bruno)

### ✅ PROCEDIMENTO CORRETO

```
QUANDO Bruno compartilhar: API key, senha, token, URL com credencial

1. 📝 REGISTRAR imediatamente
   - Criar arquivo ~/.envs/PROJETO.env
   - Adicionar: PROJETO_NOME_CHAVE=valor

2. 🔒 ISOLAR
   - chmod 600 ~/.envs/PROJETO.env
   - Adicionar ~/.envs/ ao .gitignore GLOBAL

3. 📖 USAR
   - Em código: process.env.CHAVE_DO_PROJETO
   - NUNCA hardcoded no código

4. 🚫 ESQUECER
   - Não mencionar o valor no chat após registrar
   - Não salvar em variáveis temporárias
   - Não mostrar em logs
```

### ❌ NUNCA FAZER

```
❌ Colocar API key no código
❌ Fazer console.log() com a chave
❌ Commitar arquivo .env
❌ Colocar em variável de ambiente global
❌ Compartilhar valor no chat depois de registrado
```

---

## 🚨 VERIFICAÇÃO OBRIGATÓRIA (Antes de QUALQUER commit)

```bash
# 1. Verificar se NÃO há arquivo .env commitado
grep -r "\.env" .gitignore || echo "❌ .env NÃO está no .gitignore"

# 2. Verificar se credenciais estão isoladas
grep -rEn "(sk_|pk_|api_key|secret|password)" \
  --include="*.ts" --include="*.js" \
  backend/ frontend/ || echo "✅ Nenhuma credencial no código"

# 3. Verificar se chave SSH está correta para o projeto
git remote -v | grep -oE "git@[a-zA-Z0-9.-]+:" | head -1
```

---

## 📊 REGISTRO DE CHAVES POR PROJETO

| Projeto | Chave SSH | Host SSH | Remote Git |
|---------|-----------|----------|------------|
| kothar | `id_ed25519_kothar` | `github-kothar` | `git@github-kothar:...` |
| crm-Sophia | `id_ed25519_crm_sophia` | `github.com-crm-sophia` | `git@github.com-crm-sophia:...` |
| chronodesk | `id_ed25519_chronodesk` | `github.com-chronodesk` | `git@github.com-chronodesk:...` |
| Orby.ia | `id_ed25519_orby_ia` | `github.com-orby-ia` | `git@github.com-orby-ia:...` |
| Cofre | `id_ed25519_cofre` | `github.com-cofre` | `git@github.com-cofre:...` |
| Monitor-Admin | `id_ed25519_monitor_admin` | `github.com-monitor-admin` | `git@github.com-monitor-admin:...` |
| novo-site-ugarit | `id_ed25519_novo_site_ugarit` | `github.com-novo-site-ugarit` | `git@github.com-novo-site-ugarit:...` |

---

## 🔧 SCRIPT DE VERIFICAÇÃO (kothar-ssh-verify.sh)

```bash
#!/bin/bash
# kothar-ssh-verify.sh - Verifica isolamento de chaves SSH

echo "🔍 Verificando isolamento SSH por projeto..."
echo ""

# Verificar estrutura de diretórios
if [ ! -d "$HOME/.ssh" ]; then
    echo "❌ ~/.ssh não existe"
    exit 1
fi

# Projetos esperados
PROJECTS=(
    "kothar"
    "crm_sophia"
    "chronodesk"
    "orby_ia"
    "cofre"
    "monitor_admin"
    "novo_site_ugarit"
)

echo "Verificando chaves SSH por projeto..."
echo ""

total=0
ok=0

for project in "${PROJECTS[@]}"; do
    total=$((total + 1))
    key_file="$HOME/.ssh/id_ed25519_$project"
    
    if [ -f "$key_file" ]; then
        echo "✅ $project: $(basename $key_file)"
        ok=$((ok + 1))
    else
        echo "⚠️  $project: chave não encontrada"
    fi
done

echo ""
echo "Resultado: $ok/$total projetos com chave SSH"
echo ""

# Verificar ~/.ssh/config
if grep -q "Host github-kothar" "$HOME/.ssh/config" 2>/dev/null; then
    echo "✅ ~/.ssh/config configurado"
else
    echo "❌ ~/.ssh/config não está configurado corretamente"
fi

# Verificar .envs
if [ -d "$HOME/.envs" ]; then
    echo "✅ Diretório ~/.envs existe"
else
    echo "⚠️  Diretório ~/.envs não existe (criar com: mkdir -p ~/.envs)"
fi
```

---

## 📋 CHECKLIST ANTES DE QUALQUER GIT PUSH

```
ANTES DE: git push

□ 1. Verificar qual projeto estou
□ 2. Verificar se remote usa a chave correta
□ 3. git remote -v mostra o Host SSH correto
□ 4. .env NÃO está commitado
□ 5. Nenhuma credencial hardcoded no código
□ 6. ssh -T git@HOST funciona para este projeto
□ 7. Hook de segurança passou (se configurado)
```

---

## 🚫 ERRO CRÍTICO: MISTURA DE CHAVES

### ❌ SINTOMAS DO PROBLEMA

```
- "Permission denied (publickey)" para projeto que já funcionava
- Commit vai para repositório errado
- Chave foi sobrescrita por outro projeto
- remote set-url alterou para outro repositório
```

### ✅ CAUSA RAIZ

```
- Usou ssh-keygen sem -f (sobrescreveu default)
- git remote set-url sem querer
- Editou ~/.ssh/config errado
- Copiou chave de outro projeto
```

### 🔧 COMO CORRIGIR

```bash
# 1. Identificar qual chave era do projeto
# 2. Recriar a chave (se sobrescrita)
ssh-keygen -t ed25519 -C "projeto@ugarit" -f ~/.ssh/id_ed25519_NOME_DO_PROJETO -N ""

# 3. Adicionar nova chave ao GitHub do projeto
cat ~/.ssh/id_ed25519_NOME_DO_PROJETO.pub

# 4. Corrigir remote
git remote set-url origin git@HOST-CORRETO:org/repo.git

# 5. Verificar
ssh -T git@HOST-CORRETO
```

---

## 📖 REGRA DE OURO FINAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  🎯 QUANDO O BRUNO MANDAR CRIAR CHAVE SSH OU CREDENCIAL:                    │
│                                                                              │
│  1️⃣  PERGUNTAR: "Qual projeto?"                                             │
│  2️⃣  CRIAR com nome do projeto no arquivo                                   │
│  3️⃣  CONFIGURAR ~/.ssh/config com Host único                               │
│  4️⃣  ATUALIZAR remote do git para usar Host correto                         │
│  5️⃣  REGISTRAR no arquivo de projetos                                      │
│  6️⃣  ADICIONAR .env ao .gitignore GLOBAL                                   │
│                                                                              │
│  🚫 NUNCA REUTILIZAR, NUNCA COMPARTILHAR, NUNCA MISTURAR                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Skills Relacionadas

- `gate-seguranca-credenciais.md` - Bloqueio de credenciais no código
- `seguranca.md` - Scanner de vulnerabilidades
- `project-isolation.md` - Isolamento de projetos (arquivos)
- `skill-isolamento-projetos.md` - Skill obrigatória de isolamento

---

*Skill CRÍTICA criada em 2026-08-25 — Bruno Harkin / Kothar v3.0*
*Esta skill é OBRIGATÓRIA para todos os agentes Kothar*
