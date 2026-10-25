---
name: autonomous-checkpoint
description: >-
  Protocolo de Checkpoint Autônomo (PCA) e máquina de estado persistente do Kothar
---

# Skill: Autonomous Checkpoint (Save Game Protocol)

> **Função:** Garantir a resiliência do agente entre reinícios e quedas de sessão (como `/clear` ou expiração de token). Age como um "Save Game", permitindo que o agente retome tarefas longas de forma contínua do frame exato em que parou.

## 🎯 Protocolo de Salvamento Autônomo (PCA)

O agente deve gerar e gerenciar checkpoints de forma autônoma e proativa.

### 1. Gatilhos de Salvamento
O Kothar deve salvar um checkpoint nos seguintes cenários:
1. **Fim de Sub-etapa:** Assim que concluir uma fase definida no plano de voo (ex: Discovery, Design, Build parcial).
2. **Saturação de Janela (Token Limit):** Assim que estimar que a sessão consumiu mais de 100k-120k tokens ou ao perceber degradação na performance.
3. **Decisão Crítica:** Logo após alterar arquivos de configuração central ou esquemas de banco de dados.

### 2. Ações Executadas no Checkpoint
Ao disparar o salvamento, o agente deve:
1. **Gravar Checkpoint com Data:** Criar um arquivo markdown em `00_Memoria/Snapshots/handoff-ativo.md` (o checkpoint de retomada imediata).
2. **Histórico:** Salvar uma cópia estática em `00_Memoria/Snapshots/checkpoints/cp-[timestamp]-[slug-tarefa].md` para auditoria.
3. **Despedida e Clear:** Informar de maneira clara e direta que consolidou o estado, solicitar ao usuário que digite `/clear` para limpar a janela de tokens e `/kothar retomar` na próxima sessão.

---

## 📋 Flight Plan Protocol (Plano de Voo)

Antes de iniciar qualquer tarefa complexa (que necessite de mais de 2 passos ou alteração de múltiplos componentes), o agente deve:
1. Criar um checklist binário de tarefas (`[ ]`) no arquivo `00_Memoria/Snapshots/plano-voo-ativo.md` (ou similar do projeto).
2. Marcar cada etapa concluída com `[x]` e em progresso com `[/]`.
3. Injetar o progresso atualizado no cabeçalho do checkpoint.

---

## 📄 Template de Checkpoint (`handoff-ativo.md`)

O arquivo deve seguir estritamente o formato abaixo para garantir a leitura limpa pelo loader de contexto:

```markdown
# 📍 Checkpoint Kothar Ugarit

- **Projeto:** [NOME]
- **Tarefa:** [Nome curto da Tarefa]
- **Status:** [Etapa Atual / Total (ex: 3/5 Build)]
- **Timestamp:** [YYYY-MM-DD HH:MM:SS]

## 🎯 O que foi Feito (Consolidado)
- [x] Detalhes do que foi concluído na última sessão
- [x] Configurações alteradas e validadas

## 🚧 O que Fazer Imediatamente a Seguir (Bússola)
1. **Próxima Ação:** Detalhe exato do que o agente deve executar no primeiro segundo após a retomada.
2. **Passo Futuro:** Passos planejados subsequentes.

## 🚫 Caminhos Mortos (Evitar)
- Descrição de tentativas que deram errado ou erros que ocorreram para evitar repetição inútil de ações falhas.
```
