#!/bin/bash

# Kothar Agent Browser CLI Wrapper
# Transforma os comandos do agente em requests ultra rápidos para o Daemon.

DAEMON_URL="http://localhost:8006"

COMMAND=$1
ARG1=$2

if [ "$COMMAND" = "goto" ]; then
  curl -s -X POST $DAEMON_URL/goto -H "Content-Type: application/json" -d "{\"url\": \"$ARG1\"}"
elif [ "$COMMAND" = "snapshot" ]; then
  curl -s -X POST $DAEMON_URL/snapshot
elif [ "$COMMAND" = "click" ]; then
  curl -s -X POST $DAEMON_URL/click -H "Content-Type: application/json" -d "{\"ref\": \"$ARG1\"}"
else
  echo "Uso: agent-browser <goto|snapshot|click> [args]"
  exit 1
fi
