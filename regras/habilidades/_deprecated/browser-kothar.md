---
tipo: habilidade
ferramenta: agent-browser
versao: 0.27.0
---

# browser-kothar — Automação de Navegador

← [[catalogo-habilidades]]

## O que é

Capacidade do Kothar de abrir, navegar, interagir e inspecionar aplicações web diretamente no browser — em tempo real, sem intervenção manual.

Baseada no **agent-browser** (Vercel Labs) — CLI nativa em Rust que controla Chrome via Chrome DevTools Protocol com um sistema de refs determinísticos (`@e1`, `@e2`) otimizado para LLMs.

**Skill instalada em:** `~/Cofre/.agents/skills/agent-browser`
**Binário:** `/usr/bin/agent-browser 0.27.0`
**Chrome:** `~/.agent-browser/browsers/chrome-149.0.7827.22`

---

## Quando usar

- Após implementar uma feature — ver como ficou no browser real
- Testar fluxo de usuário completo (login → ação → resultado)
- Debugar bugs visuais que não aparecem nos logs
- Inspecionar props/state de componentes React em dev
- Medir performance (Web Vitals) antes de marcar feature como pronta
- QA end-to-end sem abrir o browser manualmente

---

## Comandos principais

### Abrir e capturar
```bash
agent-browser open https://localhost:3000
agent-browser snapshot -i              # árvore de acessibilidade com refs
agent-browser screenshot               # PNG da viewport atual
agent-browser screenshot --pdf         # PDF da página
```

### Interagir
```bash
agent-browser click @e1               # clicar por ref
agent-browser fill @e2 "texto"        # preencher campo
agent-browser type @e3 "c"           # digitar caractere a caractere
agent-browser select @e4 "Opção"     # dropdown
agent-browser check @e5              # checkbox
agent-browser hover @e6              # mouse over
```

### Navegar
```bash
agent-browser back
agent-browser reload
agent-browser wait-for-url "/dashboard"
agent-browser wait-for-element @e1
```

### Extrair dados
```bash
agent-browser get text @e1
agent-browser get html @e1
agent-browser get attr @e1 href
agent-browser is visible @e1
agent-browser console               # logs JS da página
agent-browser get network-logs      # requisições de rede
```

### React + Performance
```bash
agent-browser react-inspect @e1     # component tree, props, state
agent-browser web-vitals            # LCP, CLS, FCP, TTFB, INP
```

### Estado e Storage
```bash
agent-browser get cookies
agent-browser get local-storage chave
agent-browser execute-script "return document.title"
```

### Mock de API (teste isolado)
```bash
agent-browser mock-route-intercept "api/users" 200 '{"users":[]}'
```

---

## Como o Kothar usa

### Fluxo padrão após implementar feature

```
1. agent-browser open https://localhost:PORTA
2. agent-browser snapshot -i
   → recebe: button "Login" [ref=@e1], input "Email" [ref=@e2]
3. agent-browser fill @e2 "usuario@email.com"
4. agent-browser click @e1
5. agent-browser wait-for-url "/dashboard"
6. agent-browser screenshot
   → confirma visualmente que funcionou
```

### Fluxo de debug visual

```
1. agent-browser open https://localhost:PORTA/pagina-com-bug
2. agent-browser console              → captura erros JS
3. agent-browser react-inspect @e5   → props e state do componente
4. agent-browser web-vitals          → performance
```

---

## Integração com habilidades existentes

| Habilidade | Como browser-kothar expande |
|---|---|
| `analise-bugs` | Antes: estático + logs. Agora: ver o bug acontecendo no browser |
| `frontend-ugarit-ui` | Antes: escrever código. Agora: abrir e validar visualmente |
| `verify` (skill) | Browser real para confirmar que feature funciona |

---

## Limitações

- Requer servidor local rodando antes de chamar `agent-browser open`
- Assets 3D pesados (WebGL/Three.js) podem demorar para carregar via proxy
- Ambiente headless — não executa no contexto do X display do usuário
- `agent-browser install --with-deps` pode ser necessário em ambientes sem libs gráficas
