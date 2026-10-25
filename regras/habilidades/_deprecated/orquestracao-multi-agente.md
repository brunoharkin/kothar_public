---
name: orquestracao-multi-agente
description: Orquestração de agentes de desenvolvimento especializados (Swarm) baseada no Ruflo com sincronização no segundo cérebro
version: 1.0.0
ferramenta: ruflo (ruvnet/ruflo)
---

# Habilidade: Orquestração Multi-Agente (Swarm)

## Por que existe

Desenvolver sistemas complexos (frontend premium, APIs complexas, integrações) em um único fluxo sequencial de agente único gera sobrecarga cognitiva e erros recorrentes. 

Esta habilidade cria uma arquitetura de **Swarm de Agentes Especializados**, onde diferentes "personas" colaboram paralelamente, utilizando o **Cofre Obsidian** como banco de dados compartilhado de estado e memória coletiva (Hive-Mind).

---

## 👥 Papéis do Swarm de Agentes

Cada agente possui escopo isolado de atuação, regras e ferramentas específicas:

```
                  ┌──────────────────────┐
                  │ Orquestrador (Kothar)│ ◄─── Usuário
                  └──────────┬───────────┘
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │Desenvolvedor │    │   Revisor    │    │   Testador   │
  └──────────────┘    └──────────────┘    └──────────────┘
```

### 👑 1. Orquestrador (Kothar)
* **Função**: Decompor o objetivo do usuário em planos de especificação (`spec.md`), planos técnicos (`plan.md`) e checklists de tarefas (`tasks.md`).
* **Responsabilidade**: Coordenar o ciclo de vida do desenvolvimento, delegar tarefas aos especialistas, consolidar feedbacks de bugs e garantir o cumprimento de regras gerais (como responder apenas em pt-BR e usar nomenclaturas em pt-BR).

### 💻 2. Desenvolvedor (Dev)
* **Função**: Escrever código, criar arquivos, refatorar lógica de backend e frontend.
* **Regra de Ouro**: Seguir estritamente as especificações fornecidas pelo Orquestrador. Não criar variáveis, endpoints ou rotas que não constem na especificação original.

### 🔍 3. Revisor (Reviewer)
* **Função**: Garantir a conformidade estrutural, nomenclatura e identidade visual.
* **Lista de Verificação**:
  * Nome de arquivos e pastas sugestivos em **Português do Brasil**? (Sem `src`, `components`, `utils`).
  * Padrão visual oficial Ugarit implementado? (Azul Safira `#2563EB`, bordas retas `border-radius:0`, fonte Chakra Petch/Inter).
  * Sem dados confidenciais hardcoded (tokens, senhas no código)?

### 🧪 4. Testador (Tester)
* **Função**: Homologar e certificar o funcionamento da aplicação.
* **Ferramenta**: Executar compiladores (`tsc --noEmit`), linters de código e invocar obrigatoriamente o `/react-doctor` após qualquer edição em projetos React para garantir que o health score não regrediu.

### 📝 5. Escritor (Writer / Documentador)
* **Função**: Sincronizar o progresso de desenvolvimento com a memória diária e o mapa de projetos.
* **Responsabilidade**: Atualizar a nota de `estado-atual.md` e escrever o resumo da interação na nota diária correspondente.

---

## 🧠 Sincronização via Segundo Cérebro (Obsidian)

Para evitar silos e manter a consistência entre sessões, a comunicação de estado entre agentes ocorre por meio de arquivos compartilhados:

1. **Ficha do Agente** (`01_Kothar/agentes/{nome_agente}.md`): Define o prompt e escopo do agente.
2. **Quadro de Tarefas** (`task.md` na raiz de controle do projeto): Centraliza as tarefas ativas do sprint.
3. **Log de Estado** (`estado-atual.md` na documentação do projeto): A linha do tempo dinâmica de progresso técnico que os agentes leem ao assumir a tarefa.

---

## ⚙️ Fluxo de Execução Orquestrado

1. **Planejamento**: O *Orquestrador* cria a lista de tarefas no `task.md`.
2. **Designado**: O *Desenvolvedor* executa as tarefas programadas.
3. **Revisão**: O *Revisor* valida se os arquivos de código atendem às diretrizes de nomenclatura e identidade visual.
4. **Validação**: O *Testador* executa o linter, build de produção e `react-doctor`.
5. **Registro**: O *Escritor* atualiza o `estado-atual.md` e as notas diárias com o progresso verificado.

---

## Voltar
← [[catalogo-habilidades]]
