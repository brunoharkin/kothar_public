# Instruções do Kothar

Este repositório usa o Kothar v4.0 como camada de orquestração.

- Responder em português do Brasil.
- Respeitar o fluxo Entender → Pesquisar → Planejar → Implementar → Testar → Salvar.
- **POSTURA 360° E EXECUÇÃO DE PONTA A PONTA (ANTI-PUXA-SACO EVOLUÍDO):** Não apenas apontar pontos fracos ou limitações. Ao elaborar o plano, entregar o 360° da solução técnica (frontend ↔ backend ↔ banco ↔ segurança ↔ produção). Uma vez aprovado o plano, executar toda a implementação, rodar testes e linters, e realizar a revisão de segurança dupla (credenciais + `gate-producao`). Se encontrar falhas ou lacunas durante a execução, corrigir imediatamente no próprio ciclo sem transferir pendências resolvíveis para o usuário.
- Reutilizar `.agents/skills/`.
- Não inserir chaves de API em código, logs ou configurações versionadas.
- Declarar limitações do runtime em vez de simular compatibilidade.
- **PRODUÇÃO COMO PADRÃO:** Todo código gerado destina-se a produção. Rate limiting é obrigatório em login/rotas públicas. Sessão SEMPRE server-side (Redis/Postgres); zero localStorage/sessionStorage para auth/tokens. Headers de segurança (HSTS, CSP, X-Frame) obrigatórios. Zero console.log com dados sensíveis. Validar com `gate-producao`.
- **WAR ROOM AUDITIVO OBRIGATÓRIO (DEBATE POR VOZ):** Todo e qualquer plano de voo, feature nova ou refatoração estrutural DEVE ser despachado imediatamente para o War Room (`http://localhost:3344` / `scripts/kothar_war_room.py`). O plano entra em debate auditivo com o Bruno via voz (Alex pt-BR) e só é implementado após validação e aprovação formal.
- **CONTROLE ESTRITO DE JANELA & MEMÓRIA EXTERNA:** Proibido carregar a memória inteira do projeto no contexto da sessão. Use o Grafo (Neo4j / AST) e o RAG (ChromaDB) para carregar estritamente o nó da sub-tarefa ativa (Top-3 / máx 1.500 tokens). A criação de aplicações deve ser particionada em sub-etapas; ao finalizar o plano ou uma sub-etapa, gere o `handoff-ativo.md` (máx 50 linhas) e reinicie a sessão. Nunca estoure a janela de 5h/rate-limits da API.

Integrações nativas:

- Copilot/VS Code: `.github/agents/`, `.github/hooks/`, `.vscode/mcp.json`.
- Claude Code: `.claude/` e `CLAUDE.md`.
- Gemini CLI: `GEMINI.md`.
- Codex e runtimes compatíveis: `AGENTS.md` e `.agents/skills/`.

## 🛑 PROTOCOLO ANTI-AMNÉSIA E LEITURA PROFUNDA (GRAPH-FIRST)
❌ **PROIBIDO leitura rasa.** O agente NUNCA pode reescrever um bloco ou arquivo inteiro sem antes mapear todas as funções internas.
❌ **PROIBIDO dump massivo:** Mapear dependências via Grafo (Neo4j) ou AST pontual, sem ler dezenas de arquivos inteiros na conversa.
❌ **Sincronia Obrigatória:** Se alterar um nome no Backend, é OBRIGATÓRIO rastrear a dependência no Frontend e Banco de Dados e alterar em sincronia.
❌ NUNCA apagar lógicas internas ao atualizar blocos.
✅ Utilize a skill `kothar-anti-amnesia` para garantir o tracking cirúrgico de dependências (Graph/Neo4j e AST).

## 🏛️ COFRE ÚNICO & SEGUNDO CÉREBRO (REGRA ABSOLUTA)
O **Kothar** é o agente/orquestrador (`~/kothar/`). O **Cofre** é o segundo cérebro oficial (`/home/bruno-harkin/Cofre/`).
❌ **PROIBIDO criar documentos no Kothar:** NUNCA criar arquivos markdown de documentação, planos, pesquisas, notas ou especificações dentro de `~/kothar/`.
✅ **TUDO É REGISTRADO DIRETAMENTE NO COFRE (`/home/bruno-harkin/Cofre/`):**
- `00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md` (Diários de bordo)
- `00_Memoria/Decisoes/` (Decisões de Arquitetura ADR)
- `00_Memoria/Aprendizados/` (Erros catalogados e regras)
- `00_Memoria/Snapshots/handoff-ativo.md` (Checkpoints/Handoffs)
- `00_Memoria/Empresa/` (Inteligência, mercado, pesquisas)
- `00_Memoria/Historico/` (Histórico de releases e specs)
- `Empresa/` (Estrutura canônica Ugarit: Identidade, Funil, Vendas, Delivery, Produtos)
- `Projetos/{nome-do-projeto}/` (Documentação viva dos projetos)
- `planos/` (Planos de ação e roadmaps)
- `aprendizado/` (Guias e boas práticas técnicas)
- `auditorias/` e `pentest/` (Auditorias de segurança)
- `clientes/` (Clientes e propostas)
- `regras/` e `checklist/` (Checklists operacionais)
- `kothar/docs/` e `kothar/specs/` (Documentação técnica do Kothar)
- `treinamento/` (Datasets e acervo de capacitação)

<!-- kothar-delivery-contract:start -->
## Relatório obrigatório de cada entrega

No fim de cada resposta final, inclusive consultas e entregas bloqueadas, apresente uma lista curta com:
- **Projeto:** projeto desta interação; use "não identificado" se faltar evidência.
- **Agentes:** agente principal e subagentes realmente acionados nesta interação, responsabilidade e resultado; sem delegação, declare "sem subagentes". Separe indisponível, interrompido e concluído. Roster disponível não significa execução.
- **Habilidades:** nomes reais das skills lidas e aplicadas nesta interação e a finalidade de cada uma. Busca RAG, índice ou catálogo não comprovam aplicação. Identifique consultas sem aplicação; se nenhuma foi aplicada, declare "nenhuma aplicada". Não invente um mínimo nem omita habilidades usadas para caber em um limite fixo.
- **Ferramentas e verificações:** ferramentas efetivamente chamadas, testes/comandos relevantes e resultados, sem argumentos sensíveis. Se não houve execução, declare "não executadas".
- **Resolução e pendências:** problemas encontrados e efetivamente corrigidos nesta interação. Lacunas identificadas devem ser resolvidas diretamente na execução. Se houver pendência estritamente externa ou bloqueio do usuário, declare explicitamente; quando todas as pendências forem sanadas e verificadas, declare "nenhuma pendência residual". Não repita agentes/habilidades de interações anteriores como se tivessem sido usados agora.

Produção é o padrão: ao trabalhar com autenticação, dados, APIs ou implantação, selecionar as skills de segurança pertinentes, incluindo `kothar-seguranca` e `gate-producao` quando aplicáveis. Aplicação precisa de evidências; citar o nome não equivale a passar o gate. Sem limite de login, sessão server-side, autorização, proteção de dados ou controle de exposição exigidos, a entrega de produção fica bloqueada.

Cada subagente devolve seu registro factual no handoff; o principal consolida sem transformar plano, busca, simulação ou falha em execução aprovada. O relatório é rastreabilidade e não substitui controles de segurança, testes nem revisão independente. Não force delegação ou ferramentas só para preencher a lista. Regras de economia de contexto e retomada preservam este contrato e as skills obrigatórias da tarefa atual.
<!-- kothar-delivery-contract:end -->

<!-- kothar-harness-routing:start -->
Ao desenvolver ou revisar agentes conversacionais e integrações WhatsApp (webhooks, filas, workers, ferramentas, memória ou envio), ler e aplicar `.agents/skills/harness-whatsapp/SKILL.md`. Registrar evidências e lacunas; a presença da skill não comprova execução nem aprovação de produção.
<!-- kothar-harness-routing:end -->

<!-- kothar-security-policy:start -->
## Política canônica de segurança

Antes de implementar, revisar ou liberar código que toque autenticação, entrada de usuário, persistência, APIs externas, logs, agentes conversacionais ou implantação:

1. leia `configuracao/kothar-security-policy.json`;
2. aplique todas as skills declaradas para a superfície afetada;
3. trate ambiente de produção e falha fechada como padrão;
4. bloqueie a entrega até haver evidência dos requisitos de release aplicáveis.

Versão esperada: `2026-10-17.1`. SHA-256 esperado: `03556482c7fd06a11f0f31d3e7ae691912eaae47e4d6d7c941ec2f61e07e88a6`.
<!-- kothar-security-policy:end -->
