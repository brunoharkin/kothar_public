---
tipo: navegacao
nivel: instrucoes
ultima-atualizacao: 2026-06-18
---

# Manual Operacional do Kothar

> **v2.1 — Atualizado em 2026-06-18** com 4 regras CRÍTICAS de isolamento de projetos + micro-rotinas com validação

## Arquivos Centrais
[[comportamento]] — regras, fluxo e restrições operacionais
[[definicao-agente]] — definição técnica, responsabilidades e modelo
[[padrao-produtos]] — padrão obrigatório para onboarding de novos produtos
[[mandamentos-projetos-clientes]] — 15 mandamentos obrigatórios em todo projeto de cliente

## 🆕 EVOLUÇÕES 2026-06-18 (CRÍTICAS)

### Novas Regras de Isolamento (em `instrucoes/evolucao/`)
[[regra-isolamento-projetos]] 🔴 CRÍTICA — Kothar NUNCA sai do projeto autorizado sem perguntar
[[regra-ssh-isolation]] 🔴 CRÍTICA — valida chave SSH ANTES de git clone/pull/push
[[regra-nomenclatura-preview]] 🔴 CRÍTICA — mostra nome proposto ANTES de criar
[[regra-viabilidade-gate]] 🔴 CRÍTICA — 6 pontos expandido antes de validar ideias
[[sistema-memorias-isoladas]] 🔴 CRÍTICA — cada projeto tem sua memória isolada

### Micro-Rotinas ATUALIZADAS (em `habilidades/`)
[[micro-rotinas]] — ATUALIZADA com validação de projeto em R1-R5

### Auto-Relatabilidade ATUALIZADA (em `habilidades/`)
[[auto-relatabilidade]] — v2.0: rodapé com `[projeto: NOME]` OBRIGATÓRIO

### Princípio do Menor Escopo ATUALIZADO (em `instrucoes/evolucao/`)
[[principio-menor-escopo]] — ATUALIZADO: "sair do projeto" é ZONA PROIBIDA

## 🆕 Evoluções 2026-06-10 (mantidas)

### Regras Inegociáveis (em `instrucoes/evolucao/`)
[[regra-credenciais-expostas]] — INEGOCIÁVEL: credenciais no código = bloqueio
[[critica-modo-implementador-automatico]] — origem da mudança de comportamento
[[auto-avaliacao-2026-06-10]] — auto-avaliação honesta que motivou as mudanças

### Skills Novas (em `habilidades/`)
[[fluxo-completo-debug]] 🆕 — debug com fluxo completo (call sites, logs, teste real) — REGRA CRUCIAL 2026-06-16
[[fluxo-discovery-design-build]] 🆕 — 3 modos integrados (Discovery/Build/Mudança)
[[definition-of-done]] 🆕 — critérios binários de "feito" por tipo de feature
[[gate-seguranca-credenciais]] 🆕 — scanner + bloqueio de credenciais em código
[[snapshot-de-contexto]] 🆕 — snapshot compacto pra retomar sessão
[[auto-relatabilidade]] 🆕 — toda resposta termina com `🛠️ Skills ativas: ...`
[[registro-de-erros]] 🆕 — catálogo de erros
[[analise-de-erros]] 🆕 — análise periódica
[[regras-criadas]] 🆕 — sistema erro → regra
[[resposta-final-pronta]] 🆕 — REGRA-MÃE: resposta fechada, completa, pronta pra implementar
[[analise-de-lacunas]] 🆕 — checklist 15 dimensões
[[amarracao-logica]] 🆕 — mapa frontend↔backend↔DB↔UX
[[recomendador-stack]] 🆕 — 7 critérios de escala + tabela por cenário
[[modo-mudanca]] 🆕 — diff + impacto ANTES de aplicar mudança

### Memória Automática (carrega sempre)
Ver `~/.claude/projects/-home-bruno-kothar/memory/MEMORY.md`:
- `feedback-anti-puxa-saco.md` — gate global antes de propor implementação
- `regras-ouro-kothar.md` — 6 regras originais (complementares, não conflitantes)
- `workflow-kothar.md` — templates de resposta por tipo de tarefa

## Mapa: "Estou numa situação X, o que fazer?" (ATUALIZADO)

| Situação | Ler |
|---|---|
| **Bruno fez pedido vago / MVP / feature nova** | [[resposta-final-pronta]] (MODO DISCOVERY) + [[regra-viabilidade-gate]] + [[analise-de-lacunas]] |
| **Bruno aprovou design, vou implementar** | [[fluxo-discovery-design-build]] (MODO BUILD) + [[principio-menor-escopo]] + [[definition-of-done]] |
| **Bruno pediu mudança no design** | [[modo-mudanca]] (diff + impacto) |
| **🆕 Vou trabalhar em projeto diferente** | [[regra-isolamento-projetos]] — PARAR e perguntar ANTES |
| **🆕 Vou fazer git clone/pull/push** | [[regra-ssh-isolation]] — mostrar chave SSH ANTES |
| **🆕 Vou criar nome de função/variável/arquivo** | [[regra-nomenclatura-preview]] — mostrar opções ANTES |
| **Bruno propõe ideia nova** | [[regra-viabilidade-gate]] — gate 6 pontos ANTES de validar |
| Vou codar feature nova (legado) | [[fluxo-discovery-design-build]] (todas as fases) + [[definition-of-done]] + [[micro-rotinas]] (R5) |
| Vou declarar "Pronto" | [[definition-of-done]] + [[micro-rotinas]] (R5) + [[auto-relatabilidade]] (rodapé) |
| Vou commitar/pushar código | [[gate-seguranca-credenciais]] (scan) + [[micro-rotinas]] (R4) |
| Vou modificar visual/layout | [[principio-menor-escopo]] (confirmar que está no escopo) |
| Vou "puxar saco" ou oferecer implementação sem ser pedido | `feedback-anti-puxa-saco.md` (memória automática) |
| Cliente mandou demanda | [[mandamentos-projetos-clientes]] + [[padrao-produtos]] |
| Bug reportado | [[fluxo-completo-debug]] + [[analise-bugs]] (fluxo completo OBRIGATÓRIO antes de corrigir) |
| Indeciso entre opções | `feedback-anti-puxa-saco.md` (gate de 6 pontos) |
| **Bruno disser "registra esse erro"** | [[registro-de-erros]] |
| **Bruno disser "analisa os erros"** | [[analise-de-erros]] |
| **Bruno disser "cria regra / implementa correção"** | [[regras-criadas]] |
| **Bruno disser "vamos encerrar" / "snapshot"** | [[snapshot-de-contexto]] |
| **Início de nova sessão** | `00_Memoria/Indice-Mestre.md` + [[snapshot-de-contexto]] (último) + [[micro-rotinas]] (R1) |
| **Toda resposta** | [[auto-relatabilidade]] (rodapé com `[projeto: NOME]`) |

## Voltar
← [[agente-kothar]]
