# 🏛️ KOTHAR v4.0 — The Disciplined Multi-Agent AI Orchestrator

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-360%C2%B0%20Production%20Ready-blue?style=for-the-badge" alt="Architecture" />
  <img src="https://img.shields.io/badge/Orchestration-Multi--IDE%20Swarm-purple?style=for-the-badge" alt="Orchestration" />
  <img src="https://img.shields.io/badge/Security-Fail--Closed%20%26%20Zero--Leak-red?style=for-the-badge" alt="Security" />
  <img src="https://img.shields.io/badge/Memory-Hybrid%20RAG%20(ChromaDB)-success?style=for-the-badge" alt="RAG" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-yellow?style=for-the-badge" alt="License" />
</p>

---

## ⚡ O que é o Kothar?

O **Kothar** não é mais um assistente genérico de chat. Ele é um **Orquestrador Disciplinado de IA para Engenharia de Produção**, desenvolvido para transformar modelos de linguagem em verdadeiros engenheiros de software autônomos dentro da sua IDE.

Diferente de ferramentas que apenas concordam cegamente com o desenvolvedor ("vibe coding"), o Kothar opera sob a filosofia **Anti-Puxa-Saco**:
1. **Visão 360° Imediata**: Arquitetura completa de ponta a ponta (Frontend ↔ Backend ↔ Banco de Dados ↔ Segurança ↔ Produção).
2. **Mitigação Embutida**: Antecipa custos ocultos, vetores de falha e riscos antes de qualquer linha de código.
3. **Execução Autônoma de Ponta a Ponta**: Quando autorizado, implementa, roda linters, compila e valida testes sem parar para perguntas triviais.
4. **Gates e DoD Estritos**: Nenhuma entrega é declarada como concluída sem validação binária de testes, segurança e compilação limpa.

---

## 🚀 Instalação Rápida em 1 Clique (One-Click Bootstrap)

Você pode instalar o Kothar fornecendo o comando diretamente para o seu agente de IA ou rodando no terminal:

```bash
git clone https://github.com/agestrategia360-sudo/kothar.git ~/.kothar-core && cd ~/.kothar-core && chmod +x install.sh && ./install.sh
```

### O que o instalador faz automaticamente:
* ✅ Configura o ambiente isolado Python (`.venv`) e dependências do motor.
* ✅ Ativa e indexa o **RAG Semântico Híbrido** (ChromaDB local) com teste de fumaça funcional obrigatório.
* ✅ Executa a **Auditoria de Chaves de API**, alertando sobre ferramentas que necessitam de credenciais externas.
* ✅ Sincroniza nativamente os contratos de instrução, MCPs e Hooks com suas IDEs:
  - **VS Code / GitHub Copilot** (`.github/agents/`, `.vscode/mcp.json`)
  - **Claude Code** (`CLAUDE.md`, `.claude/`)
  - **Gemini CLI / Antigravity** (`GEMINI.md`)
  - **Cursor** (`.cursorrules`)
  - **Codex CLI** (`AGENTS.md`)

---

## 🧠 Core Loop & Portões de Segurança (Gates)

```
PEDIDO → SENTIR → PENSAR → VALIDAR → AGIR → APRENDER → RELATAR
                     ↓
             [6 CHECKPOINTS]
```

### 🚧 Os 5 Gates do Kothar (Validados Antes de Agir)
* **G1 (Isolamento de Projeto):** Garante que o agente nunca modifique arquivos fora da raiz do projeto autorizado.
* **G2 (Menor Escopo):** Define escopo positivo, escopo negativo e zonas proibidas antes de codificar.
* **G3 (Credenciais & Segredos):** Scanner estático obrigatório — zero API keys ou senhas expostas em código.
* **G4 (Postura Anti-Puxa-Saco):** Análise crítica de trade-offs, riscos e custos operacionais.
* **G5 (Padrões de Produção):** Rate limiting obrigatório, sessão server-side (zero tokens em localStorage), headers seguros (CSP, HSTS).

---

## 🔑 Capacidades e Chaves de API

O Kothar funciona com modelos locais e de nuvem. Para extrair a **capacidade máxima de raciocínio da suíte**, configure suas variáveis de ambiente no arquivo `.env` ou no seu shell:

| Variável | Provedor | Capacidade Habilitada |
| :--- | :--- | :--- |
| `ANTHROPIC_API_KEY` | Anthropic Claude | Raciocínio arquitetural profundo, Claude Code e reflexão |
| `GEMINI_API_KEY` | Google Gemini | Janelas massivas de contexto (1M+ tokens), multimodalidade |
| `OPENAI_API_KEY` | OpenAI | Embeddings semânticos avançados, Codex e fallback de geração |
| `HF_TOKEN` | Hugging Face | Download de pesos, embeddings neurais e pipelines open-source |

> 💡 **Nota sobre Fallback:** Se nenhuma chave for configurada, o Kothar continuará operando através dos seus runtimes locais e regras disciplinares, mas ferramentas que exigem chamadas externas operarão em modo degradado.

---

## 🏛️ Estrutura de Segundo Cérebro (Cofre Local)

O Kothar separa rigidamente o **motor de execução** (`~/.kothar-core`) da **memória de longo prazo** do usuário (`~/Cofre`):

* `~/Cofre/00_Memoria/Diarias/`: Diários de bordo e snapshots automáticos de contexto.
* `~/Cofre/00_Memoria/Decisoes/`: ADRs (Architecture Decision Records) rastreáveis.
* `~/Cofre/00_Memoria/Aprendizados/`: Catálogo de erros catalogados que foram promovidos a regras.
* `~/Cofre/Projetos/`: Documentação viva e visão geral dos projetos gerenciados.

---

## 🛠️ Como Iniciar uma Sessão

Em qualquer IDE configurada, basta digitar o comando de inicialização no chat do seu agente:

```text
/kothar
```

O Kothar executará os 5 sensores de percepção, validará o RAG, identificará o operador ativo e responderá pronto para orquestrar:

```text
Kothar v4.0 ativo. Operador: Carlos. Sensores verificados. RAG Operacional. Pronto para orquestrar.
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Consulte o guia de contribuição e leia as diretrizes de codificação em `regras/` e as skills em `.agents/skills/`.

---

<p align="center">
  <b>Kothar v4.0 — Disciplina, Rigor e Engenharia de Produção para IA.</b>
</p>
