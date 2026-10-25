---
name: kothar-rag
description: >-
  Skill do Kothar: Motor de memória RAG híbrida. Ativar quando precisar buscar contexto
  histórico, recuperar decisões passadas, indexar novo conhecimento, ou quando Bruno perguntar
  "como fizemos isso antes?" ou "qual foi a decisão sobre X?".
  Combina ChromaDB (mente do agente) com Obsidian/Cofre (documentação viva).
---

# Skill: Kothar RAG Engine — Memória Vetorial Híbrida

> **Princípio:** O Kothar retém contexto longo via busca semântica, não apenas palavras-chave. Contexto infinito sem perda de raciocínio.

## Divisão de Memória (O Híbrido)

### ChromaDB — A Mente do Agente
- **O que guarda:** Histórico de conversas, decisões técnicas, instintos aprovados, raciocínios efêmeros
- **Por que:** Tolera falhas, não polui o projeto do cliente com logs de agente
- **Dados locais:** `$KOTHAR_ROOT/.chroma-data/` (por padrão, `/home/bruno-harkin/kothar/.chroma-data`)
- **Endpoint:** `${CHROMA_URL:-http://127.0.0.1:8000}`
- **Estado do índice:** `$KOTHAR_RAG_STATE_FILE` ou `$KOTHAR_ROOT/.rag-index-state.json`
- **Pronto somente quando:** o endpoint responde em `/api/v2/heartbeat` e `indexed_chunks > 0`
- **Recuperação:** Top K=3 trechos mais relevantes por sessão

### Obsidian / Cofre — A Documentação Viva
- **O que guarda:** `visao.md`, `estado-atual.md`, DoD, diários de projeto, arquitetura, tickets
- **Por que:** Interface visual para Bruno revisar e governar
- **Local:** `~/Cofre/00_Memoria/`

---

## Pipeline RAG — Como Funciona

```
1. GATILHO → Fim do ciclo Ship OU R4 (Registrar Decisão)
2. INGESTÃO → Extrai nota/conversa → chunking 512 tokens → embedding local
3. ARMAZENAMENTO → ChromaDB local persistente, com estado do índice verificável
4. RECUPERAÇÃO (R1) → Busca semântica na intenção do usuário
5. INJEÇÃO → Top 3 chunks relevantes no contexto antes de responder
```

---

## Como Usar RAG na Prática

### Buscar contexto histórico
```
"Como fizemos autenticação multi-tenant da última vez?"
→ RAG recupera decisões passadas relevantes
→ Kothar responde com base no histórico real, não inventado
```

### Indexar novo conhecimento
```
Após decisão técnica importante:
→ Registrar em 00_Memoria/Decisoes/YYYY-MM-DD-decisao.md
→ RAG indexa automaticamente no próximo ciclo Ship
```

### Verificar estado do projeto
```
Sempre antes de modificar código:
1. Ler visao.md (o que o sistema deve ser)
2. Ler estado-atual.md (onde está hoje)
3. Comparar com objetivo do pedido atual
```

---

## Regras do Gate RAG

- Nunca considerar RAG ativo apenas pela existência do diretório de dados.
- A ativação usa `scripts/kothar-rag-start.sh` para iniciar o Chroma local quando o índice já existe.
- Se o serviço ou o índice estiver indisponível, declarar o estado explicitamente e não inventar contexto recuperado.

```
❌ NUNCA armazenar API Keys/senhas no banco vetorial
   → gate-seguranca limpa a string antes do embedding

✅ SEMPRE buscar no ChromaDB para "como Kothar fez algo antes"
✅ SEMPRE ler do Obsidian para "o que a empresa/cliente deseja"
✅ SEMPRE ler visao.md + estado-atual.md ANTES de codar
✅ SEMPRE atualizar estado-atual.md após Ship
```

---

## Estrutura de Memória

```
00_Memoria/
├── Diarias/
│   └── YYYY-MM/
│       └── YYYY-MM-DD.md     ← diário do dia (LER SOMENTE HOJE)
├── Decisoes/
│   └── YYYY-MM-DD-*.md       ← decisões técnicas importantes
├── Snapshots/
│   ├── handoff-ativo.md      ← checkpoint para retomada
│   └── checkpoints/
│       └── cp-[ts]-[slug].md ← histórico de checkpoints
└── Indice-Mestre.md           ← índice geral do cofre
```

---

*Kothar v4.0 — RAG Engine | Ugarit Digital*
