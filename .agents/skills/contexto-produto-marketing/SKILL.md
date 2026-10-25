---
name: contexto-produto-marketing
description: >-
  Contexto canônico de produto para tarefas de marketing, copy, vendas, SEO,
  CRO e lançamento. Ative antes de escrever mensagens, definir posicionamento
  ou recomendar crescimento. Bloqueie quando faltarem produto, público,
  problema, diferencial e objetivo mensurável.
metadata:
  version: 1.0.0
  owner: product-manager
  maturity: stable
  risk: medium
---

# Contexto de produto e marketing

Esta skill é uma pré-condição de domínio. Ela não substitui o agent responsável
e não autoriza alterar código, hooks, integrações ou métricas sem blueprint.

## Ordem obrigatória

1. Procurar contexto existente no projeto, nesta ordem:
   - `docs/produto/contexto-marketing.md`
   - `.agents/product-marketing.md`
   - `.claude/product-marketing.md`
   - `product-marketing-context.md`
2. Ler o pedido, blueprint e handoff anterior.
3. Reaproveitar fatos verificados; não inventar ICP, números, depoimentos ou
   diferenciais.
4. Registrar lacunas antes de recomendar ou produzir qualquer ativo.

## Contrato mínimo

O contexto deve responder, com evidência ou marcar `desconhecido`:

- Produto e problema resolvido.
- ICP, usuário comprador e usuário final.
- Dor, resultado desejado e momento de compra.
- Diferencial e alternativas/concorrentes.
- Oferta, preço ou restrições comerciais.
- Canal, objetivo e métrica primária.
- Voz, termos proibidos e limitações legais.

## Regras de decisão

- Se faltar um item crítico, faça uma pergunta única ou bloqueie a execução.
- Não trate suposição como dado de mercado.
- Separe fato, hipótese e recomendação.
- Toda recomendação deve incluir risco, métrica, trade-off, escopo negativo,
  DoD e veredicto.
- Para CRO, copy ou anúncio, encaminhe hipóteses mensuráveis para
  `ab-testing`/QA; não declare impacto sem experimento ou evidência.

## Handoff

Entregue um bloco estruturado com `facts`, `gaps`, `hypotheses`,
`primary_metric`, `constraints`, `related_skills` e `next_agent`.
