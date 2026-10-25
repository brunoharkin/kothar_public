---
name: zen-init
description: Protocolo de Inicialização Minimalista e Warm Start para o Kothar
version: 1.0.0
projeto: kothar
tipo: habilidade
---

# Skill: Zen Initialization (Warm Start)

> **Função:** Silenciar a burocracia e o ruído visual de inicialização do terminal do usuário, carregando de forma eficiente e veloz apenas o contexto ativo e as pendências imediatas.

## 🎯 Diretrizes Core

1. **Warm Start Banner:**
   - O terminal do usuário **não** deve ser inundado com regras globais e prompts estáticos a cada início de sessão.
   - O hook de inicialização (`kothar-session-init.sh`) deve exibir apenas uma linha descritiva no terminal (`stderr`), por exemplo:
     `[HERMES v2.2.0] Ativo | Projeto: cofre | Etapa: Discovery`
     ou, caso seja uma retomada de checkpoint:
     `[HERMES v2.2.0] Conectado | Projeto: cofre | Retomando Checkpoint... Pronto.`

2. **Detecção de Retomada (Handoff Ativo):**
   - O sistema de carregamento de contexto (`kothar-context-loader.sh`) deve buscar se existe o arquivo `00_Memoria/Snapshots/handoff-ativo.md` na raiz do projeto selecionado.
   - **Se o Handoff estiver ativo:** O contexto injetado no LLM deve ser restrito exclusivamente aos metadados do projeto, ao conteúdo de `handoff-ativo.md` e a esta skill. O `prompt-principal.md` completo e as buscas ChromaDB devem ser **ignoradas**, economizando até 15.000 tokens e prevenindo lentidão e estouros de janela de contexto.
   - **Se for Início Fresco:** O fluxo normal de bootstrap do Kothar (prompt-principal + buscas ChromaDB) deve ser executado para fornecer ao agente todas as regras essenciais.

3. **Prevenção de Fadiga de Contexto:**
   - O agente está terminantemente **proibido** de re-ler arquivos markdown estruturais de documentação global (como `prompt-principal.md`, `manual-operacional.md`, `gates.md` ou `checkpoints.md`) durante uma conversa de retomada, pois as regras de negócio e de sandbox já foram injetadas. Toda a memória de trabalho deve ser recuperada a partir do snapshot consolidado.
