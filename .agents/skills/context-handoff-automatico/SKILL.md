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
1. **Logo após criar um plano multi-etapas:** O Kothar fez o discovery, buscou o contexto, criou o plano detalhado. Ele para.
2. **Ao finalizar qualquer etapa do plano:** O Kothar terminou a Etapa 1. Ele registra o que foi feito, prepara a Etapa 2, e para.
3. **Se a sessão ultrapassar 150k-200k tokens:** Cansaço iminente detectado pelo `contador-tokens.md`.

## 🔄 Fluxo de Handoff (Como Funciona)

### Passo 1: A Compressão (Fim da Sessão Atual)
Quando o gatilho dispara, o Kothar:
1. Condensa todo o contexto bruto (pesquisas soltas, logs longos) em informações objetivas.
2. Atualiza ou cria o arquivo `00_Memoria/Snapshots/handoff-ativo.md`.
3. O `handoff-ativo.md` conterá **apenas**:
   - O plano geral e o progresso.
   - O resultado já aprimorado e detalhado do discovery/pesquisas iniciais (sem o lixo da pesquisa bruta).
   - O escopo estrito da **próxima etapa**.

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
