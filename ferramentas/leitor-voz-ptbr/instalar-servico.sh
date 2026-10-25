#!/usr/bin/env bash

# Script de instalação do serviço autônomo Kothar Voice (Início com o Sistema)
set -e

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/kothar-voice.service"
SOURCE_SERVICE="/home/bruno-harkin/kothar/ferramentas/leitor-voz-ptbr/kothar-voice.service"

echo "[1/3] Criando diretório de serviços do usuário..."
mkdir -p "$SERVICE_DIR"

echo "[2/3] Instalando kothar-voice.service..."
cp "$SOURCE_SERVICE" "$SERVICE_FILE"

echo "[3/3] Recarregando systemd e habilitando na inicialização..."
systemctl --user daemon-reload
systemctl --user enable kothar-voice.service
systemctl --user restart kothar-voice.service

echo ""
echo "✅ Kothar Voice instalado e rodando com sucesso!"
echo "🌐 URL: http://localhost:3344"
echo "O serviço iniciará automaticamente sempre que a máquina ligar."

