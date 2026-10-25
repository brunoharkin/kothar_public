#!/bin/bash
# =============================================================
#  KOTHAR v4.0 — Script de Instalação Docker + Subida da Stack
#  Ubuntu 24.04 LTS (Noble) x86_64
#  Execute com: bash instalar-docker.sh
# =============================================================
set -euo pipefail

echo "============================================"
echo " KOTHAR — Instalando Docker Engine"
echo " Ubuntu 24.04 LTS"
echo "============================================"

# ---- 1. Pré-requisitos ----
echo "[1/6] Instalando dependências..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# ---- 2. Repositório oficial Docker ----
echo "[2/6] Adicionando repositório oficial Docker..."
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# ---- 3. Instalar Docker Engine + Compose Plugin ----
echo "[3/6] Instalando Docker Engine e Compose Plugin..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# ---- 4. Adicionar usuário ao grupo docker ----
echo "[4/6] Adicionando $USER ao grupo docker..."
sudo usermod -aG docker "$USER"

# ---- 5. Habilitar e iniciar serviço ----
echo "[5/6] Habilitando Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

# ---- 6. Verificar instalação ----
echo "[6/6] Verificando instalação..."
docker --version
docker compose version

echo ""
echo "============================================"
echo " Docker instalado com sucesso!"
echo "============================================"
echo ""
echo "IMPORTANTE: Faça logout e login novamente para"
echo "que o grupo 'docker' seja aplicado sem sudo."
echo ""
echo "Ou execute agora com: newgrp docker"
echo ""
echo "============================================"
echo " Próximos passos:"
echo "============================================"
echo ""
echo "1. Configure o .env:"
echo "   cd ~/kothar"
echo "   cp .env.example .env"
echo "   nano .env   # preencha com senhas fortes"
echo ""
echo "2. Suba a stack:"
echo "   docker compose up --build -d"
echo ""
echo "3. Acompanhe os healthchecks (Neo4j leva ~60s):"
echo "   watch docker compose ps"
echo ""
echo "4. Quando todos estiverem healthy, aplique as constraints do Neo4j:"
echo "   docker exec kothar_neo4j cypher-shell -u neo4j -p \$(grep NEO4J_PASSWORD .env | cut -d= -f2) -f /var/lib/neo4j/import/constraints.cypher"
echo ""
echo "5. Popular o ChromaDB com o Cofre (quando Cofre existir):"
echo "   docker exec kothar_api python3 scripts/popular_cofre_rag.py"
echo ""

