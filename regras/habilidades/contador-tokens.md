---
name: contador-tokens
versao: 1.4.0
data: 2026-06-19
projeto: kothar
tipo: habilidade
status: validada
descricao: Contabiliza tokens consumidos por sessão + custo estimado
---

# 📊 CONTADOR DE TOKENS v1.4.0

> **Função:** Mede tokens consumidos por sessão, custo estimado e comparação entre sessões.

## Comando

```bash
# Resumo de hoje
kothar metrics tokens

# Por projeto (últimos 7 dias)
kothar metrics tokens --by-project

# Por dia
kothar metrics tokens --daily

# Exportar CSV
kothar metrics tokens --export=csv
```

## Integração com `~/.kothar/metrics/`

Esta skill lê dados de:
- `~/.kothar/metrics/sessions/YYYY-MM-DD.jsonl` — métricas por sessão
- `~/.kothar/logs/session-YYYY-MM-DD.log` — tool calls

## Formato de Saída

```
╔════════════════════════════════════════════╗
║ TOKENS — Sessão 2026-06-19                  ║
╠════════════════════════════════════════════╣
║ Input tokens:      12,450                   ║
║ Output tokens:      8,320                   ║
║ Cache reads:        3,100                   ║
║ Total tokens:      23,870                   ║
║                                            ║
║ Custo estimado (Sonnet 4.6):                ║
║   Input:   $0.037                          ║
║   Output:  $0.249                          ║
║   Total:   $0.286                          ║
║                                            ║
║ Tool calls: 47                              ║
║ Skills ativas: 8                            ║
║ Tempo total: 2h 14min                       ║
╚════════════════════════════════════════════╝
```

## Métricas por Projeto (últimos 7 dias)

| Projeto | Sessões | Tokens | Custo |
|---------|---------|--------|-------|
| ratoflix | 3 | 89,420 | $1.20 |
| bioleads | 2 | 45,100 | $0.65 |
| kothar | 5 | 142,800 | $1.95 |
| disparo-em-massa | 1 | 32,000 | $0.45 |

## Pricing (referência 2026)

| Modelo | Input ($/1M) | Output ($/1M) |
|--------|--------------|----------------|
| Claude Opus 4.8 | $15 | $75 |
| Claude Sonnet 4.6 | $3 | $15 |
| Claude Haiku 4.5 | $0.80 | $4 |

## Limites Recomendados

| Métrica | Limite por sessão |
|---------|-------------------|
| Tokens totais | < 150k (Gatilho de Handoff Automático) |
| Custo | < $5 |
| Tool calls | < 100 |
| Tempo | < 4h |

**Se ultrapassar:** considerar fechar sessão, criar snapshot, abrir nova.

## Como Implementar

A skill é carregada quando:
- Bruno fala "quanto custou essa sessão?"
- Bruno fala "tokens de hoje"
- Comando direto `kothar metrics tokens`

## Arquivos

- Skill: `habilidades/contador-tokens.md` (este)
- Dados: `~/.kothar/metrics/sessions/`
- Comando: `~/.local/bin/kothar metrics tokens` (a implementar em D11.2)
