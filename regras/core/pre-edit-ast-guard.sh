#!/usr/bin/env bash
# pre-edit-ast-guard.sh (v2.0.0)
# Hook que roda ANTES de um arquivo ser modificado.
# Seu objetivo é prevenir Erro 009 (truncamento) e falhas sintáticas que LLMs costumam introduzir.

TARGET_FILE="$1"
TEMP_FILE="$2" # O arquivo com a edição proposta pelo Agente

# 1. Verifica extensão
EXT="${TARGET_FILE##*.}"

if [[ "$EXT" == "js" || "$EXT" == "ts" || "$EXT" == "tsx" ]]; then
    # Checa se o eslint local consegue parsear a AST do Temp File
    if ! npx eslint "$TEMP_FILE" --print-config > /dev/null 2>&1; then
        echo '{"status": "blocked", "reason": "AST quebrado. Possível truncamento de arquivo ou erro sintático grave. Edição abortada."}'
        exit 1
    fi
elif [[ "$EXT" == "py" ]]; then
    if ! python3 -m py_compile "$TEMP_FILE" > /dev/null 2>&1; then
         echo '{"status": "blocked", "reason": "Erro de compilação Python (indentation ou SyntaxError). Edição abortada."}'
         exit 1
    fi
fi

# Se chegou aqui, a AST é válida
echo '{"status": "allowed", "reason": "AST válida."}'
exit 0
