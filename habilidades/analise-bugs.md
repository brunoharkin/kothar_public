---
name: analise-bugs
description: Analista de bugs — scanner estático, monitor de logs em tempo real, correção de botões sem ação, rotas 404, imports inválidos, TypeScript errors
version: 1.0.0
---

# Habilidade: Analista de Bugs

## Para que serve

Garante que nada quebrado é entregue. Roda automaticamente após cada edição de código (hook PostToolUse) e pode ser executado manualmente a qualquer momento. Monitora o dev server em tempo real durante testes manuais.

---

## Ferramentas

### `kothar-bug-scan` — Scanner Estático
```bash
kothar-bug-scan /path/projeto    # projeto completo
kothar-bug-scan --file arq.tsx   # arquivo único
kothar-bug-scan --md .           # relatório markdown
```

Detecta: botões sem onClick, handlers indefinidos, rotas 404, imports inválidos, API routes inexistentes, erros TypeScript, funções incompletas.

### `kothar-log-watch` — Monitor em Tempo Real
```bash
npm run dev 2>&1 | kothar-log-watch    # monitorar dev server
kothar-log-watch --report              # ver relatório atual
kothar-log-watch --clear               # limpar antes de novo teste
```

Detecta em logs: 404s, TypeErrors, crashes React, hydration errors, build failures, connection errors, promise rejections.

### Hook Automático
Ativo em `~/.claude/settings.json` — dispara após todo `Write` ou `Edit` em `.ts/.tsx/.js/.jsx`. Bugs CRÍTICO/ALTO aparecem no contexto automaticamente.

### 🛡️ Validação Automática e Score (v2.1.5)
Todo bug analisado e corrigido deve passar pela auditoria de integridade do Kothar:
1. **Sintaxe básica:** Executar `~/.kothar/scripts/validador.sh`.
2. **Analisador de Código:** Executar `python3 ~/.kothar/scripts/analise-codigo.py [arquivo]` para inspecionar estilo, placeholders e credenciais expostas.
3. **Mapeamento de Score:** O arquivo de alteração de bug deve obter obrigatoriamente score >= 90 no analisador.

---

## Bugs mais comuns detectados

| Bug | Sintoma | Fix |
|---|---|---|
| Botão sem ação | Clique não faz nada | Adicionar onClick={handler} |
| Handler indefinido | ReferenceError no console | Definir/importar a função |
| Rota 404 | Página não encontrada | Criar page.tsx na rota |
| Import inválido | Build: Module not found | Verificar caminho/arquivo |
| API 404 | fetch retorna 404 | Criar route.ts |
| Hydration error | Erro no console do browser | Mover código client para useEffect |

---

## Workflow de teste manual

```bash
# 1. Limpar sessão anterior
kothar-log-watch --clear

# 2. Iniciar dev server com monitoramento
npm run dev 2>&1 | kothar-log-watch

# 3. Testar no browser

# 4. Ver relatório de bugs capturados
kothar-log-watch --report

# 5. Passar para o Kothar corrigir
```

---

## Voltar
← [[catalogo-habilidades]]
