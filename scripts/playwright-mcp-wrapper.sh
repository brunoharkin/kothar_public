#!/usr/bin/env bash
# Wrapper para executar o Playwright MCP usando Node.js v22 e o Google Chrome nativo do sistema
export PATH="/home/bruno-harkin/.local/node22/bin:$PATH"
exec /home/bruno-harkin/.local/node22/bin/npx -y @playwright/mcp@latest --executable-path /usr/bin/google-chrome "$@"

