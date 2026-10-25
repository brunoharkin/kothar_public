---
name: catalogo-habilidades
description: >-
  Skill do Kothar: Catálogo de Habilidades do Kothar v2.1.3. Ativar quando necessário para execução da habilidade catalogo-habilidades.
---

# Catálogo de Habilidades do Kothar v2.1.3

> **Versão:** 2.1.3 (2026-06-28) — Handoff Automático de Contexto  
> **Total ativo:** 53 habilidades  
> **Deprecadas:** 6 (em `_deprecated/`)  

---

## 🆕 Novidades v2.0.0 (3 skills novas)
### Swarm e Inteligência
| Skill | Descrição |
|-------|-----------|
| [[rag-engine]] | Memória cognitiva via ChromaDB. |
| [[swarm-router]] | Orquestração contínua multi-agentes. |
| [[acao-preditiva]] | Discovery silencioso via cron. |

---

## 🆕 Novidades v1.4.0 (8 skills antigas)

### Core (orquestração)
| Skill | Descrição |
|-------|-----------|
| [[core/core-loop]] | Orquestrador central. Todo pedido passa aqui. |
| [[core/perception]] | 5 sensores (pwd, git, ssh, diário, modo). |
| [[core/reasoning]] | Como Kothar planeja antes de agir. |
| [[core/gates]] | 5 portões automáticos. |
| [[core/checkpoints]] | 6 CPs que pedem aprovação. |
| [[5-camadas-validacao-projeto]] | Torna impossível erro 009. |
| [[memorias-isoladas]] | Cada projeto tem sua pasta. |
| [[instinct-engine]] | Auto-aprendizado de tool calls. |

---

## ✅ Status Legend
- 🟢 **validada** = testada em produção
- 🟡 **parcial** = funciona, melhorar
- 🆕 **nova v1.4.0** = criada nesta versão
- 📦 **deprecada** = em `_deprecated/`

---

## 🧠 Memória e Contexto
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[memoria-obsidian]] | 🟢 | Gravar em vault Obsidian. |
| [[recuperacao-contexto]] | 🟢 | Buscar histórico. |
| [[gestao-notas-diarias]] | 🟢 | Diário do dia. |
| [[memorias-isoladas]] | 🆕 | Isolamento por projeto. |
| [[memory-nudge]] | 🆕 | 5 gatilhos de save. |
| [[memory-search]] | 🆕 | Busca em memórias. |
| [[memory-summarize]] | 🆕 | Sumarização compressiva. |
| [[fts5-search]] | 🆕 | Full-text em transcripts. |
| [[context-handoff-automatico]] | 🆕 | Corte da janela de contexto para evitar overflow (limitações de contexto). |

---

## 🛡️ Validação e Gates
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[core/gates]] | 🆕 | 5 portões automáticos. |
| [[core/checkpoints]] | 🆕 | 6 CPs (projeto, nomenclatura, commit, push, rm, feature). |
| [[5-camadas-validacao-projeto]] | 🆕 | Torna erro 009 impossível. |
| [[regra-isolamento-projetos]] | 🆕 | NUNCA sair do projeto. |
| [[regra-ssh-isolation]] | 🆕 | Chave SSH por projeto. |
| [[regra-nomenclatura-preview]] | 🆕 | Nome antes de criar. |
| [[regra-viabilidade-gate]] | 🆕 | 6 pontos obrigatórios. |
| [[gate-seguranca-credenciais]] | 🆕 | Scan automático. |
| [[command-allowlist]] | 🆕 | SAFE/CONFIRM/DANGEROUS. |
| [[project-sandbox]] | 🆕 | Isolamento de contexto. |
| [[principio-menor-escopo]] | 🟢 | Regra 3. |
| [[seguranca]] | 🟢 | Scanner. |
| [[analise-bugs]] | 🟢 | Scanner estático. |

---

## 🔧 Desenvolvimento
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[fluxo-discovery-design-build]] | 🟢 | 3 modos integrados. |
| [[definition-of-done]] | 🟢 | DoD binário. |
| [[amarracao-logica]] | 🟢 | Frontend↔backend↔DB↔UX. |
| [[recomendador-stack]] | 🟢 | 7 critérios. |
| [[modo-mudanca]] | 🟢 | Diff + impacto antes. |
| [[fluxo-completo-debug]] | 🟢 | Fluxo obrigatório. |
| [[frontend-ugarit-ui]] | 🟡 | Next.js + GSAP + shadcn + PT-BR. |
| [[inspecao-browser-devtools]] | 🟡 | Chrome DevTools MCP. |

---

## 🧪 Teste e Operacional
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[markitdown-extractor]] | 🆕 | PDF/DOCX/XLSX → MD. |
| [[hooks-system]] | 🆕 | before/after/on_error. |
| [[fault-tolerance]] | 🆕 | Retry + buffer reset. |
| [[timeout-manager]] | 🆕 | Multi-camada. |
| [[stall-detector]] | 🆕 | Sessões travadas. |
| [[structured-logging]] | 🆕 | JSONL + níveis. |
| [[execution-metrics]] | 🆕 | Métricas por tool. |
| [[trace-correlation]] | 🆕 | traceId. |

---

## 📈 Auto-Evolução
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[instinct-engine]] | 🆕 | Detecta padrões de tool calls. |
| [[skill-workshop]] | 🆕 | Proposta/aprovação. |
| [[skill-gating]] | 🆕 | Habilitar por projeto. |
| [[registro-de-erros]] | 🆕 | Catálogo. |
| [[analise-de-erros]] | 🆕 | Análise periódica. |
| [[regras-criadas]] | 🆕 | Erro → regra. |
| [[user-modeling]] | 🆕 | Preferências dialéticas. |

---

## 🧠 Memória Persistente
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[snapshot-de-contexto]] | 🟢 | Estado fim de sessão. |
| [[micro-rotinas]] | 🟢 | R1-R5. |
| [[auto-relatabilidade]] | 🟢 | Rodapé de skills. |
| [[resposta-final-pronta]] | 🟢 | Regra-mãe. |
| [[recuperacao-contexto]] | 🟢 | Buscar antes de decidir. |
| [[analise-de-lacunas]] | 🟢 | 15 dimensões. |

---

## ✍️ Conteúdo e Marketing
| Skill | Status | Descrição |
|-------|--------|-----------|
| [[copy-vendas]] | 🟡 | AIDA, PAS, PASTOR. |
| [[marketing-estrategia]] | 🟡 | Estrategista brutal. |
| [[acesso-youtube]] | 🟡 | Extrai transcrição. |
| [[pesquisa-web]] | 🟡 | Web search estruturado. |
| [[ouvinte-whatsapp]] | 🟡 | Áudio → texto. |
| [[contador-tokens]] | 🟡 | Métricas de sessão. |

---

## 📦 Deprecadas (em `_deprecated/`)
- `fluxo-gsd-desenvolvimento` → `fluxo-discovery-design-build`
- `especificacao-projetos` → `fluxo-discovery-design-build`
- `browser-kothar` → `inspecao-browser-devtools`
- `orquestracao-multi-agente` → Core Loop decide
- `descoberta-skills` → `npx skills find` (externo)
- `client-ops` → `Contextos/cliente.md`

---

## 🆕 v1.4.0 Resumo
- 8 skills novas (core + validação + instinto)
- 6 skills deprecadas (movidas para `_deprecated/`)
- Total ativo: **49 skills**
- Cobertura: governança, dev, debug, auto-aprendizado, conteúdo




---

## 🤖 Habilidades Auto-Criadas
| Skill | Descrição |
|---|---|
| [[auto-criadas/skill-aprendida-implementar-compliance-legal-n]] | Habilidade aprendida para: Implementar compliance legal no banco de dados. |
| [[auto-criadas/skill-aprendida-corrigir-meno-a-conta-gratui]] | Habilidade aprendida para: Corrigir menção a conta gratuita na landing page e erro de Invalid Hook Call com Radix Switch. |
