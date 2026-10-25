---
name: memorias-isoladas
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: habilidade
descricao: Sistema de memórias isoladas por projeto — fecha brecha M14
---

# 🗄️ SISTEMA DE MEMÓRIAS ISOLADAS v1.4.0

> **Função:** Cada projeto tem sua pasta de memórias. R1 só carrega memórias do projeto atual.

## Estrutura de Pastas

```
~/.claude/projects/
├── -home-bruno-kothar/              # Kothar (sempre carregado)
│   └── memory/
│       ├── MEMORY.md                # índice
│       ├── feedback-anti-puxa-saco.md
│       ├── regras-ouro-kothar.md
│       └── [outras]
│
├── -home-bruno-cofre/               # Cofre raiz
│   └── memory/
│       └── MEMORY.md
│
├── -home-bruno-bioleads/            # Projeto BioLeads
│   └── memory/
│       ├── MEMORY.md
│       ├── regras-negocio.md
│       ├── arquitetura.md
│       └── [projeto-específico]
│
├── -home-bruno-ratoflix/            # Projeto Ratoflix
│   └── memory/
│       ├── MEMORY.md
│       └── [projeto-específico]
│
├── -home-bruno-linkdabio/           # Projeto LinkDaBio
│   └── memory/
│       ├── MEMORY.md
│       └── [projeto-específico]
│
├── -home-bruno-disparo-em-massa/    # Projeto Disparo em Massa
│   └── memory/
│       ├── MEMORY.md
│       └── [projeto-específico]
│
└── -home-bruno-site-novo-modelo/    # site-novo-modelo
    └── memory/
        ├── MEMORY.md
        └── [projeto-específico]
```

## Regra de Carregamento (R1)

```
R1 (Carregar Contexto):
  1. Detectar projeto via pwd → PROJETO_ATUAL
  2. Carregar SEMPRE: ~/.claude/projects/-home-bruno-kothar/memory/ (regras universais)
  3. Carregar SÓ DEPOIS: ~/.claude/projects/-home-bruno-[PROJETO_ATUAL]/memory/
  4. NÃO carregar: memórias de outros projetos
```

**Exceção (com aprovação):** Bruno pode pedir memória de outro projeto explicitamente:
"carrega contexto do ratoflix mesmo estando no bioleads" → R1 pergunta: "Isso mistura projetos. Autoriza?"

## Comandos CLI

```bash
# Adicionar memória ao projeto atual
kothar memory add "recurso novo usa X"

# Ver memórias do projeto atual
kothar memory list

# Buscar memória por keyword (só no projeto atual)
kothar memory search "validar cpf"

# Trocar para memórias de outro projeto (com aprovação)
kothar project switch ratoflix
```

## Como Mover Memórias Antigas

As memórias antigas estão em:
- `~/.claude/projects/-home-bruno-kothar/memory/` (mistas)

**Plano de migração:**

| Memória | Projeto correto | Ação |
|---|---|---|
| `feedback-anti-puxa-saco.md` | kothar | MANTER em kothar |
| `regras-ouro-kothar.md` | kothar | MANTER em kothar |
| Memórias sobre ratoflix | ratoflix | MOVER para ratoflix |
| Memórias sobre bioleads | bioleads | MOVER para bioleads |
| Memórias sobre disparo | disparo-em-massa | MOVER para disparo |

**Status atual:** Estrutura criada. Migração manual conforme necessário.

## DoD

- [x] Estrutura de pastas criada para 7 projetos
- [x] Cada projeto tem pasta memory/
- [x] R1 referencia estrutura nova
- [ ] Migração de memórias antigas (sob demanda)
- [ ] Comando `kothar memory add/list/search` (D11)
