---
name: marketing-estrategia
description: >-
  Skill do Kothar: 🎯 MARKETING E ESTRATÉGIA v1.4.0. Ativar quando necessário para execução da habilidade marketing-estrategia.
---

# 🎯 MARKETING E ESTRATÉGIA v1.4.0

> **Função:** Avaliar viabilidade de produtos/features com rigor. Sem "achismo", só dados.

## Framework: 6 Pontos Anti-puxa-saco

**Toda ideia ANTES de ser validada:**

### 1. RISCOS

```markdown
## Riscos
1. [Risco] — probabilidade: X% — custo: Y (tempo/dinheiro/reputação)
2. ...
```

**Tipos comuns:**
- Técnico: stack não suporta, dependência não existe
- Mercado: público não quer, concorrente já tem
- Negócio: ROI negativo, escopo inflado
- Reputação: atrasa, quebra, vaza

### 2. MÉTRICAS

```markdown
## Métricas
- P50 (provável): [esforço em horas/dias]
- P90 (pior caso razoável): [esforço]
- Arquivos afetados: [N]
- Dependências externas: [lista]
- Custo de infraestrutura: [$/mês se aplicável]
```

**P50 vs P90:** P50 é o "mais provável", P90 é "se der ruim mas não catastrófico".

### 3. TRADE-OFFS

```markdown
| Opção | Benefício | Custo | Veredicto |
|---|---|---|---|
| Fazer agora | [+1] | [-1] | ✅ se alto |
| Fazer em 30 dias | [+1] | [-1] | 🤔 |
| Não fazer | liberar tempo | perder oportunidade | ❌ se irreversível |
| Alternativa X | [+] | [-] | comparar |
```

### 4. ESCOPO NEGATIVO

```markdown
## O que NÃO vai ser feito
- [item 1]
- [item 2]
- [zona proibida]
```

### 5. CRITÉRIOS DE "PRONTO"

```markdown
- [ ] [critério binário 1 — verificável sim/não]
- [ ] [critério binário 2]
- [ ] [critério binário 3]
```

**Exemplos bons:**
- "Build passa sem erros"
- "Testes cobrem 80%+"
- "Deploy em produção em < 5 min"
- "Bruno consegue usar sem manual"

**Exemplos ruins:**
- "Funciona bem" (subjetivo)
- "Está bonito" (subjetivo)
- "Tá pronto" (sem critério)

### 6. RECOMENDAÇÃO

```markdown
**[vai / não vai / vai com ressalvas]** — [justificativa em 1 linha]
```

**Quem decide:** Bruno. Kothar recomenda, Bruno aprova.

---

## Framework: ICE Score

**Para priorização de backlog:**

| Letra | Significado | Pergunta |
|---|---|---|
| **I** | Impact | Se funcionar, qual o impacto? (1-10) |
| **C** | Confidence | Quão confiante estou? (1-10) |
| **E** | Ease | Quão fácil de implementar? (1-10) |

**ICE Score = (I + C + E) / 3**

| Score | Ação |
|-------|------|
| 8-10 | Fazer agora |
| 6-7 | Backlog priorizado |
| 4-5 | Backlog normal |
| 1-3 | Reconsiderar ou cortar |

## Análise de Lançamento (GTM)

### Template

```markdown
# Lançamento: [Produto/Feature]

## Posicionamento
- **Para quem (ICP):** [descrição específica]
- **Dor:** [problema real]
- **Solução:** [como resolve]
- **Diferencial:** [vs concorrente X]

## Pricing
- **Modelo:** [subscription | one-time | freemium | usage-based]
- **Tiers:**
  - Básico: R$ [X]/mês — [o que inclui]
  - Pro: R$ [Y]/mês — [o que inclui]
  - Enterprise: R$ [Z]/mês — [o que inclui]
- **AARRR esperado:**
  - Acquisition: [meta]
  - Activation: [meta]
  - Retention: [meta]
  - Revenue: [meta]
  - Referral: [meta]

## Canais
- **Aquisição:** [lista com custo estimado]
- **Ativação:** [fluxo de primeiros 7 dias]
- **Retenção:** [mecanismo de loop]

## MVP (30 dias)
- [feature mínima 1] — 1 semana
- [feature mínima 2] — 1 semana
- [feature mínima 3] — 2 semanas

## Métrica de Sucesso
- Primária: [1 métrica]
- Secundária: [2-3 métricas]
- Prazo: [quando medir]
```

## Análise de Concorrente

```markdown
# Concorrente: [Nome]

## Visão Geral
- Site: [URL]
- Tamanho: [N usuários / $X funding / Y funcionários]
- Modelo: [subscription / one-time / freemium]

## Features
- ✅ [feature que eles têm]
- ❌ [feature que eles não têm — oportunidade]

## Pricing
- Tiers: [lista]
- Modelo de cobrança: [por usuário / por uso / fixo]

## Pontos Fortes
- [diferencial 1]
- [diferencial 2]

## Pontos Fracos
- [oportunidade 1]
- [oportunidade 2]

## Estratégia Ugarit
- [como vamos competir]
- [o que copiar]
- [o que fazer diferente]
```

## Anti-padrões (PROIBIDO)

- ❌ "Todas as minhas ideias são ótimas" — sem dados
- ❌ Aprovar ideia sem 6 pontos
- ❌ Pular P50/P90 (subestimar sempre)
- ❌ Não definir métrica de sucesso
- ❌ Comparar com concorrente sem critério
- ❌ "Fácil" / "Rapidinho" / "Só X" — sem medir

## Regra de Ouro

> **"Se você não consegue escrever o critério de Pronto, você não entendeu o problema ainda."**
