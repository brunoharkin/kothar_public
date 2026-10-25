---
name: validador-execucao
description: Diretrizes de assertividade e indicadores de validação automatizada de código
version: 1.0
projeto: kothar
tipo: habilidade
---

# Skill: Indicadores de Assertividade e Validação de Execução

## Diretriz de Qualidade
Todo código escrito deve passar pelos indicadores automatizados antes de ser considerado "Pronto". Isso evita regressões de sintaxe ou de lógica básica.

## Protocolo de Testes e Pontuação
1. **Frontend:** Executar compilação/build e validar erros de tipagem/linter.
2. **Backend:** Executar `node -c` (JavaScript) ou `tsc` (TypeScript) para verificar erros sintáticos.
3. **Qualidade de Sintaxe:** Pontuação gerada via `analise-codigo.py` (deve ser maior ou igual a 90).

Use o script `~/.kothar/scripts/validador.sh` e o analisador `~/.kothar/scripts/analise-codigo.py` para automatizar as checagens no final da fase de Build (Verify phase).
