# Frontend — Regras de Desenvolvimento Kothar

## Estrutura Obrigatória

```
frontend/
├── paginas/{pagina}/
│   ├── {pagina}.page.{tsx,jsx}
│   ├── {pagina}.styles.{css,scss}
│   └── {pagina}.types.{ts,tsx}
├── componentes-compartilhados/
│   ├── {nome}.component.{tsx,jsx}
│   └── {nome}.styles.{css,scss}
├── utilitarios/
│   └── {nome}.util.{ts,tsx}
└── tipos/
    └── {nome}.types.{ts,tsx}
```

## Regras de Nomenclatura

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Página | `{pagina}.page.{tsx,jsx}` | `login.page.tsx` |
| Componente | `{Nome}.component.{tsx,jsx}` | `BotaoConfirmar.component.tsx` |
| Estilo | `{nome}.styles.{css,scss}` | `tela-login.styles.css` |
| Tipo | `{nome}.types.{ts,tsx}` | `usuario.types.ts` |
| Hook | `use{nome}.hook.{ts,tsx}` | `useAuth.hook.ts` |
| Context | `{nome}.context.{tsx,ts}` | `Auth.context.tsx` |

## Regras de UI/UX

1. **NUNCA** usar `src/` → usar `frontend/`
2. **NUNCA** usar `components/` genérico → usar `componentes-compartilhados/`
3. **TODAS** as páginas devem ter loading state
4. **TODAS** as requisições devem ter tratamento de erro
5. **NUNCA** deixar credenciais no código

## GATES Aplicáveis

- G3: Credenciais (OBRIGATÓRIO scan antes de commit)
- G5: Nomenclatura (português, PascalCase para componentes)

---

*Ugarit Digital — Kothar v3.0*
