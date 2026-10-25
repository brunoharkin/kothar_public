---
name: kothar-trace
description: Registrar e inspecionar sessões, eventos, thinking e métricas no frontend e painel de traces do Kothar. Ativar quando o usuário solicitar /kothar trace ou quando for necessário verificar a telemetria das sessões.
---

# Kothar Trace — Telemetria e Registro de Sessões

## Visão Geral
O comando `/kothar trace` permite ao operador inspecionar em tempo real o histórico e telemetria da sessão ativa:
- Entradas e saídas de agentes
- Cadeia de raciocínio (thinking)
- Chamadas de ferramentas e hooks
- Consumo de tokens e latência

## Como Usar
No chat de qualquer IDE integrada:
```text
/kothar trace
```
Ou no terminal:
```bash
~/kothar/scripts/kothar-cli.sh trace
```

## Painel Web de Traces
Para abrir a interface gráfica do frontend do Kothar com visualização em cascata:
- Acesse: `http://localhost:3030/trace` (ou na porta configurada em `FRONTEND_PORT`)
