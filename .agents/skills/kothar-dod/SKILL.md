---
name: kothar-dod
description: >-
  Skill do Kothar: Definition of Done — critérios binários de "Pronto" por tipo de feature.
  Ativar SEMPRE antes de declarar qualquer tarefa como concluída. Nunca declarar "Pronto"
  sem verificar todos os critérios desta skill. DoD é lei, não sugestão.
---

# Skill: Kothar DoD — Definition of Done

> **Regra-mãe:** NUNCA declarar "✅ Pronto" sem verificar todos os critérios binários. DoD é lei.

## DoD Universal (toda e qualquer tarefa)

```
[ ] U1 — Compilação OK (zero erros TypeScript/Python/qualquer linguagem)
[ ] U2 — Imports corretos (sem imports não usados ou faltando)
[ ] U3 — Lógica validada (trace completo do fluxo funciona)
[ ] U4 — Testes passam (sem falhas nos testes existentes)
[ ] U5 — Escopo preservado (nada fora do pedido foi tocado)
[ ] U6 — Credenciais scaneadas (zero chaves/senhas no código)
[ ] U7 — Console limpo (zero erros no terminal/browser)
```

---

## DoD por Tipo de Feature

### Feature de UI / Frontend
```
[ ] F1 — Componente renderiza sem erros no browser
[ ] F2 — Responsividade: mobile + desktop testados
[ ] F3 — Estados: loading, erro, vazio, sucesso — todos tratados
[ ] F4 — Acessibilidade: labels, aria, keyboard navigation
[ ] F5 — Performance: sem rerenders desnecessários
[ ] F6 — Integração com API funcionando (não mock hardcoded)
[ ] F7 — Screenshot ou descrição visual incluída no relatório
+ DoD Universal (U1-U7)
```

### Feature de Backend / API
```
[ ] B1 — Endpoint responde com status codes corretos (200/400/401/404/500)
[ ] B2 — Validação de input com Pydantic/Zod (sem aceitar dados inválidos)
[ ] B3 — Autenticação/autorização verificada (rota protegida funciona)
[ ] B4 — Erro tratado com mensagem clara (sem stack trace exposto)
[ ] B5 — Dados sensíveis não expostos na resposta
[ ] B6 — Teste de integração roda e passa
[ ] B7 — Documentação da rota atualizada (se aplicável)
+ DoD Universal (U1-U7)
```

### Bug Fix
```
[ ] D1 — Bug original não reproduz mais (seguir passos do report)
[ ] D2 — Nenhum teste existente quebrou por causa da correção
[ ] D3 — Sem regressão visual (se bug era funcional)
[ ] D4 — Causa raiz documentada ("o que era + por que acontecia")
[ ] D5 — Correção é mínima (diff mostra apenas o necessário)
+ DoD Universal (U1-U7)
```

### Commit / Git
```
[ ] G1 — gate-seguranca rodou: zero credenciais
[ ] G2 — Mensagem de commit no formato: tipo(escopo): descrição em pt-BR
[ ] G3 — Branch correta (não está em main por acidente)
[ ] G4 — Bruno aprovou push (CP4) se for para main/staging
[ ] G5 — CHANGELOG atualizado se for release
+ DoD Universal (U1-U7)
```

### Novo Projeto / Scaffold
```
[ ] P1 — Estrutura de pastas em pt-BR (sem src/, utils/, components/)
[ ] P2 — README.md presente com: objetivo, como rodar, variáveis de ambiente
[ ] P3 — .env.example criado (sem valores reais)
[ ] P4 — .gitignore inclui .env e arquivos de build
[ ] P5 — visao.md e estado-atual.md criados
[ ] P6 — Git inicializado com commit inicial
+ DoD Universal (U1-U7)
```

---

## Como Reportar DoD

Ao declarar "Pronto", sempre incluir no relatório:
```markdown
## DoD — [Nome da Feature]
**Tipo:** [UI/Backend/BugFix/Commit/Projeto]

### Universal
- [x] U1 — Compilação OK
- [x] U2 — Imports corretos
- [x] U3 — Lógica validada
... (todos os itens)

### Específico
- [x] F1 — Renderiza sem erros
... (todos os itens do tipo)

**Status:** ✅ Pronto / ❌ Bloqueado em [item]
```

---

*Kothar v4.0 — Definition of Done | Ugarit Digital*

