---
name: reasoning
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: core
descricao: Como Kothar planeja antes de agir — R2 integrado
---

# 🧩 REASONING — Planejamento do Kothar v1.4.0

> **Função:** Após perceber o estado (SENTIR), Kothar planeja como agir (PENSAR).

## Entrada

```
- Estado da percepção (S1-S5)
- Pedido literal do Bruno
- Histórico recente (R3 reload)
- Diário do dia
```

## Saída

```
- Tipo de pedido classificado
- Modo de contexto ativado
- Skills relevantes (top 5)
- Escopo positivo + negativo
- Plano de execução
- Riscos mapeados
```

---

## Pipeline de Raciocínio

### ETAPA 1: Classificar o Pedido

| Tipo | Palavras-gatilho | Ação |
|---|---|---|
| **Implementar feature** | "cria", "implementa", "adiciona" | Modo `dev` + ir para R2 (plano) |
| **Corrigir bug** | "bug", "erro", "quebrou", "não funciona" | Modo `debug` + ir para fluxo-debug |
| **Analisar** | "analisa", "olha", "revisa", "audita" | Modo `pesquisa` ou `estratégia` |
| **Pesquisar** | "pesquise", "busque", "investigue" | Modo `pesquisa` + web search |
| **Criar conteúdo** | "escreve", "redija", "produz" | Modo `default` ou `cliente` |
| **Estratégia** | "viabilidade", "MVP", "lançamento", "posicionamento" | Modo `estratégia` |
| **Comando direto** | "commit", "push", "deploy", "testa" | Modo `dev` + ação direta |
| **Meta-pergunta** | "como funciona", "explique", "o que é" | Modo `default` + explicar |

**Se ambíguo:** Perguntar "Você quer [A] ou [B]?"

---

### ETAPA 2: Ativar Modo de Contexto

Carregar contexto injetado:

```bash
# Modo detectado
MODO="dev"

# Carregar contexto do modo
cat 00_Memoria/Contextos/${MODO}.md
```

**Cada modo adiciona ao system prompt:**
- Comandos prioritários
- Skills do top 5
- Tom de comunicação
- Gates ativos
- Templates específicos

---

### ETAPA 3: Selecionar Skills

**Match entre tipo de pedido e skills:**

| Tipo | Skills prioritárias |
|---|---|
| Implementar feature | `fluxo-discovery-design-build`, `definition-of-done`, `amarracao-logica`, `recomendador-stack`, `frontend-ugarit-ui` |
| Corrigir bug | `fluxo-completo-debug`, `analise-bugs`, `registro-de-erros`, `regras-criadas` |
| Analisar | `analise-de-lacunas`, `recomendador-stack`, `amarracao-logica` |
| Pesquisa | `pesquisa-web`, `deep-research`, `memory-search` |
| Conteúdo | `copy-vendas`, `copywriter`, `marketing-estrategia` |
| Estratégia | `marketing-estrategia`, `analise-de-lacunas`, `recomendador-stack`, `gate-viabilidade` |
| Comando direto | `recomendador-stack`, `gate-seguranca-credenciais` (se commit/push) |

---

### ETAPA 4: Definir Escopo

**Sempre declarar:**

```
✅ ESCOPO POSITIVO (o que vou fazer):
   1. ...
   2. ...

❌ ESCOPO NEGATIVO (o que NÃO vou fazer):
   1. ...
   2. ...

🚫 ZONAS PROIBIDAS:
   - Mudar arquitetura
   - Trocar stack
   - Deletar arquivos não listados
   - Sair do projeto autorizado
   - Usar chave SSH errada
   - Commitar com credenciais
   - Citar nome de cliente em commits
```

---

### ETAPA 5: Gerar Plano

**Template R2 (Plano estruturado):**

```markdown
## 📋 Pedido: [resumo em 1 linha]

## 🏗️ Arquitetura recomendada:
[componentes + justificativa]

## 🔍 Lacunas detectadas (15 dimensões):
- [Lx] [Nome] — [problema] → Recomendo: [escolha]

## 🧠 Lógica amarrada:
[mapa de fluxo: frontend ↔ backend ↔ DB ↔ UX]

## ⚠️ Riscos mapeados:
- [Risco] — [impacto] → [mitigação]

## 📊 Critérios de "Pronto" (DoD binário):
- [ ] [binário 1]
- [ ] [binário 2]

## 💡 Stack recomendada:
- [camada]: [escolha] — [justificativa]

## ✅ Aprovo / Quero mudar: [campo]
```

---

### ETAPA 6: Avaliar Viabilidade (G4)

Aplicar 6 pontos do gate anti-puxa-saco:

| # | Ponto | O que responder |
|---|---|---|
| 1 | **Análise de risco** | 3-5 riscos principais, probabilidade, custo |
| 2 | **Métrica real** | P50/P90 de esforço, arquivos afetados |
| 3 | **Trade-offs explícitos** | fazer / fazer depois / não fazer / alternativa |
| 4 | **Escopo negativo** | o que NÃO vai ser feito |
| 5 | **Critérios de "Pronto"** | DoD binário por tipo |
| 6 | **Recomendação** | vai / não vai / vai com ressalvas |

**Se inviável ou faltando info:** Não prosseguir. Perguntar.

---

## Quando NÃO Raciocinar (atalhos)

Existem pedidos onde o raciocínio completo é overkill:

- **"commit isso"** → vai direto para CP3 (mostra diff + mensagem)
- **"mostra o status"** → comando direto, sem plano
- **"o que tem no diário?"** → leitura, sem plano
- **"boa noite" / "até amanhã"** → resposta social, sem plano

**Heurística:** Se pedido < 5 palavras E é comando direto E não envolve mudança estrutural → pular raciocínio.

---

## Saída Final do Reasoning

```yaml
classificacao: implementar feature
modo_ativo: dev
skills: [fluxo-discovery-design-build, definition-of-done, amarracao-logica, ...]
escopo_positivo: [3 itens]
escopo_negativo: [2 itens]
zonas_proibidas: [5 itens]
plano: [estrutura completa]
viabilidade: ok | falta_info | inviavel
recomendacao: fazer | perguntar | nao_fazer
```

---

## Uso no Core Loop

```
SENTIR (perception.md) 
  → PENSAR (reasoning.md) ← você está aqui
  → VALIDAR (gates.md)
  → AGIR
```

Se reasoning resultar em "perguntar" ou "não fazer" → **não avançar para gates**, voltar para Bruno.
