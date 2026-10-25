#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - Arsenal de Segurança (SecLists + Nuclei)
# Instalador de Ferramentas para Defesa Ativa e DAST
# =========================================================================

set -e

echo "🛡️ Iniciando instalação do Arsenal de Segurança Kothar..."

mkdir -p /home/bruno/kothar/scratch/bin
mkdir -p /home/bruno/kothar/scratch/security

cd /home/bruno/kothar/scratch/security

# 1. SecLists (Wordlists, Passwords, Payloads)
if [ ! -d "SecLists" ]; then
    echo "📦 Clonando SecLists (Shallow clone para poupar tempo/espaço)..."
    git clone --depth 1 https://github.com/danielmiessler/SecLists.git
else
    echo "✅ SecLists já instalado."
fi

# 2. Nuclei (Motor de DAST e PenTest Automatizado)
NUCLEI_BIN="/home/bruno/kothar/scratch/bin/nuclei"
if [ ! -f "$NUCLEI_BIN" ]; then
    echo "☢️ Baixando Nuclei..."
    # Baixando versão compilada para Linux amd64
    wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.2.0/nuclei_3.2.0_linux_amd64.zip -O nuclei.zip
    unzip -q nuclei.zip nuclei
    mv nuclei /home/bruno/kothar/scratch/bin/
    chmod +x /home/bruno/kothar/scratch/bin/nuclei
    rm nuclei.zip
    echo "✅ Nuclei instalado em $NUCLEI_BIN"
else
    echo "✅ Nuclei já instalado."
fi

# 3. Nuclei Templates
if [ ! -d "/home/bruno/nuclei-templates" ]; then
    echo "📋 Baixando templates do Nuclei..."
    /home/bruno/kothar/scratch/bin/nuclei -update-templates
else
    echo "✅ Nuclei templates já atualizados."
fi

echo "========================================================================="
echo "🛡️ Instalação Concluída! O Arsenal está pronto para a Engenharia de Invasão."
echo "========================================================================="
