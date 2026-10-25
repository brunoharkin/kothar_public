---
name: stall-prevention
description: >-
  Skill do Kothar: 🛡️ PREVENÇÃO DE TRAVAMENTO EM TAREFAS GRANDES v2.1.2. Ativar quando necessário para execução da habilidade stall-prevention.
---

# 🛡️ PREVENÇÃO DE TRAVAMENTO EM TAREFAS GRANDES v2.1.2

> **Problema:** O Claude para de finalizar tarefas grandes, fica em loop infinito de raciocínio

## Solução Proposta

### 1. Sistema de Checkpoints Progressivos

```yaml
config:
  max_raciocinio_steps: 10      # Passos máximos de raciocínio
  max_execution_time: 1800      # 30 minutos por tarefa
  checkpoint_interval: 300     # 5 minutos entre checkpoints
  force_action_threshold: 3     # Força ação após 3 checkpoints sem ação
```

### 2. Micro-Rotina de Execução

```bash
# R6: Executar com Controle de Loop
1. Iniciar timer de execução
2. A cada 5 minutos:
   a. Verificar se houve ação concreta (arquivo criado/editado)
   b. Se não → perguntar "Continuar com [ação específica]?"
   c. Se sim → resetar timer
3. Após 30 min → forçar conclusão com resumo
```

### 3. Regras Anti-Loop

```markdown
🚫 PROIBIDO:
- Mais de 10 passos de raciocínio sem ação concreta
- Mais de 30 minutos sem progresso visível
- Loop de perguntas sem decisão

✅ OBRIGATÓRIO:
- A cada 5 passos: ação concreta (criar arquivo, editar, etc)
- Após 10 passos: apresentar resumo parcial
- Após 30 min: concluir com o que foi feito
```

### 4. Script de Monitoramento

#!/bin/bash
# task-monitor.sh - Monitora execução de tarefas grandes

TASK_ID="$1"
MAX_STEPS=10
MAX_TIME=1800
STEP_COUNT=0
LAST_ACTION=0

while [ $STEP_COUNT -lt $MAX_STEPS ]; do
    # Verificar última ação
    current_time=$(date +%s)
    if [ $((current_time - LAST_ACTION)) -gt 300 ]; then
        echo "⚠️ Sem ação por 5 minutos. Continuar?"
        read -r response
        if [[ $response =~ ^(n|nao|stop) ]]; then
            break
        fi
    fi
    
    # Executar próximo passo
    STEP_COUNT=$((STEP_COUNT + 1))
    echo "Passo $STEP_COUNT/$MAX_STEPS"
    
    # Verificar tempo
    if [ $((current_time - TASK_START)) -gt $MAX_TIME ]; then
        echo "⏰ Tempo esgotado. Concluindo..."
        break
    fi
done
```

### 5. Prompt Modificado para Tarefas Grandes

```markdown
AO RECEBER UMA TAREFA GRANDE:

1. DIVIDIR IMEDIATAMENTE em sub-tarefas
2. CRIAR CHECKLIST de ações concretas
3. EXECUTAR UMA POR UMA com confirmação
4. APÓS CADA AÇÃO: registrar progresso
5. SE TRAVAR: perguntar "Continuar com [ação específica]?"

EXEMPLO:
✅ Tarefa: "Criar sistema de login"
   1. Criar tabela users (confirmar?)
   2. Criar endpoint /login (confirmar?)
   3. Criar frontend (confirmar?)
   4. Testar fluxo completo (confirmar?)
```

### 6. Integração com Kothar

No core/reasoning.md, adicionar:

```markdown
### ETAPA 7: Controle de Execução (v2.1.2)

Para tarefas classificadas como "grande":
- Dividir em sub-tarefas
- Aplicar R6 (execução com controle)
- Monitorar a cada 5 minutos
- Forçar conclusão após 30 min
```

### 7. Configuração do Hook

Adicionar em ~/.kothar/hooks/task-monitor.sh:

```bash
#!/bin/bash
# Executado a cada tool call para monitorar tarefas

if [ -f ~/.kothar/state/task-active ]; then
    TASK_INFO=$(cat ~/.kothar/state/task-active)
    STEPS=$(echo "$TASK_INFO" | jq -r '.steps // 0')
    LAST_ACTION=$(echo "$TASK_INFO" | jq -r '.last_action // 0')
    
    # Se passou 5 minutos desde última ação
    if [ $(($(date +%s) - LAST_ACTION)) -gt 300 ]; then
        echo "🔄 5 minutos sem ação. Continuar com a tarefa?"
        # Esperar resposta do usuário
    fi
fi
```

## Implementação Imediata

1. Criar script de monitoramento
2. Modificar reasoning.md para incluir R6
3. Adicionar hook ao settings.json
4. Criar arquivo de controle de tarefas
5. Documentar o fluxo para Bruno
