---
name: analise-de-erros
description: Análise periódica de erros catalogados. Bruno fala "analisa os erros" e Kothar agrega dados, identifica recorrências, SUGERE correções (não implementa sem aprovação).
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: auto-aprendizado
---

# Skill: Análise de Erros

> **Princípio:** Bruno pede análise → Kothar agrega, identifica padrões, **sugere** correções. Não implementa sem aprovação.
>
> Bruno: "agente analia e corrigi para ele nao cometer os mesmo erros como erros frequentes assim agente cria a regra"

---

## 🔴 Gatilho (sob demanda)

**Bruno disser uma das frases:**
- "analisa os erros"
- "analisa os erros do mês"
- "analisa os erros de [período]"
- "mostra erros recorrentes"
- "qual erro mais comum"
- "erros frequentes"
- "relatório de erros"

**Kothar DEVE:**
1. Ler todas as entradas em `00_Memoria/Aprendizados/erros/`
2. **META-ANÁLISE (NOVO):** Executar auditoria interna da própria janela de contexto e estrutura. Verificar gargalos burocráticos ("Estou lendo arquivos demais antes de agir?").
3. Agregar dados (por tipo, severidade, recorrência, e **peso arquitetural**)
4. Identificar top erros recorrentes (incluindo falhas silenciosas de esgotamento de contexto)
5. Identificar skills que mais falharam (ou que adicionaram complexidade desnecessária)
6. **SUGERIR** correções concretas (criar/atualizar/excluir skill/regra)
7. Pedir aprovação antes de implementar
8. Salvar análise em `00_Memoria/Aprendizados/analises/YYYY-MM-analise-X.md`

---

## 📊 O que a análise DEVE conter

### 1. Visão Geral
- Total de erros no período
- Por severidade (crítico/alto/médio/baixo)
- Por tipo (código/processo/comunicação/memória/segurança)
- Por status (registrado/em-análise/regra-criada/resolvido)

### 2. Top Erros Recorrentes
- Ranking dos erros que mais aconteceram
- Para cada: ID, título, ocorrências, severidade, skill relacionada

### 3. Skills que Mais Falharam
- Quais skills estão envolvidas em mais erros
- Sinal de skill mal-definida ou mal-aplicada

### 4. Padrões Identificados e Meta-Análise
- Erros que acontecem em situações similares
- **Fadiga de Contexto:** O Kothar está demorando muito para planejar e pouco para executar? As regras estão conflitando?
- Ex: "A burocracia de 5 portões está consumindo os tokens e causando falhas de 'limite de contexto'."

### 5. Ações Sugeridas (Desburocratização)
- Quais skills criar/atualizar
- Quais regras adicionar à memória automática
- Quais regras-mãe formalizar
- Estimativa de impacto (vai resolver X% dos erros)

### 6. Próximos Passos
- O que Bruno precisa decidir
- O que Kothar implementa se Bruno aprovar

---

## 📁 Onde salvar

```
00_Memoria/Aprendizados/analises/
├── _template.md
├── 2026-06-analise-mensal.md
├── 2026-06-analise-semanal-1.md
└── ...
```

**Nome:** `YYYY-MM-analise-[periodo]-[N].md`

---

## 📋 Template da Análise

```markdown
---
data: YYYY-MM-DD
periodo: "2026-06-01 a 2026-06-30" (ou "semana 1", "últimas 24h", etc)
total-erros: N
gerado-por: "Kothar (sob demanda)"
---

# Análise de Erros — [período]

## 📊 Visão Geral
- Total de erros: N
- Por severidade:
  - Críticos: X
  - Altos: Y
  - Médios: Z
  - Baixos: W
- Por tipo:
  - Código: N
  - Processo: N
  - Comunicação: N
  - Memória: N
  - Segurança: N
  - **Fadiga de Contexto (Arquitetural):** N
- Por status:
  - Registrados: N
  - Em análise: N
  - Regra criada: N
  - Resolvidos: N

## 🧠 Meta-Análise Arquitetural
- **Gargalo Atual:** [Ex: O agente está lendo 5 arquivos inúteis antes de dar 'git add']
- **Risco de Cegueira:** [Ex: Falha em prever bugs devido à falsa sensação de segurança dos gates estritos]

## 🔁 Top Erros Recorrentes

### 1. Erro-XXX — [título] (K ocorrências)
- Severidade: alta
- Skill: gate-seguranca-credenciais
- Última: YYYY-MM-DD
- Regra violada: regra-X

### 2. ...

## 📉 Skills que Mais Falharam

| Skill | Erros envolvidos | % |
|---|---|---|
| [skill-1] | N | X% |
| [skill-2] | N | Y% |

## 🔍 Padrões Identificados

1. **Padrão A:** [descrição do padrão, com 2-3 exemplos]
2. **Padrão B:** ...

## 💡 Ações Sugeridas (aguarda aprovação Bruno)

| Ação | Tipo | Impacto estimado | Esforço |
|---|---|---|---|
| Criar skill X | Nova skill | Resolve N erros/mês | Xh |
| Atualizar skill Y | Skill existente | Resolve N erros/mês | Xh |
| Adicionar regra Z à memória automática | Regra global | Resolve N erros/mês | Xh |
| Reforçar gate W | Regra-mãe | Resolve N erros/mês | Xh |

## ⏭️ Próximos Passos

**Bruno decide:**
- [ ] Aprovar ação A
- [ ] Aprovar ação B
- [ ] Rejeitar ação C (motivo: ...)
- [ ] Adiar pra próximo ciclo

**Kothar implementa** após aprovação.
```

---

## 🔴 Comportamento PROIBIDO

- ❌ Implementar correções sem aprovação de Bruno
- ❌ Sugerir correções vagas ("cuidar mais da qualidade")
- ❌ Gerar análise sem base em dados reais (inventar números)
- ❌ Pular etapa "Bruno decide" e partir pra implementar

---

## 🔗 Skills relacionadas

- `registro-de-erros.md` — fonte dos dados
- `micro-rotinas.md` — R4 (registrar) alimenta este sistema
- `regras-criadas/` — onde as ações aprovadas viram regras
- `feedback-anti-puxa-saco.md` — se análise detectar padrão "puxa-saco", reforça gate

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Fluxo: Bruno pede → Kothar analisa → SUGERE → Bruno aprova → Kothar implementa.*
