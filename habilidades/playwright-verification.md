---
name: playwright-verification
description: Protocolo de verificação dinâmica em browser usando Playwright MCP. Ativa na Micro-Rotina R5 (antes de declarar Pronto) em qualquer feature que tenha interface web. Substitui o "funcionou no compilador" por "funcionou no browser".
version: 1.0.0
projeto: kothar
tipo: habilidade
data: 2026-08-12
---

# Skill: Playwright Verification (Verificação Dinâmica em Browser)

> **Filosofia (Thariq, Anthropic):** "Dar ao Claude uma forma de verificar seu próprio output é a dica mais importante. Uma vez que você faz isso, Claude itera até o resultado ser ótimo."
> 
> O `validador.sh` verifica sintaxe. Esta skill verifica **comportamento real** no browser.

---

## 🎯 Quando Ativar

Ativar SEMPRE que o trabalho envolva qualquer um destes:
- Interface web (frontend)
- Formulários, login, cadastro
- Fluxos de checkout ou pagamento
- APIs que retornam dados para o browser
- Alterações em rotas ou navegação
- Alterações visuais/CSS

**Não ativar para:** scripts shell puro, scripts Python sem UI, alterações só em banco de dados.

---

## 🔧 Pré-requisito: Playwright MCP

O Playwright MCP deve estar configurado em `~/.kothar/configuracao/mcp.json` ou `.mcp.json` do projeto:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {}
    }
  }
}
```

**Verificar se está disponível:**
```bash
npx @playwright/mcp@latest --version
```

---

## 📋 Protocolo de Verificação (Checklist R5 Estendido)

### Passo 1: Subir o Servidor Local
```bash
# Verificar se porta está livre (Gate G1 do pre-bash-guard)
~/.kothar/ports/check-port.sh {PORTA}

# Subir servidor
cd {PROJECT_ROOT}
npm run dev &  # ou equivalente do projeto
```

### Passo 2: Screenshot Inicial
```
[Playwright] Navegar para: http://localhost:{PORTA}
[Playwright] Tirar screenshot: verificacao-inicial.png
[Playwright] Verificar: página carregou sem erros 404/500
```

### Passo 3: Fluxos por Tipo de Feature

#### Para Login/Autenticação:
```
1. Navegar para /login (ou rota equivalente)
2. Screenshot da tela de login
3. Preencher campo usuário/email com dados de teste
4. Preencher campo senha com dados de teste
5. Clicar no botão de login
6. Screenshot após tentativa de login
7. Verificar: redirecionou para dashboard/home? ✅
8. Verificar: mensagem de erro visível? ❌ (se sim, bug!)
```

#### Para Formulários:
```
1. Navegar para a página com formulário
2. Screenshot do formulário vazio
3. Testar campo por campo com dados inválidos → verificar validação
4. Preencher com dados válidos
5. Submeter
6. Screenshot após submit
7. Verificar: mensagem de sucesso? Redirecionamento correto?
```

#### Para Listagens/Dashboard:
```
1. Navegar para a página
2. Screenshot geral
3. Verificar: dados aparecem (não vazio, não erro)
4. Testar filtros/busca se existirem
5. Verificar: scroll funciona, paginação funciona
```

#### Para Fluxos de Checkout/Pagamento:
```
⚠️ NUNCA usar dados reais de cartão em teste!
1. Usar modo sandbox/teste do gateway de pagamento
2. Navegar pelo fluxo completo
3. Screenshot a cada etapa
4. Verificar: chegou na tela de confirmação?
```

### Passo 4: Verificação de Console (Erros JS)
```
[Playwright] Verificar: console do browser tem erros JS? 
→ Se sim: registrar e corrigir antes de declarar Pronto
→ Se não: ✅
```

### Passo 5: Verificação de Rede (Chamadas API)
```
[Playwright] Verificar: chamadas de API retornaram 200?
→ Se alguma retornou 4xx/5xx: registrar e investigar
→ Se todas 2xx: ✅
```

---

## 🚦 Critérios de Aprovação

| Critério | Resultado Esperado |
|---|---|
| Página carrega | Status 200, sem erro |
| Sem erros JS no console | Console limpo |
| Fluxo principal funciona | Sequência de telas OK |
| APIs respondem | Todas 2xx |
| UI está como esperado | Screenshot corresponde ao design |

**Todos os critérios ✅ → pode declarar Pronto**
**Qualquer critério ❌ → corrigir e re-verificar**

---

## 📸 Evidência Obrigatória (R5)

Ao final da verificação, anexar na resposta:
1. Screenshot da tela principal funcionando
2. Log resumido: "Verificação Playwright: X/X critérios passaram"
3. Se houver falhas: "Falhas encontradas: [lista] → Corrigidas: [como]"

---

## 🔗 Integração com o Kothar

- **R5 (Gate Final):** Playwright Verification é o último item do DoD para features com UI
- **analise-codigo.py:** Verifica código estático ANTES do Playwright
- **validador.sh:** Verifica sintaxe ANTES do Playwright
- **Ordem correta:** `validador.sh` → `analise-codigo.py` → `playwright-verification`

---

## 💡 Dicas

1. **Servidor não subiu?** → Verificar porta com `check-port.sh`, verificar logs do processo
2. **Login falhou?** → Verificar se há usuário de teste no banco de dados
3. **Screenshot diferente do esperado?** → Comparar com o `design.md` da feature
4. **API 401/403?** → Verificar token de autenticação no ambiente de dev
5. **Playwright não disponível?** → Instalar via `npx @playwright/mcp@latest`

*Skill criada em 2026-08-12 — Inspirada na filosofia Thariq (Anthropic) de product verification skills*
