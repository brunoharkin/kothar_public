#!/usr/bin/env bash
set -euo pipefail

echo "Limpando sessões anteriores..."
rm -f /home/bruno/kothar/.current_session
pkill -f antigravity_tracer.py || true

echo "Criando nova sessão limpa..."
/home/bruno/kothar/cli/kothar.sh session create "Maestro Kothar v3.0"

touch /home/bruno/kothar/.recording

echo "Iniciando trace-daemon..."
nohup python3 /home/bruno/kothar/scripts/antigravity_tracer.py > /home/bruno/kothar/trace-daemon.log 2>&1 &

echo "Gravação ATIVA!"
