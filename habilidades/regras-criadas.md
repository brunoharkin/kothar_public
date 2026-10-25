---
name: regras-criadas
description: Sistema de promoção de erros → regras. Erros recorrentes viram regras permanentes. Bruno aprova, Kothar implementa. Onde: memória automática / skill / regra-mãe, conforme gravidade.
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: auto-aprendizado
---

# Skill: Regras Criadas (Erros → Regras)

> **Princípio:** erros viram dados → dados viram regras → regras viram comportamento. Loop fechado de auto-aprendizado.
>
> Bruno: "agente analia e corrigi para ele nao cometer os mesmo erros... agente cria a regra e nao se esqueca"

---

## 🔄 Loop de Promoção

```
[1ª vez: erro acontece] → registra
     ↓
[2ª vez: marca "recorrente — atenção"]
     ↓
[3ª vez: Kothar SUGERE criar regra proativamente]
     ↓
[Bruno aprova]
     ↓
[Kothar implementa]
     ↓
[REGRA ATIVA NO PRÓXIMO CONTEXTO]
     ↓
[Loop fecha — erro não acontece mais]
```

---

## 🔴 Gatilho (múltiplos caminhos)

| Gatilho | Quem dispara | Quando |
|---|---|---|
| "cria regra pra evitar" | Bruno | Após análise, quando identifica padrão |
| "implementa correção" | Bruno | Após análise, ação já aprovada |
| "cria regra X" | Bruno | Direto, sem análise |
| "atualiza skill Y" | Bruno | Modificar skill existente |
| "Kothar SUGERE (3ª vez do erro) | Kothar | Proativo, mas espera aprovação |

---

## 📋 Decisão: Onde a Regra Vai

| Tipo de erro / regra | Onde vai | Por quê |
|---|---|---|
| Crítico de segurança (credenciais, vazamento) | **Memória automática** | Nunca pode ser esquecido |
| Erro de processo recorrente | **Skill nova** ou **atualizar skill existente** | Documenta comportamento |
| Regra absoluta (nunca violar) | **Regra-mãe em `evolucao/`** | Categoria de regra inegociável |
| Erro de memória (esqueceu contexto) | **Adicionar ao `Indice-Mestre.md`** ou **prompt-principal** | Visão geral, fácil acesso |
| Erro de código (padrão recorrente) | **Atualizar `definition-of-done.md`** | Critério de aceitação |
| Erro de comunicação | **Atualizar skill de workflow** ou **`auto-relatabilidade`** | Como Kothar se expressa |
| Erro de fluxo (pulou etapa) | **Reforçar regra em micro-rotinas** | R1-R5 ficam mais específicas |

---

## 📁 Onde a Regra Criada Mora

### Opção 1: Memória automática (sempre carrega)
```
~/.claude/projects/-home-bruno-kothar/memory/regra-XXX.md
```

**Quando usar:** regra crítica que NUNCA pode ser esquecida (segurança, regra absoluta).

### Opção 2: Skill nova ou atualizada
```
01_Kothar/habilidades/nome-da-skill.md
```

**Quando usar:** comportamento que se aplica em contextos específicos.

### Opção 3: Regra-mãe
```
01_Kothar/instrucoes/evolucao/nome-da-regra.md
```

**Quando usar:** regra inegociável, sem ser crítica de segurança.

### Opção 4: Regra catalogada (histórico, não carrega)
```
00_Memoria/Aprendizados/regras-criadas/YYYY-MM-DD-regra-NNN.md
```

**Quando usar:** toda regra criada fica catalogada aqui, independente de onde mora. É o "audit log".

---

## 📋 Template da Regra Criada (catalogação)

```markdown
---
id: regra-NNN
data: YYYY-MM-DD
hora: HH:MM
origem: "erro-001" + "erro-007" + "erro-012" (erros que motivaram)
tipo: "seguranca" | "processo" | "comunicacao" | "memoria" | "codigo"
severidade: "baixa" | "media" | "alta" | "critica"
onde-mora: "memoria-automatica" | "skill-nova" | "skill-atualizada" | "regra-mae"
caminho: "01_Kothar/..." ou "~/.claude/..."
status: "sugerida" | "aprovada" | "implementada" | "ativa"
---

# Regra-NNN — [título curto]

## Origem
Esta regra foi criada a partir dos seguintes erros recorrentes:
- erro-001 (YYYY-MM-DD)
- erro-007 (YYYY-MM-DD)
- erro-012 (YYYY-MM-DD)

Padrão identificado: [descrição do padrão]

## A Regra
[Descrição clara e acionável da regra]

## Onde mora
- Arquivo: `[caminho]`
- Tipo: [memoria-automatica | skill | regra-mae]
- Carrega em: [todo contexto | contexto específico | manual]

## Por que esta severidade
[Justificativa — impacto do erro se regra não existir]

## Como validar que está funcionando
- [Critério 1: como saber que regra tá ativa]
- [Critério 2: como saber que tá prevenindo o erro]

## Status
- [x] Sugerida por análise
- [x] Bruno aprovou
- [x] Implementada
- [x] Ativa no contexto
```

---

## 🔴 Comportamento PROIBIDO

- ❌ Kothar criar regra sem aprovação de Bruno
- ❌ Criar regra vaga ("cuidar mais")
- ❌ Criar regra redundante com regra existente
- ❌ Esquecer de catalogar a regra (vai em `regras-criadas/` independente de onde mora)
- ❌ Não atualizar `Indice-Mestre.md` após criar regra

---

## 🔗 Skills relacionadas

- `analise-de-erros.md` — gera sugestões de regras
- `registro-de-erros.md` — fonte dos dados
- `micro-rotinas.md` — R4 e R5 podem virar reforços de regra
- `Indice-Mestre.md` — sempre atualizar após criar regra

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Loop fechado: erro → análise → regra → comportamento. Bruno no controle de cada passo.*
