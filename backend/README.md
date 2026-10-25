# Backend — Regras de Desenvolvimento Kothar

## Estrutura Obrigatória

```
backend/
├── servidor-principal.{ts,py,go}
├── rotas/
│   └── {recurso}.routes.{ts,py,go}
├── servicos/{feature}/
│   ├── {feature}.service.{ts,py,go}
│   └── {feature}.types.{ts,py}
├── banco/
│   ├── conexao.{ts,py,go}
│   └── migrations/
├── utilitarios/
│   └── {nome}.util.{ts,py}
└── tipos/
    └── {nome}.types.{ts,py}
```

## Regras de Nomenclatura

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Arquivo servidor | `servidor-{modulo}.{ts,py}` | `servidor-autenticacao.ts` |
| Rotas | `{recurso}.routes.{ts,py}` | `usuario.routes.ts` |
| Serviços | `{feature}.service.{ts,py}` | `pagamento.service.ts` |
| Utilitários | `{nome}.util.{ts,py}` | `validacao-cpf.util.ts` |
| Tipos | `{nome}.types.{ts,py}` | `usuario.types.ts` |

## Regras de Negócio

1. **TODAS** as queries SQL devem usar parâmetros protegidos
2. **NENHUMA** credencial no código → usar `.env`
3. **TODAS** as funções assíncronas devem ter tratamento de erro
4. **CADA** endpoint deve ter validação de entrada
5. **NUNCA** fazer commit com `console.log` em produção

## Portas Reservadas Backend

| Serviço | Porta |
|---------|-------|
| Evolution API (primária) | 2785 |
| Evolution API (secundária) | 2786 |
| Servidor Node/Express | 3000 |
| Servidor FastAPI | 8000 |
| Servidor Go | 8080 |

## Gates Aplicáveis

- G3: Credenciais (OBRIGATÓRIO scan antes de commit)
- G4: Viabilidade (para features novas)
- G5: Nomenclatura (português, descritivo)

---

*Ugarit Digital — Kothar v3.0*
