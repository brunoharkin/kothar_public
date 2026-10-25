---
name: loop-automation
description: >-
  Automação contínua usando /loop e /schedule do Claude Code. Define loops padrão para os projetos do Bruno — monitoramento de PRs, standups automáticos, indexação periódica. Transforma o Kothar de reativo para proativo.
---

# Skill: Loop Automation (Automação Contínua)

> **Fonte:** Boris Cherny (criador do Claude Code): "Experiment with turning workflows into skills + loops. It's powerful."
> 
> Boris usa: `/loop 5m /babysit`, `/loop 30m /slack-feedback`, `/loop 1h /pr-pruner`
>
> **Princípio:** O Kothar não precisa que o Bruno esteja presente para progredir em tarefas de monitoramento, manutenção e relatórios.

---

## 🔄 Conceito: Loop vs Sessão Normal

| Sessão Normal | Com Loop |
|---|---|
| Bruno precisa estar presente | Kothar age autonomamente |
| Uma tarefa por vez | Múltiplas tarefas em paralelo |
| Para quando termina | Continua rodando no intervalo definido |
| Bruno pergunta → Kothar responde | Kothar monitora → alerta se necessário |

---

## 📋 Loops Disponíveis para os Projetos do Bruno

### 🔍 Loop de Monitoramento Diário
```bash
# Verifica status dos projetos, PRs abertos, erros no log
/loop 30m /kothar-monitor
```
**O que faz a cada 30 minutos:**
- Verifica se há PRs abertos nos projetos ativos
- Checa se há erros novos nos logs de aplicação
- Envia resumo via Telegram se há algo importante
- Atualiza `estado-atual.md` do projeto ativo

---

### 📊 Loop de Standup Automático
```bash
# Gera resumo do dia a cada hora durante horário de trabalho
/loop 1h /kothar-standup
```
**O que faz a cada hora (7h-20h):**
- Lê o diário do dia (`00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md`)
- Lê o `estado-atual.md` do projeto ativo
- Gera resumo de 5 linhas: o que foi feito, o que está em progresso, bloqueios
- Salva em `00_Memoria/Sessoes/standup-{data}.md`

---

### 🧹 Loop de Manutenção (PR Pruner)
```bash
# Fecha PRs obsoletos e tasks concluídas
/loop 1d /kothar-manutencao
```
**O que faz uma vez por dia:**
- Lista PRs com mais de 7 dias sem atividade
- Lista tasks marcadas como concluídas mas não arquivadas
- Propõe ações de limpeza (sem executar sem aprovação)

---

### 💾 Loop de Checkpoint Preventivo
```bash
# Salva checkpoint se sessão estiver longa
/loop 15m /kothar-checkpoint-check
```
**O que faz a cada 15 minutos:**
- Verifica contagem de tokens da sessão
- Se > 60k tokens: avisa Bruno para salvar checkpoint em breve
- Se > 80k tokens: salva checkpoint automaticamente e avisa

---

## 🛠️ Como Ativar Loops no Claude Code

### Método 1: Interativo (durante sessão)
```bash
# Na sessão do Claude Code:
/loop 5m "Verificar se há novos erros no log do projeto disparo-em-massa"
/loop 30m "Gerar resumo do progresso e enviar via Telegram"
```

### Método 2: Agendado (via /schedule)
```bash
# Agendar para horário específico:
/schedule "09:00" "Gerar standup do dia e salvar em Cofre"
/schedule "18:00" "Fazer checkpoint da sessão e gerar nota de sessão"
```

### Método 3: Background (--bg)
```bash
# Rodar em background sem bloquear o terminal:
claude --bg "/loop 1h /kothar-standup"
```

---

## 📝 Criando um Loop Personalizado

Para criar um novo loop, defina um **comando** em `.claude/commands/`:

```markdown
# .claude/commands/kothar-monitor.md
Monitore o projeto atual e:
1. Verifique erros novos em `~/.kothar/logs/audit.log` da última hora
2. Se há erros: notifique via Telegram com resumo
3. Atualize `estado-atual.md` com timestamp da última verificação
4. Se tudo OK: registre "Monitoramento OK às {HORA}" no diário do dia
```

---

## ⚠️ Regras de Segurança para Loops

1. **NUNCA loop com ações destrutivas** — loops só podem ler, monitorar e notificar
2. **Ações que modificam código** → requerem aprovação do Bruno (PermissionRequest Hook)
3. **Loops com Git** → apenas `git status`, `git log` — nunca `git push` automático
4. **Limite de tokens** → se sessão de loop atingir 50k tokens, reiniciar automaticamente

---

## 🔗 Integração com o Kothar

- **Stop Hook:** O `kothar-stop-hook.sh` notifica via Telegram quando o loop pausa
- **PermissionRequest Hook:** Qualquer loop que precise de permissão envia para Telegram
- **Micro-Rotina R3:** O loop de monitoramento é a versão automatizada da R3 (re-leitura a cada 30min)
- **SessionEnd Hook:** Loops são encerrados automaticamente com a sessão

---

## 💡 Boas Práticas (Boris Cherny)

1. **Comece simples** — um loop de monitoramento antes de loops de ação
2. **Loops de notificação** antes de loops de automação
3. **Testar manualmente** o comando antes de transformar em loop
4. **Log tudo** — loops devem registrar cada execução em `~/.kothar/logs/`
5. **Timeout por loop** — defina tempo máximo de execução para evitar loops infinitos

*Skill criada em 2026-08-12 — Inspirada nas práticas de Boris Cherny (criador do Claude Code)*
