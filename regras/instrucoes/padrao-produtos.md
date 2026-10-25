---
tipo: padrao-operacional
versao: 1.0.0
---

# Padrão: Onboarding de Novo Produto

← [[manual-operacional]]

## Regra

Todo produto da Ugarit Digital segue este padrão sem exceção. Nenhuma estrutura é inventada, nenhum passo é pulado.

---

## Passo 1 — SSH key isolada

```bash
# Uma chave por produto, nunca compartilhada
ssh-keygen -t ed25519 -C "apps.ugarit@gmail.com" \
  -f ~/.ssh/id_ed25519_{nome-produto} -N ""

# Adicionar ao ~/.ssh/config
Host github-{nome-produto}
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_{nome-produto}
  IdentitiesOnly yes

# Adicionar known_hosts se necessário
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

Chave pública → adicionar no GitHub: Settings → SSH keys → Authentication Key.

---

## Passo 2 — Clone

```bash
# Sempre na raiz /home/bruno/, pasta nomeada exatamente como o produto
cd /home/harkin
git clone git@github-{nome-produto}:{org}/{repo}.git {nome-produto}
```

---

## Passo 3 — Análise do repositório

Ler nesta ordem:
1. `README.md` — visão geral e instruções
2. `CLAUDE.md` — regras do projeto
3. `.env.example` — variáveis e dependências externas
4. `package.json` / `requirements.txt` — stack exata
5. Estrutura de pastas — frontend, backend, infra
6. Arquivos chave: roteamento, banco, autenticação, deploy

---

## Passo 4 — Estrutura no Cofre

```
03_Empresa/Produtos/{nome-produto}/
├── {nome-produto}.md       ← nó principal no graph (visão + módulos + navegação)
└── docs/                   ← filtrado do graph, acessível pelo file explorer
    ├── arquitetura-{nome-produto}.md   ← stack, infra, diagrama, deploy, .env
    ├── agentes-ia-{nome-produto}.md    ← se tiver IA (agentes, modelos, fluxo)
    ├── banco-dados-{nome-produto}.md   ← schema, tabelas, migrations, RLS
    └── roadmap-{nome-produto}.md       ← fases concluídas e próximas entregas
```

**Regras dos arquivos:**
- `{nome-produto}.md` — YAML sem `atualizado:`, back-link `← [[produtos-ugarit]]`, **sem wikilinks para docs/**
- Docs em `docs/` — YAML sem `atualizado:`, back-link `← nome-produto` (**texto simples, não wikilink**), **zero wikilinks** — docs são navegados via file explorer, não pelo graph

---

## Passo 5 — Graph: filtro e cor

### Adicionar ao filtro `search` em `graph.json`

```
-path:"Produtos/{nome-produto}/docs"
```

### Adicionar `colorGroups` em `graph.json` (após os grupos existentes)

```json
{
  "query": "path:\"03_Empresa/Produtos/{nome-produto}\"",
  "color": { "a": 1, "rgb": {COR_RGB_INT} }
}
```

**Paleta de cores para produtos (usar em ordem):**

| Produto | Cor | RGB int |
|---------|-----|---------|
| ChronoDesk | Ciano #0ea5e9 | 959977 |
| Produto 2 | Violeta #8b5cf6 | 9134326 |
| Produto 3 | Rosa #ec4899 | 15484057 |
| Produto 4 | Lima #84cc16 | 8704022 |
| Produto 5 | Âmbar #f59e0b | 16097803 |

---

## Passo 6 — Registrar em produtos-ugarit.md

Adicionar o produto na seção correta (Em Desenvolvimento / MVP / Ativo):

```markdown
| [[{nome-produto}\|Nome Exibido]] | O que é | Stack |
```

---

## Conteúdo mínimo de cada arquivo

### `{nome-produto}.md`
- O que é e para quem
- Repositório (GitHub, clone local, SSH key, branch deploy, domínios)
- Tabela de módulos com status (✅ / 🔄 / ⏳)
- Seção "Documentação técnica" listando os docs/ em texto simples (sem wikilinks)
- `← [[produtos-ugarit]]`

### `arquitetura-{nome-produto}.md`
- Diagrama ASCII do fluxo completo
- Stack frontend e backend com versões
- Mapa de rotas/proxy
- Segurança (auth, CORS, rate limit, headers)
- Infra/deploy (VPS, Docker, CI/CD, domínios)
- Variáveis de ambiente (.env completo)

### `banco-dados-{nome-produto}.md`
- Engine, banco, extensões, porta
- Todas as tabelas com descrição
- RLS: como funciona no projeto
- Migrations em ordem cronológica
- Triggers (se existirem)

### `agentes-ia-{nome-produto}.md`
- Arquitetura geral (diagrama)
- Modelos usados com custo por token
- Cada agente: nome, função, tools disponíveis
- Sistema de memória (se existir)
- Regras de segurança da IA

### `roadmap-{nome-produto}.md`
- Status atual (fase + descrição)
- Fases com checkboxes (concluído / em andamento / próximo)
- Próximas 3 entregas prioritárias

---

## Checklist final antes de considerar concluído

- [ ] SSH key criada e adicionada no GitHub
- [ ] Repo clonado em `/home/bruno/{nome-produto}`
- [ ] `{nome-produto}.md` criado com YAML sem `atualizado:`
- [ ] `docs/` criados com back-link `← nome-produto` em texto simples (sem `[[]]`)
- [ ] `produtos-ugarit.md` atualizado
- [ ] `graph.json`: filtro `-path:"Produtos/{nome-produto}/docs"` adicionado
- [ ] `graph.json`: colorGroup do produto adicionado
- [ ] **Zero wikilinks** em qualquer arquivo dentro de `docs/`
- [ ] **Zero wikilinks para `docs/`** no `{nome-produto}.md` — seção "Documentação técnica" usa texto simples, não `[[docs/...]]`
