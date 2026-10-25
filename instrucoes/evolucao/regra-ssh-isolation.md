---
name: regra-ssh-isolation
description: "Regra CRÍTICA (2026-06-18): Kothar DEVE validar chave SSH ANTES de qualquer operação git. Cada projeto = uma chave dedicada."
metadata:
  tipo: regra-comportamental
  data: 2026-06-18
  autor: Bruno Harkin
  origem: erro-009-contaminacao-projetos-ssh
  severidade: CRITICA
---

# SSH ISOLATION RULE

> **⚠️ REGRA CRÍTICA — Implementada 2026-06-18**
> Erro que originou: Kothar usou chave `bioleads` para trabalhar em `disparo-em-massa`.
> Resultado: contaminação de projetos, perda de contexto, erros累积.

---

## A Regra

### Antes de QUALQUER operação git, Kothar DEVE:

```
1. IDENTIFICAR projeto atual (pwd)
2. IDENTIFICAR projeto do remote (url do repo)
3. IDENTIFICAR chave SSH correta para este projeto
4. MOSTRAR para Bruno antes de executar
5. AGUARDAR confirmação
```

---

## Tabela de Chaves SSH por Projeto

| Projeto | Chave SSH | Remote Git |
|--------|-----------|------------|
| bioleads | `id_ed25519_bioleads` | `git@github.com:appsugarit-dev/BioLeads.git` |
| disparo-em-massa | `id_ed25519_disparo-em-massa` | `git@github.com:appsugarit-dev/disparo_em_massa.git` |
| ratoflix | `id_ed25519_ratoflix` | `git@github-bibliotecasapps:bibliotecasapps/Ratoflix.git` |
| linkdabio | `id_ed25519_linkdabio` | `git@github.com:appsugarit-dev/linkdabio.git` |
| orby | `id_ed25519_orby` | (verificar) |
| chronodesk | `id_ed25519_chronodesk` | `git@github.com-chronodesk:agestrategia360-sudo/ChronoDesk.git` |
| cofre | `id_ed25519_cofre` | `git@github.com-cofre:agestrategia360-sudo/Cofre.git` |
| kothar | `id_ed25519_kothar` | (verificar) |

**⚠️ Regra de ouro: SE a chave não corresponde ao projeto, NÃO EXECUTA.**

---

## Template Obrigatório (antes de git clone/pull/push)

```
🔐 SSH VALIDATION:

Projeto atual: [NOME]
Chave SSH correta: [NOME_DA_CHAVE]
Operação: [clone/pull/push]
Remote: [URL COMPLETA]

⚠️ Se a chave não corresponde ao projeto:
   "ERRO: chave [X] não corresponde ao projeto [Y]. 
    Chave correta é [Z]. Posso usar [Z]? (sim/não)"
```

---

## Quando a Chave Estiver Errada

### Situação: Kothar detectou chave errada
```
🔐 SSH VALIDATION:

❌ ERRO DETECTADO:
- Projeto: [NOME_DO_PROJETO]
- Chave usada: [CHAVE_ERRADA]
- Chave correta: [CHAVE_CERTA]

Motivo: chave [ERRADA] pertence ao projeto [OUTRO_PROJETO].
Usar chave errada = contaminar contextos.

Ação: Parar execução até Bruno autorizar.
```

### Situação: Bruno pediu para usar chave errada
```
⚠️ Bruno autorizou chave errada:

Entendido. Usando [CHAVE_ERRADA] para [OPERAÇÃO].
Isso pode causar [RISCO]. Tem certeza? (sim/não)

⚠️ Risco: contextos contaminados, operações no projeto errado
```

---

## Operações que REQUEREM Validação SSH

| Operação | Requer Validação? |
|----------|-------------------|
| `git clone` | ✅ SEMPRE |
| `git pull` | ✅ SEMPRE |
| `git push` | ✅ SEMPRE |
| `git fetch` | ✅ SEMPRE |
| `git remote -v` | ⚠️ Para verificar |
| `ssh user@host` | ✅ SEMPRE (VPS) |

---

## Auto-Correção (quando detectar erro)

Se Kothar detectar que está prestes a usar chave errada:

1. **PARAR imediatamente**
2. **Reportar o erro:**
   ```
   🔴 ALERTA SSH ISOLATION:
   
   Detectei que vou usar a chave ERRADA.
   
   Projeto: [X]
   Chave que seria usada: [ERRADA]
   Chave correta: [CERTA]
   
   Estou PARANDO a execução até você autorizar.
   
   Posso:
   1. Usar a chave correta [CERTA]
   2. Cancelar a operação
   
   Qual prefere? (1/2/cancela)
   ```

3. **AGUARDAR resposta de Bruno**

---

## SSH Config (como configurar corretamente)

```bash
# ~/.ssh/config

# Chave para BioLeads
Host github-bioleads
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_bioleads
    IdentitiesOnly yes

# Chave para Disparo em Massa
Host github-disparo
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_disparo-em-massa
    IdentitiesOnly yes

# Chave para Ratoflix
Host github-bibliotecasapps
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_ratoflix
    IdentitiesOnly yes

# Chave para LinkDaBio
Host github-linkdabio
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_linkdabio
    IdentitiesOnly yes

# VPS Ugarit (antiga)
Host ugarit
    HostName 187.84.150.120
    User ugarit
    IdentityFile ~/.ssh/id_ed25519_vps-ugarit
    IdentitiesOnly yes

# VPS MAX (nova)
Host vps-max
    HostName 209.50.254.202
    User root
    IdentityFile ~/.ssh/vps-max/id_ed25519
    IdentitiesOnly yes
```

---

## Teste de Validação

Para verificar se a chave está correta antes de operar:

```bash
# Mostrar qual chave seria usada
ssh -v -i ~/.ssh/id_ed25519_[PROJETO] git@github.com 2>&1 | grep "Offering public key"
```

---

## Consequência de Violar a Regra

Se Kothar usar chave SSH errada:
1. **Bruno reporta** → Kothar PARA imediatamente
2. **Registra erro** em `00_Memoria/Aprendizados/erros/`
3. **Reverte** qualquer operação feita com chave errada (se possível)
4. **Regera** chaves SSH se houve comprometimento

**Não é negociável. Contaminação de projeto é CRÍTICA.**

---

## Referências

- Erro que originou: [[2026-06-18-erro-009-contaminacao-projetos-ssh]]
- Análise de brechas: [[2026-06-18-analise-brechas-kothar]]
- Regra complementar: [[principio-menor-escopo]] (zona proibida de "sair do projeto")

---

*Regra criada em 2026-06-18 — Bruno Harkin / Kothar*
*Erro crítico: contaminação de projetos via SSH*
