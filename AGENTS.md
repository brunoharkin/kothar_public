# Instruções do Kothar

Este repositório usa o Kothar v4.0 como camada de orquestração.

- Responder em português do Brasil.
- Respeitar o fluxo Entender → Pesquisar → Planejar → Implementar → Testar → Salvar.
- Reutilizar `.agents/skills/`.
- Não inserir chaves de API em código, logs ou configurações versionadas.
- Declarar limitações do runtime em vez de simular compatibilidade.

Integrações nativas:

- Copilot/VS Code: `.github/agents/`, `.github/hooks/`, `.vscode/mcp.json`.
- Claude Code: `.claude/` e `CLAUDE.md`.
- Gemini CLI: `GEMINI.md`.
- Codex e runtimes compatíveis: `AGENTS.md` e `.agents/skills/`.

## 🛑 PROTOCOLO ANTI-AMNÉSIA E LEITURA PROFUNDA
❌ **PROIBIDO leitura rasa.** O agente NUNCA pode reescrever um bloco ou arquivo inteiro sem antes mapear todas as funções internas.
❌ **Sincronia Obrigatória:** Se alterar um nome no Backend, é OBRIGATÓRIO rastrear a dependência no Frontend e Banco de Dados e alterar em sincronia.
❌ NUNCA apagar lógicas internas ao atualizar blocos.
✅ Utilize a skill `kothar-anti-amnesia` para garantir o tracking de dependências (Graph/Neo4j e AST).
