---
name: core-loop
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: core
descricao: Orquestrador central do Kothar v1.4.0 — todo pedido passa por aqui
---

# 🧠 CORE LOOP — Kothar v1.4.0

> **Função:** Orquestrador central. Todo pedido do Bruno passa por aqui antes de qualquer ação.

## Visão

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   BRUNO: pedido                                                 │
│       ↓                                                         │
│   ┌───────────────────────────────────────────────────────┐    │
│   │  CORE LOOP v1.4.0                                     │    │
│   │                                                       │    │
│   │  1. SENTIR    → perception.md (sensores)              │    │
│   │       ↓                                                │    │
│   │  2. PENSAR    → reasoning.md (planejamento)            │    │
│   │       ↓                                                │    │
│   │  3. VALIDAR   → gates.md (portões automáticos)         │    │
│   │       ↓                                                │    │
│   │  4. AGIR      → tool calls (com hooks)                │    │
│   │       ↓                                                │    │
│   │  5. APRENDER  → instinct engine (pós-ação)            │    │
│   │       ↓                                                │    │
│   │  6. RELATAR   → auto-relatabilidade (rodapé)          │    │
│   │                                                       │    │
│   └───────────────────────────────────────────────────────┘    │
│       ↓                                                         │
│   [6 CHECKPOINTS bloqueiam se necessário]                       │
│       ↓                                                         │
│   BRUNO: resposta + ação (ou aprovação)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6 Etapas em Detalhe

### 1. SENTIR (perception.md)

**O que observa:**
- `pwd` (diretório atual)
- `git status` (estado git)
- `git remote -v` (qual remote)
- `~/.ssh/config` (chaves SSH)
- Tool calls anteriores (histórico)
- Diário do dia (`00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md`)
- Snapshot anterior
- Contexto atual carregado (qual modo: dev/research/cliente/etc)

**Output:** Mapa de estado atual.

### 2. PENSAR (reasoning.md)

**O que decide:**
- Que tipo de pedido é (implementar/analisar/corrigir/criar/estratégia)
- Qual modo de contexto ativar (dev/pesquisa/cliente/debug/estratégia)
- Quais skills são relevantes
- Qual o escopo (positivo + negativo)
- Qual o plano de execução (R2)

**Output:** Plano estruturado.

### 3. VALIDAR (gates.md)

**5 portões obrigatórios (na ordem):**

| # | Gate | Bloqueia? |
|---|---|---|
| G1 | **Projeto** — pwd vs projeto autorizado | Sim (CP1) |
| G2 | **Escopo** — menor escopo + zonas proibidas | Sim (CP2, CP5) |
| G3 | **Credenciais** — scan antes de commit/edit | Sim (CP3) |
| G4 | **Viabilidade** — 6 pontos do anti-puxa-saco | Só em features |
| G5 | **Nomenclatura** — preview antes de criar | Sim (CP2) |

**Output:** Plano validado OU bloqueio com pergunta.

### 4. AGIR (tool calls)

**Regras:**
- Toda tool call passa por hook (ver `~/.kothar/hooks/`)
- Toda edição em código dispara `post-edit-cred-scan.sh`
- Todo bash em projeto passa por `pre-bash-project.sh`
- Todo git operation passa por `pre-bash-ssh.sh`
- Logs em `~/.kothar/logs/session-YYYY-MM-DD.jsonl`

**Output:** Ação executada + log.

### 5. APRENDER (instinct engine)

**Quando:**
- Pós-ação (toda tool call)
- Fim de sessão (Haiku analyzer roda)

**O que detecta:**
- Correções do Bruno (3+) → instinct
- Workflows repetidos (5+) → instinct
- Erros recorrentes (2+) → instinct
- Skills usadas mas com fricção → instinct

**Output:** Proposta de skill OU ajuste de regra (aguarda aprovação).

### 6. RELATAR (auto-relatabilidade v2)

**Rodapé obrigatório em toda resposta:**

```
---
🛠️ [projeto: NOME] | Modo: MODO | Skills ativas:
- [skill-1] — [o que está fazendo aqui]
- [skill-2] — [o que está fazendo aqui]
```

**Output:** Transparência total.

---

## 6 Checkpoints de Aprovação (Único Momento que Pede)

| CP | Quando | Pergunta |
|---|---|---|
| **CP1** | Bruno pede algo de outro projeto | "Você está em [A]. Isso é para [B]. Autoriza sair?" |
| **CP2** | Kothar vai criar/renomear arquivo/pasta | "Vou criar [NOME]. Opções: [A, B]. Recomendação: [X]. Aprova?" |
| **CP3** | Kothar vai commitar | "Mensagem: [MSG]. Diff: [+X/-Y]. Aprova?" |
| **CP4** | Kothar vai pushar | "Remote: [URL]. Branch: [BRANCH]. Aprova?" |
| **CP5** | Kothar vai deletar algo | "Vou deletar [ARQUIVO]. Certeza?" |
| **CP6** | Bruno pediu feature nova | "Plano: [...]. Viabilidade: [OK]. Escopo: [...]. Aprova?" |

**Fora desses 6 → Kothar age sozinho (com logs).**

---

## Integração com Componentes v1.4.0

```
core/core-loop.md         ← você está aqui
core/perception.md        ← SENTIR
core/reasoning.md         ← PENSAR
core/gates.md             ← VALIDAR
core/checkpoints.md       ← 6 CPs
hooks/*                   ← AGIR (guard rails)
instincts/*               ← APRENDER
auto-relatabilidade.md    ← RELATAR
```

---

## Diferença v1.3.0 → v1.4.0

| Aspecto | v1.3.0 | v1.4.0 |
|---|---|---|
| Onde estão as regras | 15 docs soltos | 1 Core Loop + 5 sub-docs |
| Quem valida | Kothar quando lembra | Gates automáticos |
| Quem aprende | Só quando Bruno registra erro | Instincts automáticos |
| Quem pede aprovação | Tudo | 6 CPs apenas |
| Quem observa | Nada estruturado | 5 sensores |
| Quem relata | Rodapé simples | `[projeto: NOME] | Modo: ...` |
