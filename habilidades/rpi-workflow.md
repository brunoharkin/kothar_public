---
name: rpi-workflow
description: Workflow estruturado Research → Plan → Implement para features complexas que precisam de pesquisa e validação gate a gate. Coexiste com o GSD — use RPI para features novas, GSD para correções e ajustes.
version: 1.0.0
projeto: kothar
tipo: habilidade
data: 2026-08-12
---

# Skill: RPI Workflow (Research → Plan → Implement)

> **Fonte:** Inspirado no repositório `shanraisshan/claude-code-best-practice` (64.4k ⭐) e nas práticas do time Anthropic.
> **Quando usar:** Features novas com pesquisa necessária, refatorações grandes, integrações externas, mudanças de arquitetura.
> **Quando NÃO usar:** Correções de bugs, ajustes visuais pequenos, hotfixes → use o GSD para isso.

---

## 🗺️ Visão Geral do Fluxo

```
Bruno descreve a feature
        ↓
  [RPI REQUEST]
  Criar REQUEST.md em features/<slug>/
        ↓
  Bruno aprova ✅ (CP6 do Core Loop)
        ↓
  [RESEARCH]
  Analisar viabilidade, dependências, riscos
  Gerar RESEARCH.md com veredito GO/NO-GO
        ↓
  Bruno aprova veredito ✅
        ↓ (se GO)
  [PLAN]
  Criar PLAN.md com tasks detalhadas, DoD, stack
        ↓
  Bruno aprova plano ✅
        ↓
  [IMPLEMENT]
  Executar task por task com commits curtos
        ↓
  [VERIFY]
  DoD completo + Playwright (se frontend) + scan credenciais
        ↓
  [SHIP]
  Commit + push (com permissão Bruno)
```

---

## 📁 Estrutura de Arquivos por Feature

```
{PROJETO_ROOT}/features/
└── {slug-da-feature}/
    ├── REQUEST.md        ← Descrição do pedido original
    ├── RESEARCH.md       ← Análise de viabilidade
    ├── PLAN.md           ← Plano de implementação detalhado
    └── IMPLEMENTATION.md ← Log de progresso durante o build
```

**Exemplo:**
```
/home/bruno-harkin/disparo-em-massa/features/
└── integracao-stripe/
    ├── REQUEST.md
    ├── RESEARCH.md       (veredito: GO)
    └── PLAN.md
```

---

## 📋 Templates

### REQUEST.md
```markdown
---
feature: {nome-descritivo-da-feature}
data: {YYYY-MM-DD}
status: AGUARDANDO_RESEARCH
projeto: {nome-do-projeto}
---

# Request: {nome-descritivo-da-feature}

## Descrição
{O que o Bruno pediu, em suas palavras}

## Critérios de Sucesso
- [ ] {critério 1}
- [ ] {critério 2}

## Restrições Conhecidas
- {restrição 1}

## Contexto Adicional
{qualquer contexto relevante}
```

### RESEARCH.md
```markdown
---
feature: {slug}
data: {YYYY-MM-DD}
status: GO | NO-GO | GO_COM_RESSALVAS
---

# Research: {slug}

## Veredito: ✅ GO | ❌ NO-GO | ⚠️ GO COM RESSALVAS

## Análise de Viabilidade
{Análise técnica detalhada}

## Dependências Externas
- {lib/serviço 1}: {versão, status}

## Riscos Identificados (3-5)
1. **Risco X** — Probabilidade: Alta/Média/Baixa | Mitigação: {como mitigar}

## Stack Recomendada
- {tecnologia}: {justificativa}

## Estimativa de Esforço (P50/P90)
- P50: {estimativa mediana}
- P90: {estimativa pior caso}

## O que NÃO será feito nesta feature
- {escopo negativo 1}
```

### PLAN.md
```markdown
---
feature: {slug}
data: {YYYY-MM-DD}
status: APROVADO
---

# Plano: {slug}

## Resumo
{O que será implementado}

## DoD (Definition of Done)
- [ ] {critério binário 1}
- [ ] {critério binário 2}
- [ ] Validador.sh passou sem erros
- [ ] analise-codigo.py score >= 90
- [ ] Testado em browser (se frontend)
- [ ] Sem credenciais expostas

## Tasks (em ordem)

### Task 1: {nome-da-task}
- Arquivos a criar/modificar: {lista}
- Critério de conclusão: {o que significa feito}

### Task 2: {nome-da-task}
...

## Commits Planejados
- `feat: {descrição curta 1}`
- `feat: {descrição curta 2}`
```

---

## 🔄 Comandos do Workflow

```bash
# Iniciar RPI para nova feature
kothar rpi iniciar "nome-da-feature"
# → Cria features/{slug}/REQUEST.md

# Executar fase de pesquisa
kothar rpi research features/{slug}/REQUEST.md
# → Cria features/{slug}/RESEARCH.md

# Criar plano (após aprovação do research)
kothar rpi planejar features/{slug}/
# → Cria features/{slug}/PLAN.md

# Verificar status de todas as features
kothar rpi status
```

---

## 🆚 RPI vs GSD — Quando Usar Cada Um

| Situação | Fluxo Recomendado |
|---|---|
| Bug/hotfix | GSD (rápido) |
| Ajuste visual pequeno | GSD |
| Feature nova simples | GSD |
| Feature com API externa | **RPI** |
| Refatoração de arquitetura | **RPI** |
| Integração de nova biblioteca | **RPI** |
| Feature que leva > 1 dia | **RPI** |
| Pesquisa de viabilidade necessária | **RPI** |

---

## 📌 Integração com o Sistema Kothar

- **Gate G6 (Viabilidade):** O `RESEARCH.md` preenche os 6 pontos do anti-puxa-saco automaticamente
- **Checkpoint CP6:** Bruno aprova o `PLAN.md` antes de qualquer código ser escrito
- **Micro-Rotina R4:** Cada decisão tomada durante o RESEARCH é registrada em `00_Memoria/Decisoes/`
- **Micro-Rotina R5:** O DoD do `PLAN.md` é o checklist da R5

---

## ⚠️ Regras

1. **NUNCA iniciar IMPLEMENT sem PLAN.md aprovado**
2. **Se RESEARCH retornar NO-GO** → apresentar alternativas ao Bruno antes de encerrar
3. **Tasks do PLAN.md** → uma por commit (commits pequenos e descritivos)
4. **IMPLEMENTATION.md** → atualizar progresso a cada task concluída

*Skill criada em 2026-08-12 — Inspirada no repositório shanraisshan/claude-code-best-practice*
