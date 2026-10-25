---
name: acao-preditiva
description: Permite ao Kothar rodar em background para antecipar fases de Discovery e Design de tarefas pendentes ou relatadas no histórico diário.
metadata:
  tipo: skill
  data: 2026-06-26
  categoria: operacao
  versao: 2.0.0
---

# Skill: Ação Preditiva (Cron Job Silencioso)

> **Princípio:** O Kothar v2 não espera sentado. Se há tarefas mapeadas no Diário (`00_Memoria/Diarias/...`) que ainda não foram iniciadas, um sub-agente Preditivo acorda em horários ociosos (ex: madrugada ou horário de almoço) para pesquisar e formular um plano de ação (Discovery + Design), entregando-o pronto para revisão quando o usuário voltar.

---

## 🕒 Como o Cron Preditivo Funciona

1. **Gatilho de Background:** Um agendador (`cron-preditivo.sh`) ativa um script python isolado fora da sessão principal do usuário.
2. **Coleta de Tarefas Pendentes:** O script varre as tarefas desmarcadas no diário de hoje/ontem.
3. **Auto-Auditoria de Sistema (NOVO):** Antes de planejar código do projeto, o cron preditivo DEVE verificar o estado das regras do próprio Kothar (ex: se há muitos gates que estão lentificando a execução).
4. **Discovery e Design Silenciosos:** Ele executa as fases de `Discovery` (análise de problema) e `Design` (análise de solução) de forma isolada, gerando um plano.
5. **Alerta Preditivo:** Assim que o Bruno logar (Hook `session-init`), o Kothar lê que há planos preditivos prontos e pergunta: *"Enquanto você estava fora, fiz o Discovery para a Task X e Y. Quer revisar os designs?"*

## 🛡️ Gate de Segurança Preditivo (Menor Escopo)

> [!IMPORTANT]
> O Cron Preditivo obedece RIGOROSAMENTE as seguintes regras:
> - **Proibido Executar (Build/Ship):** O agente preditivo PODE pesquisar e planejar (escrevendo arquivos `.md` isolados de plano), mas **NUNCA DEVE escrever código, gerar commits ou mexer no projeto real**.
> - **Isolamento Total:** Os planos são salvos numa subpasta temporária `.kothar/preditivo/` e só vão para a pasta do projeto se aprovados.
> - **Custo Restrito:** Utiliza o modelo mais econômico (ex: Haiku) para fazer o Discovery e só recomenda o Sonnet para execução final.

## ⚙️ Implementação e Configuração

O cron pode ser gerenciado pelo Bruno:
```bash
# Ativa a percepção noturna
kothar predictive enable --schedule "0 2 * * *"

# Desabilita percepção preditiva
kothar predictive disable
```

---

*Skill criada em 2026-06-26 — Bruno Harkin / Kothar (v2.0)*
