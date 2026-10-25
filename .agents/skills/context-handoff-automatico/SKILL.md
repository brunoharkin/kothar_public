---
name: context-handoff-automatico
description: >-
  Skill do Kothar: Skill: Handoff Automático de Contexto. Ativar quando necessário para execução da habilidade context-handoff-automatico.
---

# Skill: Handoff Automático de Contexto

> **Função:** Impedir a "alucinação de cansaço" (context overflow) do modelo. Transforma uma tarefa longa e complexa em sessões ultra-focadas e curtas.

## 🎯 O Problema
Modelos com 1M de contexto perdem precisão quando a conversa se estende. O contexto bruto (resultados de pesquisas extensas, tentativas, erros) polui a janela. 
**Solução:** Sempre que houver um plano com **mais de uma etapa**, o Kothar está PROIBIDO de executar a primeira etapa imediatamente. Ele deve salvar o contexto limpo, parar e pedir ao usuário para limpar o chat.

## 🔴 Gatilhos Obrigatórios

Esta habilidade é engatilhada automaticamente nas seguintes situações:
1. **Logo após criar um plano multi-etapas:** O Kothar fez o discovery, buscou o contexto, criou o plano detalhado. Ele para e grava o handoff.
2. **Ao finalizar qualquer sub-etapa de implementação:** O Kothar terminou a sub-etapa ativa. Ele testa, registra o que foi feito no `handoff-ativo.md`, prepara a próxima sub-etapa e para.
3. **Se a sessão ultrapassar 60k-80k tokens (ou após 5 tool calls complexas):** Cansaço e risco iminente de rate limit de 5 horas.

## 🔄 Fluxo de Handoff (Como Funciona)

### Passo 1: A Compressão Estrita (Máximo 50 linhas)
Quando o gatilho dispara, o Kothar:
1. Condensa todo o contexto bruto em estritamente no máximo **50 linhas de texto Markdown**.
2. Atualiza ou cria o arquivo `00_Memoria/Snapshots/handoff-ativo.md`.
3. O `handoff-ativo.md` conterá **apenas**:
   - Projeto e status da fase.
   - O que foi concluído (3-5 bullets).
   - O escopo estrito da **próxima sub-etapa** (1 único módulo ou endpoint).
   - Dependências imediatas obtidas via Grafo (Neo4j / AST), sem dumps de arquivos.
   - **PROIBIDO:** colar logs de erros, transcrições longas ou código fonte completo dentro do handoff.

### Passo 2: O Alerta (Interrupção)
O Kothar emite o seguinte bloco EXATO na tela do usuário, parando qualquer execução:

```markdown
🛑 **LIMITE DE CONTEXTO / FIM DE ETAPA ATINGIDO**
O plano e o contexto aprimorado foram gravados. Para garantir precisão máxima e economizar tokens, precisamos de uma sessão limpa.

Por favor, faça o seguinte:
1. Digite `/clear` para limpar esta janela de chat.
2. Digite `/kothar retomar` para continuarmos exatamente da próxima etapa, apenas com a memória essencial.
```

### Passo 3: A Retomada (Nova Sessão Iniciada com `/kothar retomar`)
Quando o usuário digita `/kothar retomar`, o Kothar:
1. **NÃO LÊ** o histórico complexo.
2. Lê apenas o `00_Memoria/Snapshots/handoff-ativo.md`.
3. Sabe imediatamente qual etapa executar e inicia o trabalho.

### Passo 4: Conclusão Final
Na última etapa, em vez de um Handoff, o Kothar executa uma consolidação:
1. Lê todos os registros de handoffs parciais / diárias recentes.
2. Gera o **Relatório Final** da tarefa inteira.
3. Finaliza a tarefa declarando o fechamento do plano.

## ⚠️ Restrição (Anti-Puxa-Saco)
- O Kothar nunca avança de fase sem realizar o Handoff. É inegociável. A precisão do código depende de um contexto limpo a cada nova etapa.
