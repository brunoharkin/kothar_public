---
tipo: spec
projeto: kothar
modulo: painel-cofre
status: aprovada
criado: 2026-06-01
---

# Spec — Painel do Cofre (Kothar vira app visual)

## Visão

Transformar o Kothar num **aplicativo visual completo** do Cofre. Em vez de abrir o
Obsidian, o Bruno tem controle total da Ugarit Digital pelo frontend: visualiza e
**edita** todo o conteúdo do Cofre de forma organizada, com visões especializadas por
seção.

> Decisão de arquitetura (2026-06-01): código permanece em `/home/bruno/kothar`
> (fora do Cofre). Primeira entrega já com **edição inline** (ler e salvar de volta
> nos `.md`). Visões especializadas em Funil, Produtos, Financeiro e Clientes.

## Escopo

Páginas (todas leem o filesystem do Cofre em tempo real):

| Página | Fonte no Cofre | Visão |
|--------|----------------|-------|
| Comercial | `03_Empresa/Comercial/` | leitura + edição |
| Estratégia | `03_Empresa/Estrategia/` | leitura + edição |
| Financeiro | `03_Empresa/Financeiro/` | **cards/números** + edição |
| Marketing | `03_Empresa/Marketing/` | leitura + edição |
| Operacional | `03_Empresa/Operacional/` | leitura + edição |
| Produtos | `03_Empresa/Produtos/` | **grade de cards** |
| Clientes | `04_Clientes/` | **painel operacional** (bugs, escopo, contrato) |
| Funil | `03_Empresa/Estrategia/funil/` | **kanban** (prospecção + desenvolvimento) |

Fora do escopo: pasta `Pessoas` (não vira página agora).

## Arquitetura

Segue o padrão Kothar: nomes em pt-BR, sem `src/components/utils`.

### Backend (`/home/bruno/kothar/backend/src/`)

```
cofre/
  caminho-seguro.ts    — resolve e valida paths DENTRO do Cofre (anti path-traversal)
  leitor-cofre.ts      — lerNota, listarPasta, árvore; parse frontmatter (gray-matter)
  escritor-cofre.ts    — salvarNota (re-serializa frontmatter + corpo)
  rotas-cofre.ts       — GET/PUT genéricos de qualquer nota
empresa/rotas-empresa.ts    — índices das seções da empresa
produtos/rotas-produtos.ts  — lista + detalhe de produtos (frontmatter: status, stack, dominio)
clientes/rotas-clientes.ts  — lista + detalhe (bugs-novos, escopo, contrato)
funil/
  analisador-funil.ts  — parse de funil-completo.md → fases e etapas (E1..E17)
  rotas-funil.ts
```

Base do Cofre via env `COFRE_PATH` (default `/home/bruno/Cofre`).

### Frontend (`/home/bruno/kothar/frontend/`)

```
servicos/
  api-cofre.ts, api-produtos.ts, api-clientes.ts, api-funil.ts
componentes/
  visualizador-markdown.tsx — render .md (react-markdown + remark-gfm + wikilinks)
  editor-markdown.tsx       — textarea cru + preview, salva via PUT
  navegador-notas.tsx       — árvore de notas de uma seção
paginas/
  comercial/ estrategia/ financeiro/ marketing/ operacional/
  produtos/ clientes/ funil/
app/
  comercial/page.tsx ... funil/page.tsx
```

## Regras

- Identidade visual: ecossistema Ugarit (Azul Safira `#2563EB`, Chakra Petch,
  bordas quadradas) — design system já existente no app.
- Edição salva o `.md` exato (frontmatter preservado). Nunca apagar histórico.
- Segurança: toda escrita/leitura validada por `caminho-seguro` — impossível sair do Cofre.
- Wikilinks `[[nota]]` viram navegação interna.

## Critérios de aceite

1. Cada seção lista suas notas e abre o conteúdo renderizado.
2. Editar uma nota pelo frontend e salvar reflete no `.md` do Cofre.
3. Funil exibe kanban com as 17 etapas agrupadas por fase.
4. Produtos exibe grade com status/stack por card.
5. Financeiro exibe cards de números além do texto.
6. Clientes exibe painel com bugs/escopo por cliente.
7. `tsc --noEmit` sem erros; bug-scan sem CRÍTICO/ALTO.
