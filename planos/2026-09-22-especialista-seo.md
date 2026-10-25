# Plano aprovado: especialista SEO para páginas públicas

## Escopo

- Criar o agent nativo `seo`.
- Roteá-lo para discovery, páginas públicas, conteúdo, metadata, schema,
  sitemap, robots, performance e verificação de produção.
- Exigir classificação pública/privada antes da implementação.
- Encaminhar implementação para frontend, copywriter, a11y, e2e e devops.

## Fora do escopo

- Indexar páginas autenticadas ou dados operacionais.
- Garantir ranking orgânico.
- Instalar Claude SEO, MCPs ou APIs externas.
- Migrar o frontend para SSR/SSG.
- Criar skill nova.

## DoD

- [x] Manifesto SEO com gatilhos, não-gatilhos, contrato e bloqueios.
- [x] Registry inclui `seo` no perfil completo e nas rotas corretas.
- [x] SEO público e proteção privada são critérios explícitos.
- [x] 33 agents e 6 hooks passam na verificação.
- [x] Sincronização multi-IDE permanece idempotente.
