---
name: business-process-automation
description: Automação de processos de negócio repetitivos — standup diário automático, relatório semanal de progresso, resumo de sessão em formato executivo. Elimina tarefas manuais de comunicação e documentação.
version: 1.0.0
projeto: kothar
tipo: habilidade
data: 2026-08-12
---

# Skill: Business Process Automation (Automação de Processos)

> **Fonte:** Thariq (Anthropic): "Business Process & Team Automation Skills automate repetitive workflows into one command. Saving previous results in log files can help the model stay consistent and reflect on previous executions."
> 
> **Propósito:** Eliminar toda tarefa manual e repetitiva de documentação, comunicação e acompanhamento de progresso.

---

## 📋 Processos Automatizados

---

### 1. 🌅 Standup Diário Automático

**Ativar com:** `kothar standup` ou via loop `/loop 1h /kothar-standup`

**O que faz:**
1. Lê o diário do dia em `00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md`
2. Lê o `estado-atual.md` do projeto ativo
3. Verifica as últimas sessões em `00_Memoria/Sessoes/`
4. Gera resumo estruturado de 5 linhas

**Formato de output:**
```
🌅 STANDUP — {DIA_DA_SEMANA}, {DATA}
Projeto: {PROJETO_ATIVO}

✅ CONCLUÍDO: {o que foi feito desde o último standup}
🔄 EM PROGRESSO: {o que está sendo feito agora}
🚧 BLOQUEIOS: {problemas encontrados / dependências}
📅 PRÓXIMAS TASKS: {o que será feito a seguir}
⏱️ Estimativa: {tempo para próxima entrega}
```

**Salva em:** `00_Memoria/Sessoes/standup-{YYYY-MM-DD}-{HHMM}.md`

---

### 2. 📊 Relatório Semanal de Progresso

**Ativar com:** `kothar relatorio-semanal`

**O que faz:**
1. Lê todos os diários da semana em `00_Memoria/Diarias/YYYY-MM/`
2. Lê todas as notas de sessão da semana em `00_Memoria/Sessoes/`
3. Lê decisões tomadas na semana em `00_Memoria/Decisoes/`
4. Calcula métricas: sessões, tokens, features completadas
5. Gera relatório em formato executivo

**Formato de output:**
```markdown
# Relatório Semanal — {DATA_INICIO} a {DATA_FIM}

## 📈 Métricas da Semana
- Sessões de trabalho: {N}
- Tokens consumidos: {N}
- Features concluídas: {N}
- Decisões registradas: {N}

## ✅ Features/Tasks Concluídas
- {feature 1} — {projeto}
- {feature 2} — {projeto}

## 🔄 Em Andamento
- {task 1} — {progresso}%

## 📋 Decisões Importantes
- {decisão 1} — {data}

## 🎯 Prioridades da Próxima Semana
1. {prioridade 1}
2. {prioridade 2}
```

**Salva em:** `00_Memoria/Relatorios/relatorio-{YYYY-WW}.md`

---

### 3. 📝 Nota de Sessão Executiva

**Ativar com:** Automático ao final de cada sessão (via `SessionEnd` hook + `gerar-nota-sessao.sh`)

**Já existe parcialmente** — o `gerar-nota-sessao.sh` cria a nota técnica.
Esta skill adiciona o **formato executivo** no início da nota:

```markdown
## TL;DR da Sessão (Resumo Executivo)
- **Objetivo:** {o que foi pedido}
- **Entregue:** {o que foi feito}
- **Próximo passo:** {próxima ação necessária}
- **Tempo estimado na próxima sessão:** {X horas}
```

---

### 4. 🔔 Alerta de Prazo (Deadline Tracker)

**Ativar com:** `kothar verificar-prazos`

**O que faz:**
1. Busca arquivos com `data:`, `prazo:` ou `deadline:` nos projetos ativos
2. Filtra os próximos 7 dias
3. Gera alerta se há prazo próximo

**Formato de output:**
```
⚠️ PRAZOS NOS PRÓXIMOS 7 DIAS:
- {feature X}: {projeto} — vence em {N} dias ({DATA})
- {feature Y}: {projeto} — vence em {N} dias ({DATA})
```

---

### 5. 📦 Resumo de Projeto para Cliente

**Ativar com:** `kothar resumo-cliente {projeto}`

**O que faz:**
1. Lê o `estado-atual.md` do projeto
2. Lê as últimas decisões em `Decisoes/`
3. Gera resumo em linguagem NÃO técnica, focado em valor entregue

**Formato:**
```
📦 ATUALIZAÇÃO DO PROJETO — {NOME_CLIENTE}

O que entregamos esta semana:
→ {descrição não-técnica da feature 1}
→ {descrição não-técnica da feature 2}

O que vem a seguir:
→ {descrição não-técnica da próxima entrega}

Status geral: ✅ No prazo | ⚠️ Atenção | ❌ Atrasado
```

---

## 🔧 Como Registrar Processos Personalizados

Para adicionar um novo processo automático:

1. Criar um arquivo de processo em `Cofre/01_Kothar/habilidades/processos/`
2. Definir: **gatilho** (quando ativa), **input** (o que lê), **output** (o que gera)
3. Adicionar ao catálogo de habilidades

**Template de processo:**
```markdown
## Processo: {nome}
- **Gatilho:** {quando ativa}
- **Input:** {arquivos/dados que lê}
- **Output:** {arquivo/mensagem gerada}
- **Frequência:** {uma vez / por sessão / por dia / por semana}
```

---

## 🔗 Integração com o Kothar

- **SessionEnd Hook:** `gerar-nota-sessao.sh` é a base para nota executiva
- **Loop Automation:** Standup diário pode rodar como loop automático
- **Stop Hook:** Relatório de progresso pode ser gerado ao pausar sessão longa
- **Telegram:** Alertas de prazo e standups podem ser enviados via `telegram-notify.sh`
- **Micro-Rotina R4:** Cada decisão registrada alimenta os relatórios automáticos

---

## ⚠️ Regras

1. **Relatórios não tomam decisões** — apenas informam, nunca executam ações
2. **Tom executivo** — sem jargão técnico em resumos para cliente
3. **Dados reais** — lê sempre do Cofre, nunca inventa progresso
4. **Honestidade** — se não há progresso a reportar, diz isso claramente

*Skill criada em 2026-08-12 — Inspirada na categoria Business Process Automation do time Anthropic*
