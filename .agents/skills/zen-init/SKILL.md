---
name: zen-init
description: >-
  Protocolo de Inicialização Minimalista e Warm Start para o Kothar
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
   - **Se o Handoff estiver ativo:** Carregar metadados, handoff, instruções vigentes, contrato de entrega e habilidades obrigatórias da próxima ação. Consultar contexto adicional apenas quando necessário. O snapshot não substitui políticas nem autoriza omitir segurança.
   - **Se for Início Fresco:** O fluxo normal de bootstrap do Kothar (prompt-principal + buscas ChromaDB) deve ser executado para fornecer ao agente todas as regras essenciais.

3. **Prevenção de Fadiga de Contexto:**
   - Evitar releituras sem finalidade. Reler regras/habilidades quando a tarefa, versão ou contexto mudar. Preservar a baseline de segurança e `auto-relatabilidade`; o relatório final lista apenas uso real da interação atual.
