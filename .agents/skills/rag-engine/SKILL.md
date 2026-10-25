---
name: rag-engine
description: >-
  Motor de Busca Semântica Avançada (RAG) combinando ChromaDB para memórias de agente e Obsidian para documentação de projeto/cliente.
---

# Skill: RAG Engine (Memória Vetorial Híbrida)

> **Princípio:** O Kothar retém o contexto longo e profundo usando Busca Semântica e não apenas correspondência de palavras-chave. Ele delega o registro de histórico flexível da IA para um banco vetorial local (ChromaDB), enquanto mantém o cofre em Markdown (Obsidian) estritamente para documentações e registros do cliente.

---

## 🧠 Divisão de Memória (O Híbrido)

### 1. ChromaDB (A Mente do Agente)
- **O que armazena:** Transcrições de conversas, embeddings de decisões antigas, instintos aprovados, histórico de uso de ferramentas e nudges comportamentais.
- **Por que:** Tolerância a falhas. O agente não suja a pasta do cliente com logs de erro intermináveis ou raciocínios efêmeros. O vetor capta o contexto exato (ex: "Qual foi aquele erro de deploy na Vercel há 3 meses?").
- **Local:** `~/.kothar/vector-db/`

### 2. Obsidian / Cofre (A Documentação Viva)
- **O que armazena:** Documentação do projeto, arquitetura (`visao.md`, `estado-atual.md`), DoD, diários de projeto para o cliente, tickets e notas de negócio.
- **Por que:** É a interface visual onde Bruno (o usuário) lê e interfere. O Obsidian atua como o "contrato de registro e governança" com o cliente/empresa.

---

## ⚙️ Fluxo de Funcionamento (Pipeline RAG)

1. **Gatilho de Indexação:** 
   Sempre que o Kothar finalizar o ciclo de *Ship* ou rodar a rotina *R4 (Registrar Decisão)*, o hook em background aciona o `embedder.py`.
2. **Ingestão Vetorial:**
   O script extrai a nota (ou conversa) gerada, chunkifica o texto em blocos de 512 tokens e gera embeddings locais usando modelo open-source (ex: all-MiniLM-L6-v2), armazenando no ChromaDB.
3. **Recuperação (Retrieval):**
   No início de toda sessão (Micro-Rotina R1 Expandida), o Kothar roda uma busca no ChromaDB injetando a intenção do usuário:
   - "Quais padrões seguimos da última vez que fizemos autenticação multi-tenant?"
   O RAG retorna os 3 blocos mais relevantes (Top K=3) diretamente para o contexto do Kothar antes de ele responder.

---

## 📋 Regras de Uso (Gate RAG)

- ❌ **NUNCA** armazenar segredos (API Keys, senhas) no banco vetorial. O gate `gate-seguranca-credenciais` DEVE limpar a string antes do embedding.
- ✅ **SEMPRE** preferir buscar no ChromaDB para dúvidas sobre "como o Kothar fez algo antes".
- ✅ **SEMPRE** ler do Obsidian para descobrir "o que a empresa/cliente deseja".

---

*Skill atualizada para v2.0.0 — Bruno Harkin / Kothar (Ecossistema Multi-Nó)*
