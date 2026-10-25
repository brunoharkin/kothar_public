---
name: sistema-memorias-isoladas
description: "Sistema de memórias isoladas por projeto — cada projeto tem sua memória, não mistura contexto"
metadata:
  tipo: regra-comportamental
  data: 2026-06-18
  autor: Bruno Harkin
  origem: erro-009-contaminacao-projetos-ssh
  severidade: ALTA
---

# SISTEMA DE MEMÓRIAS ISOLADAS POR PROJETO

> **⚠️ Implementado 2026-06-18**
> Problema: Kothar carregava memórias de TODOS os projetos, causando contaminação de contexto.
> Solução: cada projeto tem sua memória isolada, Kothar só carrega a do projeto ATUAL.

---

## Estrutura de Memórias

```
~/.claude/
├── projects/
│   │
│   ├── -home-bruno-kothar/           # 🏠 MEMÓRIAS GERAIS (sempre carrega)
│   │   └── memory/
│   │       ├── MEMORY.md            # Índice de todas as memórias
│   │       ├── feedback-anti-puxa-saco.md    # Regras do Kothar
│   │       ├── regras-ouro-kothar.md          # Regras originais
│   │       ├── sistema-completo-kothar.md     # Sistema completo
│   │       ├── regra-isolamento-projetos.md   # ISOLAMENTO
│   │       ├── regra-ssh-isolation.md          # SSH
│   │       ├── regra-nomenclatura-preview.md   # Nomenclatura
│   │       ├── regra-viabilidade-gate.md       # Viabilidade
│   │       ├── erro-009-contaminacao-projetos.md  # Erro 009
│   │       ├── analise-brechas-kothar.md       # Análise
│   │       └── ...
│   │
│   ├── -home-bruno-bioleads/         # 📦 PROJETO BIOLEADS
│   │   └── memory/
│   │       ├── MEMORY.md            # Índice do projeto
│   │       ├── projeto-bioleads.md  # Contexto do projeto
│   │       ├── estado-atual.md      # Estado atual
│   │       ├── decisoes/           # Decisões do projeto
│   │       └── ...
│   │
│   ├── -home-bruno-disparo/         # 📦 PROJETO DISPARO EM MASSA
│   │   └── memory/
│   │       ├── MEMORY.md
│   │       ├── projeto-disparo.md
│   │       ├── estado-atual.md
│   │       └── ...
│   │
│   ├── -home-bruno-ratoflix/        # 📦 PROJETO RATOFLIX
│   │   └── memory/
│   │       ├── MEMORY.md
│   │       ├── projeto-ratoflix.md
│   │       ├── estado-atual.md
│   │       ├── regras-cliente.md    # Regras específicas do cliente
│   │       └── ...
│   │
│   ├── -home-bruno-linkdabio/       # 📦 PROJETO LINKDABIO
│   │   └── memory/
│   │       ├── MEMORY.md
│   │       ├── projeto-linkdabio.md
│   │       └── ...
│   │
│   └── -home-bruno-Cofre/          # 📦 COFRE (memórias do sistema)
│       └── memory/
│           ├── MEMORY.md
│           └── ...
```

---

## Regras de Isolamento de Memória

### Regra 1: CARREGAR SOMENTE DO PROJETO ATUAL
```
Ao iniciar sessão ou mudar de projeto:
1. Identificar PROJETO_ATUAL via pwd
2. Carregar SOMENTE ~/.claude/projects/-home-bruno-{PROJETO}/memory/
3. NUNCA carregar memórias de outros projetos automaticamente
4. Se precisar info de outro projeto: pedir autorização explícita
```

### Regra 2: MEMÓRIAS GERAIS SEMPRE DISPONÍVEIS
```
As memórias em -home-bruno-kothar/ são GLOBAIS e SEMPRE carregam:
- Regras do Kothar (anti-puxa-saco, isolamento, ssh, etc)
- Sistema completo
- Erros e análises
- Configurações gerais

Estas NÃO contaminam — são regras de COMPORTAMENTO, não de PROJETO.
```

### Regra 3: SE PRECISAR DE OUTRO PROJETO
```
Situação: Bruno pede info de projeto diferente do ATUAL

1. Reportar: "Isso é do projeto [X], mas estou no [Y]. Posso acessar?"
2. Se Bruno autorizar: carregar SOMENTE a memória necessária
3. Após usar: VOLTAR ao projeto original [Y]
4. NUNCA misturar contextos entre projetos
```

### Regra 4: FRONTMATTER OBRIGATÓRIO
```
Toda memória de projeto DEVE ter frontmatter:

---
name: nome-da-memoria
description: "1 linha sobre o que é"
metadata:
  type: project | reference | decision
  projeto: nome-do-projeto
  data: YYYY-MM-DD
---

O campo `projeto:` permite filtrar memórias por projeto.
```

---

## Como Identificar o Projeto Atual

```bash
# Pega o diretório atual
pwd
# /home/bruno/bioleads/backend

# Extrai o nome do projeto
PROJETO=$(basename "$(pwd)")
# bioleads

# Mapeia para o projeto correto
case $PROJETO in
  bioleads) PROJETO_ID="bioleads" ;;
  disparo|disparo-em-massa) PROJETO_ID="disparo" ;;
  ratoflix) PROJETO_ID="ratoflix" ;;
  linkdabio) PROJETO_ID="linkdabio" ;;
  Cofre) PROJETO_ID="Cofre" ;;
  kothar) PROJETO_ID="kothar" ;;
  *) PROJETO_ID="desconhecido" ;;
esac
```

---

## Tabela de Projetos e Memórias

| Projeto | Diretório | Memória ID |
|---------|-----------|------------|
| BioLeads | `/home/bruno/bioleads/` | `-home-bruno-bioleads` |
| Disparo em Massa | `/home/bruno/disparo-em-massa/` | `-home-bruno-disparo` |
| Ratoflix | `/home/bruno/Ratoflix-cliente/` | `-home-bruno-ratoflix` |
| LinkDaBio | `/home/bruno/linkdabio/` | `-home-bruno-linkdabio` |
| Cofre | `/home/bruno/Cofre/` | `-home-bruno-Cofre` |
| Kothar | `/home/bruno/kothar/` | `-home-bruno-kothar` |

---

## Fluxo de Isolamento

```
[Kothar inicia sessão]
     ↓
pwd → identifica PROJETO_ATUAL
     ↓
Carrega memórias GERAIS (kothar/)
     ↓
Carrega memórias do PROJETO_ATUAL
     ↓
Se Bruno pedir info de outro projeto:
  → Pergunta autorização
  → Carrega SOMENTE o necessário
  → Volta ao projeto original
     ↓
[Continua trabalhando]
```

---

## Exemplo de Memória de Projeto

```markdown
---
name: projeto-bioleads
description: "Contexto central do BioLeads — stack, deploy, estado atual"
metadata:
  type: project
  projeto: bioleads
  data: 2026-06-18
---

# BioLeads — Contexto do Projeto

## Stack
- Backend: Python/FastAPI + Celery + Redis
- Frontend: Next.js
- Database: PostgreSQL

## Deploy
- VPS: vps-max (Integrator)
- URL: https://bioleads.ugaritdigital.com

## Estado Atual
- Status: 🟢 Produção
- Última atualização: 2026-06-18

## Repositório
- Git: git@github.com:appsugarit-dev/BioLeads.git
- Chave SSH: id_ed25519_bioleads
```

---

## Checklist de Isolamento

```
□ Ao iniciar sessão: identificar projeto via pwd
□ Carregar memórias GERAIS (kothar/) primeiro
□ Carregar memórias do PROJETO_ATUAL
□ NUNCA carregar memórias de outros projetos automaticamente
□ Se precisar de outro projeto: pedir autorização
□ Todas as memórias de projeto têm frontmatter com `projeto:`
```

---

## Referências

- Erro que originou: [[2026-06-18-erro-009-contaminacao-projetos-ssh]]
- Análise de brechas: [[2026-06-18-analise-brechas-kothar]]
- Regra isolamento: [[regra-isolamento-projetos]]

---

*Sistema implementado em 2026-06-18 — Bruno Harkin / Kothar*
