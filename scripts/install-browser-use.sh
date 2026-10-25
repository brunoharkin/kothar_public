#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - Instalador da Visão QA (Browser-Use)
# =========================================================================

set -e

echo "👁️ Instalando Browser-Use no ambiente do Kothar..."

# O container Docker usa o sistema diretamente sem venv (ou podemos instalar via pip)
# Para este instalador de scratch, garantimos que os pacotes essenciais sejam instalados.

docker exec -i kothar_api bash -c "
    pip install --upgrade pip
    pip install browser-use playwright
    playwright install chromium
"

echo "========================================================================="
echo "👁️ Visão Ativada! QA Agent agora pode 'ver' os testes localmente."
echo "========================================================================="
