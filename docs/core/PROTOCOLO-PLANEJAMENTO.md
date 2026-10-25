---
tipo: protocolo
id: protocolo-planejamento
titulo: Protocolo Obrigatório de Planejamento — Kothar
pertence_a: kothar
status: ativo
versao: 1.0
criado_em: 2026-09-05
---

# 📋 Protocolo Obrigatório de Planejamento — Kothar

> **Este protocolo é MANDATÓRIO. Nenhum agente pode iniciar execução sem seguir este fluxo.**

---

## Por Que Este Protocolo Existe

Durante o desenvolvimento, ocorrem travamentos, apagões de contexto e perda de informações. Este protocolo garante que:
- O plano existe ANTES de qualquer código ou mudança ser feita
- A cada etapa concluída, o progresso é registrado no cofre
- Em caso de travamento, o agente sabe exatamente onde parou
- O Maestro pode auditar qualquer trabalho consultando o cofre

---

## Fluxo Obrigatório (Gatilho Automático)

```
USUÁRIO APROVA TAREFA
        │
        ▼
[1] REGISTRAR PLANO NO COFRE
        │
        ▼
[2] EXECUTAR ETAPA 1
        │
        ▼
[3] ATUALIZAR PLANO (marcar etapa como concluída)
        │
        ▼
[4] EXECUTAR ETAPA 2
        │
        ▼
[5] ATUALIZAR PLANO
        │
       ...
        ▼
[N] CONCLUIR → MARCAR PLANO COMO COMPLETO
```

---

## Onde Salvar o Plano

O agente deve identificar o **contexto** da tarefa e salvar no lugar correto:

| Contexto da Tarefa | Onde Salvar o Plano |
|---|---|
| Trabalho em um **produto** (ex: ChronoDesk) | `empresa/produtos/comerciais/[produto]/planejamento/` |
| Trabalho em um **projeto de cliente** | `clientes/[cliente]/projetos/[projeto]/planejamento/` |
| Trabalho **geral/do Kothar/do cofre** | `planos/` (raiz do cofre) |
| Trabalho de **infraestrutura/devops** | `planos/` (raiz do cofre) |

---

## Formato Obrigatório do Arquivo de Plano

**Nome do arquivo:** `plano_YYYY-MM-DD_descricao-curta.md`

**Frontmatter obrigatório:**
```yaml
---
tipo: plano
id: plano_YYYY-MM-DD_titulo-curto
titulo: [Título descritivo da tarefa]
pertence_a: [produto/projeto/kothar]
status: aprovado | em-execucao | concluido | cancelado
criado_em: YYYY-MM-DD
atualizado_em: YYYY-MM-DD HH:MM
agente_responsavel: [nome do agente]
relacionado_com:
  - [caminho/para/documento-relacionado.md]
etapas_total: [número]
etapas_concluidas: [número atualizado a cada etapa]
---
```

**Corpo obrigatório:**
```markdown
## Contexto
[Por que este plano foi criado]

## Objetivo
[O que será entregue ao final]

## Regra de Atualização
A cada etapa concluída, atualizar este arquivo.

## Etapas
- [ ] ETAPA 01 — [descrição]
- [ ] ETAPA 02 — [descrição]
- [x] ETAPA 03 — [descrição] ← marcada quando concluída

## Log de Execução
| Data/Hora | Etapa | Ação | Status |
|---|---|---|---|
| YYYY-MM-DD HH:MM | ETAPA 01 | [o que foi feito] | ✅ |
```

---

## Regras de Atualização do Plano

1. **Antes de executar**: status = `em-execucao`
2. **Após cada etapa**: marcar `[x]`, incrementar `etapas_concluidas`, adicionar linha no Log
3. **Ao finalizar**: status = `concluido`, `etapas_concluidas` = `etapas_total`
4. **Se cancelado**: status = `cancelado` + justificativa no log

---

## Protocolo de Recuperação (Apagão/Travamento)

Se o agente reiniciar ou perder contexto, DEVE executar este procedimento:

```
1. Buscar no cofre o plano da tarefa em andamento
   → grep "status: em-execucao" cofre/planos/*.md
   → ou buscar na pasta do produto/projeto relevante

2. Ler o plano completo

3. Verificar a última etapa marcada [x]

4. Retomar da próxima etapa NÃO marcada

5. NÃO reiniciar do zero sem consultar o plano
```

---

## Verificação de Escopo (Para Projetos de Clientes)

Antes de executar qualquer trabalho em um projeto de cliente:

```
1. Ler: clientes/[cliente]/projetos/[projeto]/escopo.md
2. Confirmar que a tarefa está DENTRO do escopo
3. Se fora do escopo → PARAR e informar o Maestro
4. Registrar a verificação no Log do plano
```

---

## Para o Engenheiro Kothar — Prompt de Contexto

> Ao receber uma tarefa aprovada, você DEVE:
>
> **PASSO 1 — REGISTRAR PLANO**
> Antes de escrever uma linha de código ou mover um arquivo, crie o plano no cofre no caminho correto (produto, projeto ou `planos/`). Use o formato padrão com frontmatter YAML.
>
> **PASSO 2 — EXECUTAR COM ATUALIZAÇÃO**
> A cada etapa concluída, atualize imediatamente o plano: marque `[x]`, incremente `etapas_concluidas`, adicione linha no Log de Execução.
>
> **PASSO 3 — EM CASO DE DÚVIDA**
> Se perder contexto ou travar: busque o plano no cofre, leia, retome da última etapa concluída.
>
> **NUNCA comece execução sem plano registrado no cofre.**
> **NUNCA pule etapa sem atualizar o plano.**
> **NUNCA reinicie do zero sem consultar o plano existente.**
