---
nome: plano-correcao-kothar-paradas
descricao: Plano completo para corrigir o problema do Kothar parando no meio da execução de tarefas grandes
metadata:
  type: project
  criado_em: "2026-06-28"
  prioridade: critica
---

# Plano de Correção - Kothar v2.1.2

## 🚨 Problema Identificado

O Kothar está parando no meio da execução de tarefas grandes, especialmente:
- Planos complexos são iniciados mas não concluídos
- O agente para de responder mesmo com comandos "continue"
- Execuções travam sem aviso prévio
- Contexto muito grande pode estar causando travamentos

## 🎯 Causas Raiz Análise

### 1. **Stall Detector Agressivo**
- Threshold de 5 minutos (300s) pode ser muito baixo para tarefas complexas
- O detector está marcando sessões como "stalled" prematuramente
- Hooks estão interferindo no fluxo normal de execução

### 2. **Fault Tolerance Loop Infinito**
- Retry automático pode estar criando loops
- Máximo de 3 retries não é suficiente para operações pesadas
- Exponential backoff está pausando execuções por muito tempo

### 3. **Session Snapshot Inoportuno**
- Snapshot em SessionEnd está sendo acionado em meio a execuções
- Pode estar truncando o estado da sessão
- Hooks estão rodando em paralelo com tarefas principais

### 4. **Context Window Overflow**
- Tarefas grandes excedem o limite de tokens (1M)
- Não há estratégia de chunking para tarefas complexas
- Memória não está sendo gerenciada adequadamente

### 5. **Hooks Interferindo**
- 13 hooks rodando em cada tool call estão sobrecarregando
- Hooks estão bloqueando ou pausando execuções
- Logs excessivos estão consumindo recursos

## 🛠️ Plano de Ação

### Fase 1: Diagnóstico Completo (30 minutos)

1. **Verificar logs do Kothar**
```bash
# Verificar logs de stall detector
ls -la ~/.kothar/logs/stall-*.jsonl

# Verificar logs de fault tolerance
ls -la ~/.kothar/logs/fault-tolerance-*.jsonl

# Verificar session logs
ls -la ~/.kothar/logs/session-*.log
```

2. **Testar comportamento atual**
```bash
# Executar uma tarefa simples e monitorar
timeout 300 bash -c "echo 'testando stall detector'"
```

3. **Coletar métricas de desempenho**
```bash
# Monitorar uso de memória e CPU
htop

# Verificar processos do kothar
ps aux | grep kothar
```

### Fase 2: Ajustes de Configuração Imediatos (15 minutos)

1. **Ajustar Stall Detector**
   - Aumentar STALLED_MIN de 300s para 600s (10 minutos)
   - Aumentar STUCK_MIN de 600s para 1200s (20 minutos)
   - Desativar notificações agressivas

2. **Ajustar Fault Tolerance**
   - Reduzir MAX_RETRIES de 3 para 2
   - Reduzir BASE_DELAY de 1000ms para 500ms
   - Adicionar timeout global de 30 minutos

3. **Otimizar Hooks**
   - Remover hooks não essenciais
   - Adicionar flag `--silent` para logs verbosos
   - Implementar batching de logs

### Fase 3: Implementação de Chunking (45 minutos)

1. **Criar script de chunking**
```bash
# Criar arquivo: ~/.kothar/scripts/chunk-tasks.sh
cat > ~/.kothar/scripts/chunk-tasks.sh << 'EOF'
#!/bin/bash
# Divide tarefas grandes em chunks menores
TASK_FILE="$1"
CHUNK_SIZE=5  # 5 tarefas por chunk

if [ ! -f "$TASK_FILE" ]; then
    echo "Arquivo de tarefas não encontrado: $TASK_FILE"
    exit 1
fi

# Dividir em chunks
split -l $CHUNK_SIZE "$TASK_FILE" "$TASK_FILE.chunk."

echo "Tarefas divididas em chunks:"
ls -la "$TASK_FILE.chunk."*
EOF
chmod +x ~/.kothar/scripts/chunk-tasks.sh
```

2. **Implementar gerenciador de contexto**
```bash
# Criar arquivo: ~/.kothar/scripts/context-manager.py
cat > ~/.kothar/scripts/context-manager.py << 'EOF'
#!/usr/bin/env python3
import json
import os
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.kothar")
STATE_DIR = f"{HERMES_HOME}/state"
CONTEXT_FILE = f"{STATE_DIR}/context.json"

def save_context_chunk(chunk_id, data):
    """Salva um chunk de contexto"""
    chunk_file = f"{CONTEXT_FILE}.{chunk_id}"
    with open(chunk_file, 'w') as f:
        json.dump(data, f)
    return chunk_file

def load_context_chunk(chunk_id):
    """Carrega um chunk de contexto"""
    chunk_file = f"{CONTEXT_FILE}.{chunk_id}"
    if os.path.exists(chunk_file):
        with open(chunk_file, 'r') as f:
            return json.load(f)
    return None

def cleanup_context():
    """Limpa chunks antigos"""
    cutoff = datetime.now().timestamp() - 86400  # 24 horas atrás
    for file in os.listdir(STATE_DIR):
        if file.startswith("context.json."):
            file_path = os.path.join(STATE_DIR, file)
            if os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
EOF
```

### Fase 4: Refatoração de Hooks (60 minutos)

1. **Criar hook manager centralizado**
```bash
# Criar arquivo: ~/.kothar/scripts/hook-manager.sh
cat > ~/.kothar/scripts/hook-manager.sh << 'EOF'
#!/usr/bin/env bash
# Hook Manager - Controla quais hooks são executados

HOOKS_DIR="$HOME/.kothar/hooks"
ACTIVE_HOOKS_FILE="$HOME/.kothar/state/active-hooks.json"

# Carregar hooks ativos
load_active_hooks() {
    if [ -f "$ACTIVE_HOOKS_FILE" ]; then
        jq -r '.hooks[]' "$ACTIVE_HOOKS_FILE" 2>/dev/null || echo "stall-detector,fault-tolerance"
    else
        echo "stall-detector,fault-tolerance"
    fi
}

# Executar hook se ativo
run_hook() {
    local hook_name="$1"
    local tool_name="$2"
    local shift
    shift 2
    
    if [[ "$(load_active_hooks)" =~ "$hook_name" ]]; then
        echo "Executando hook: $hook_name para $tool_name"
        "$HOOKS_DIR/$hook_name.sh" "$@"
    fi
}

# Ativar/desativar hooks
toggle_hook() {
    local hook_name="$1"
    local action="$2"  # enable/disable
    
    mkdir -p "$(dirname "$ACTIVE_HOOKS_FILE")"
    if [ "$action" = "disable" ]; then
        jq --arg hook "$hook_name" 'del(.hooks[] | select(. == $hook))' "$ACTIVE_HOOKS_FILE" > tmp.json && mv tmp.json "$ACTIVE_HOOKS_FILE"
    else
        jq --arg hook "$hook_name" '.hooks += [$hook]' "$ACTIVE_HOOKS_FILE" > tmp.json && mv tmp.json "$ACTIVE_HOOKS_FILE"
    fi
}

# Inicializar arquivo se não existir
if [ ! -f "$ACTIVE_HOOKS_FILE" ]; then
    echo '{"hooks": ["stall-detector", "fault-tolerance"]}' > "$ACTIVE_HOOKS_FILE"
fi
EOF
chmod +x ~/.kothar/scripts/hook-manager.sh
```

2. **Atualizar configuração do Kothar**
```bash
# Criar novo arquivo de configuração
cat > ~/.kothar/config/kothar-v2.1.3.json << 'EOF'
{
  "stall_detector": {
    "stalled_min": 600,
    "stuck_min": 1200,
    "long_running_min": 300,
    "notifications": false
  },
  "fault_tolerance": {
    "max_retries": 2,
    "base_delay": 500,
    "max_delay": 5000,
    "timeout": 1800
  },
  "hooks": {
    "enabled": ["stall-detector", "fault-tolerance", "session-snapshot"],
    "batch_logging": true,
    "log_level": "warn"
  },
  "chunking": {
    "enabled": true,
    "chunk_size": 5,
    "max_tasks_per_session": 50
  },
  "context": {
    "max_tokens": 800000,
    "cleanup_interval": 3600
  }
}
EOF
```

### Fase 5: Testes e Validação (45 minutos)

1. **Criar script de teste**
```bash
# Criar arquivo: ~/.kothar/scripts/test-execution.sh
cat > ~/.kothar/scripts/test-execution.sh << 'EOF'
#!/bin/bash
# Testa execução de tarefas grandes

echo "🧪 Iniciando teste de execução..."

# Criar arquivo de teste com 100 tarefas
cat > /tmp/test-tasks.txt << 'TASKS'
Task 1: Executar comando básico
Task 2: Ler arquivo de configuração
Task 3: Processar dados
Task 4: Validar entrada
Task 5: Gerar saída
Task 6: Atualizar banco
Task 7: Enviar notificação
Task 8: Registrar log
Task 9: Limpar cache
Task 10: Comprimir arquivo
# ... (repetir até 100)
Task 100: Finalizar processamento
TASKS

# Medir tempo de execução
start_time=$(date +%s)

# Executar com chunking
echo "Executando com chunking..."
./chunk-tasks.sh /tmp/test-tasks.txt

# Executar sem chunking (para comparação)
echo "Executando sem chunking..."
cat /tmp/test-tasks.txt | while read task; do
    echo "Executando: $task"
    sleep 0.1
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "⏱️ Tempo total: ${duration}s"
echo "✅ Teste concluído"
EOF
chmod +x ~/.kothar/scripts/test-execution.sh
```

2. **Executar teste de carga**
```bash
# Rodar teste
./test-execution.sh

# Monitorar logs
tail -f ~/.kothar/logs/stall-*.jsonl
tail -f ~/.kothar/logs/fault-tolerance-*.jsonl
```

### Fase 6: Implementação Final (30 minutos)

1. **Atualizar versão do Kothar**
```bash
# Atualizar arquivo SKILL.md
sed -i 's/v2.1.2/v2.1.3/g' ~/.claude/skills/kothar/SKILL.md
sed -i 's/ESTADO ATUAL v2.1.2/ESTADO ATUAL v2.1.3/g' ~/.claude/skills/kothar/SKILL.md
```

2. **Criar script de atualização**
```bash
# Criar arquivo: ~/.kothar/scripts/update-to-v2.1.3.sh
cat > ~/.kothar/scripts/update-to-v2.1.3.sh << 'EOF'
#!/bin/env bash
# Atualiza Kothar para v2.1.3

echo "🚀 Atualizando Kothar para v2.1.3..."

# Parar serviços
echo "Parando serviços..."
pkill -f "kothar" || true

# Backup da configuração
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Aplicar correções
echo "Aplicando correções..."

# Atualizar hooks
cp ~/.kothar/hooks/post-tool-stall-detector.sh ~/.kothar/hooks/post-tool-stall-detector.sh.backup
sed -i 's/STALLED_MIN=300/STALLED_MIN=600/' ~/.kothar/hooks/post-tool-stall-detector.sh
sed -i 's/STUCK_MIN=600/STUCK_MIN=1200/' ~/.kothar/hooks/post-tool-stall-detector.sh

# Atualizar fault tolerance
cp ~/.kothar/hooks/post-tool-fault-tolerance.sh ~/.kothar/hooks/post-tool-fault-tolerance.sh.backup
sed -i 's/MAX_RETRIES=3/MAX_RETRIES=2/' ~/.kothar/hooks/post-tool-fault-tolerance.sh
sed -i 's/BASE_DELAY=1000/BASE_DELAY=500/' ~/.kothar/hooks/post-tool-fault-tolerance.sh

# Reiniciar serviços
echo "Reiniciando serviços..."
source ~/.kothar/kothar-init.sh

echo "✅ Kothar v2.1.3 atualizado com sucesso!"
EOF
chmod +x ~/.kothar/scripts/update-to-v2.1.3.sh
```

## 📊 Métricas de Sucesso

### Indicadores de Monitoramento
1. **Tempo médio de execução**: < 30 minutos para tarefas complexas
2. **Taxa de sucesso**: > 95% das tarefas concluídas
3. **False positives do stall detector**: < 5%
4. **Uso de memória estável**: Sem picos de > 2GB
5. **Tempo de resposta**: < 5s para comandos simples

### Logs a Monitorar
- `~/.kothar/logs/stall-*.jsonl` - Eventos do stall detector
- `~/.kothar/logs/fault-tolerance-*.jsonl` - Tentativas de retry
- `~/.kothar/logs/session-*.log` - Logs completos da sessão

## 🔄 Manutenção Contínua

### Checklist Semanal
1. [ ] Verificar logs de stalls e faults
2. [ ] Limpar arquivos de contexto antigos
3. [ ] Atualizar configurações se necessário
4. [ ] Testar com novas cargas de trabalho

### Alertas Configurados
- Stall detector ativado por > 10 minutos
- Mais de 5 retries na mesma sessão
- Uso de memória > 1.5GB por 15 minutos contínuos

## 🎉 Conclusão

Este plano aborda todas as causas raiz identificadas:
- ✅ Reduz falsos positivos do stall detector
- ✅ Evita loops infinitos no fault tolerance
- � Implementa chunking para tarefas grandes
- � Centraliza e otimiza execução de hooks
- � Adiciona monitoramento adequado

Com estas correções, o Kothar deve conseguir executar tarefas complexas sem parar no meio do caminho.