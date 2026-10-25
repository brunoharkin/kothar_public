---
name: engenharia-de-ia-producao
description: >-
  Diretrizes de Engenharia de IA de Produção e Arquitetura de Sistemas com LLMs (baseada na metodologia de Ronnald Hawk e padrões canônicos da Anthropic).
  Ativar obrigatoriamente ao projetar, implementar ou revisar qualquer sistema com LLMs, agentes conversacionais, harnesses, RAG, rotas de IA ou automações de WhatsApp.
  Substitui práticas amadoras (vibe coding, prompts soltos) por padrões de engenharia: Harness desacoplada com Debounce/DLQ, Guardrails em 3 camadas, Workflows estruturados (Router/Orchestrator-Workers), Evals semânticos automatizados e Loop Engineering.
---

# Skill: Engenharia de IA de Produção (Production AI Engineering)

> **Regra Suprema de Engenharia:** "Modelos são commodities; o produto é a Harness e o Sistema ao redor."
> Não construímos demos frágeis; construímos sistemas de software resilientes, observáveis, tolerantes a falhas e orientados a métricas reais.

---

## 🏛️ Os 6 Pilares Inegociáveis

### 1. Harness como o Produto Central (Desacoplamento)
- A LLM **NUNCA** deve ser exposta diretamente ao webhook de clientes ou usuários.
- A Harness é a casca de software estável que absorve a instabilidade e a lentidão dos modelos:
  - **ACK Imediato:** Responder ao webhook do WhatsApp/Meta com `HTTP 200` em menos de 200ms.
  - **Buffer Debounce:** Agrupar rajadas de mensagens curtas sequenciais (janela de 2.5s a 3.5s por remetente) em um único lote consolidado antes de chamar o modelo.
  - **Fila Assíncrona & DLQ:** Erros persistentes após 3 tentativas com backoff exponencial são enviados para uma Dead-Letter Queue para transbordo ou revisão humana.
  - **Resiliência a Troca de Modelos:** Se o modelo for trocado (Claude $\to$ GPT $\to$ Qwen local via Ollama), a harness permanece 100% idêntica.

### 2. Guardrails em Três Camadas (Código sobre Prompts)
A segurança não depende de instruções soltas de prompt. Ela é garantida por código determinístico em 3 fronteiras:
1. **Entrada:** Bloqueio determinístico de *Prompt Injection* antes de chamar a LLM; sanitização e mascaramento automático de PII (CPF, cartões, dados sensíveis). Se violar, corta a execução economizando tokens.
2. **Ferramentas (Tool Calls):** Validação estrita de schemas com Zod/Pydantic. Aplicação obrigatória de **Human-In-The-Loop (HITL)** (Checkpoints CP1 a CP6 do Kothar) para qualquer ação irreversível ou de alto impacto (deletar dados, disparos em massa, pagamentos).
3. **Saída:** Varredura estrita e bloqueio contra vazamento de chaves de API, credenciais de banco ou alucinações de preço antes de enviar a resposta final ao usuário.

### 3. Padrões Formais de Workflows (Chega de Agentes Caóticos)
Para toda demanda com IA, escolher e justificar formalmente um dos 5 padrões arquiteturais da Anthropic:
- **Prompt Chaining:** Tarefas lineares decompostas em passos sequenciais determinísticos.
- **Router (JEV - Just-in-Time Evaluation):** Classificação rápida da intenção usando modelos econômicos/rápidos para direcionar para caminhos especialistas.
- **Parallelization:** Subtarefas independentes processadas simultaneamente com agregação posterior.
- **Orchestrator-Workers (Swarm):** Um orquestrador central (Kothar Maestro) planeja e delega para subagentes especialistas com contratos de interface claros.
- **Evaluator-Optimizer:** Um gerador gera, um auditor critica e valida contra critérios objetivos antes da entrega.

### 4. Evals Semânticos & Benchmark (LLM-as-a-Judge)
- Não se mede a confiabilidade de um agente apenas com testes unitários tradicionais.
- Antes de qualquer deploy de prompt, modelo ou harness, rodar obrigatoriamente a suíte de avaliação com dataset canônico (`scripts/kothar-evals.py`).
- Rubrica de avaliação obrigatória:
  1. *Fidelidade ao Contexto (Faithfulness):* Zero invenção além da base autorizada (Cofre/RAG).
  2. *Segurança & Guardrails:* Zero vazamento de dados ou quebra de restrições.
  3. *Completude:* Respondeu exatamente o problema solicitado.
  4. *Latência e Custo:* Tempo de resposta P50/P95 e contagem estrita de tokens.

### 5. RAG 3.0 & Particionamento Hierárquico de Contexto
- A busca semântica por similaridade de cosseno em chunks soltos quebra em bases grandes.
- RAG em produção exige:
  - Metadados rígidos de particionamento (por projeto, cliente, categoria).
  - Consulta hierárquica: Grafo/AST primeiro $\to$ Resumo de Documento $\to$ Chunks pontuais.
  - **Anti-Context Fatigue:** Proibido dump massivo de contexto na sessão ativa (máximo de 1.500 tokens ou Top-3 nós relevantes).

### 6. Spec-Driven Development & Loop Engineering (Anti-Vibe Coding)
- Proibido programar por intuição ("vibe coding"). O código só existe a partir de uma especificação ou plano formal registrado no Cofre (`planos/` ou `00_Memoria/`).
- **Loop Engineering:** O agente propõe o código, compila e roda os testes no mesmo ciclo de execução. Se encontrar erros de linting ou teste, o próprio agente auto-corrige cirurgicamente e só entrega o resultado quando o Definition of Done (DoD) estiver 100% satisfeito.

---

## 🛠️ Ferramentas e Implementações Oficiais do Kothar

- **Debounce Worker:** `backend/servicos/harness/debounce_worker.py`
- **Guardrails Middleware:** `backend/servicos/harness/guardrails_middleware.py`
- **Evals Runner:** `scripts/kothar-evals.py`
- **Validador de Browser:** `scripts/playwright-mcp-wrapper.sh` (Google Chrome nativo)
- **Plano Mestre de Produção:** `/home/bruno-harkin/Cofre/planos/2026-10-19-plano-harness-engenharia-de-producao.md`

← [[catalogo-habilidades]]

