# Avaliação de Modelos Kothar - Resultados

## Objetivo
Testar a capacidade real de cada modelo local para assumir o papel do Kothar.

## Modelos Testados
- **kothar-gemma:latest** (base: gemma2:2b) - 1.6GB VRAM
- **kothar-coder:latest** (base: qwen2.5-coder:1.5b) - 1GB VRAM
- **kothar-deepseek:latest** (base: deepseek-r1:1.5b) - 1.1GB VRAM

## Diagnóstico: Por que falham?

### Causa Raiz #1: Sem System Prompt
A API estava enviando as mensagens **sem nenhum system prompt**. Os modelos não sabiam que deveriam agir como "Kothar". Por isso respondiam coisas genéricas como "Olá! Como posso ajudar hoje?".

**Evidência na imagem:**
- kothar-gemma: resposta vazia (modelo não soube o que fazer)
- kothar-coder: "Olá! Meu nome é Kothar Native AI" (inventou, mas perdeu contexto)
- kothar-deepseek: "Olá! Como posso ajudar hoje?" (resposta genérica de ChatGPT)

### Causa Raiz #2: Tamanho dos Modelos
Modelos de 1.5B-2B parâmetros têm limitações severas:
- Capacidade limitada de seguir instruções complexas
- Janela de atenção curta (esquecem contexto rápido)
- Dificuldade com raciocínio multi-etapa
- Não conseguem manter persona consistente

## Solução Implementada (Nível 1: Prompt Engineering)

### Mudanças no `ollama.api.ts`
1. **System prompt automático** injetado quando não há um
2. Prompt compacto otimizado para modelos pequenos

### System Prompt Injetado
```
Você é Kothar v3.0, o Maestro do Orquestro Digital. 
Assistente técnico especializado em desenvolvimento, 
análise de código, arquitetura e planejamento. 
Responda em português brasileiro, de forma técnica e direta. 
Use markdown quando útil.
```

## Resultados Após Correção (esperado)

### Teste 1: Identidade
**Pergunta:** "Olá, qual o seu nome?"

| Modelo | Resposta Anterior | Resposta Esperada |
|--------|-------------------|-------------------|
| kothar-gemma | (vazio) | "Sou Kothar v3.0, Maestro do Orquestro Digital..." |
| kothar-coder | "Kothar Native AI" | "Sou Kothar v3.0..." |
| kothar-deepseek | "Como posso ajudar?" | "Sou Kothar v3.0..." |

### Teste 2: Capacidades
**Pergunta:** "Qual sua habilidade?"

| Modelo | Score Anterior | Score Esperado |
|--------|----------------|----------------|
| kothar-gemma | 0/10 | 6/10 |
| kothar-coder | 4/10 | 7/10 |
| kothar-deepseek | 2/10 | 7/10 |

## Próximo Passo: Few-Shot Prompting (Nível 2)

Adicionar 2-3 exemplos de conversas Kothar no system prompt. Isso ensina o modelo o **estilo** e **formato** esperado, mesmo que não tenha capacidade de raciocínio profundo.

Arquivo: `kothar-prompts.ts` já tem versão completa com exemplos.

## Quando Considerar Fine-Tuning (Nível 3)?

Fine-tuning faz sentido se:
- ✅ Prompt engineering + few-shot não alcançarem 7/10 consistentemente
- ✅ Você tiver GPU com 8GB+ VRAM disponível (para treinar 7B)
- ✅ Tiver dataset de 100+ exemplos de conversas Kothar reais

**Recomendação:** Antes de fine-tuning, tente few-shot. Se os modelos ainda falharem em tarefas básicas, o problema é tamanho do modelo, não treinamento.

## Como Testar

1. Recarregue o frontend (localhost:5180)
2. Abra a página Ollama
3. Envie "Olá, qual o seu nome?" para cada modelo
4. Compare respostas

Se as respostas seguirem o padrão Kothar, o Nível 1 funcionou. Se ainda estiverem fracas, ative o few-shot no `kothar-prompts.ts`.