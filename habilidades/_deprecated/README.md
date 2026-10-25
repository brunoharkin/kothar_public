---
name: skills-deprecadas
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: meta
descricao: Registro de skills descontinuadas e seus substitutos
---

# 📦 SKILLS DEPRECADAS v1.4.0

> **Função:** Documentar skills removidas e indicar substitutos.

## Skills Movidas para `_deprecated/`

| Skill | Motivo | Substituta |
|---|---|---|
| `fluxo-gsd-desenvolvimento` | Fluxo antigo, fraco | `fluxo-discovery-design-build` |
| `especificacao-projetos` | Substituída por Discovery | `fluxo-discovery-design-build` |
| `browser-kothar` | Browser nativo do Claude | `inspecao-browser-devtools` |
| `orquestracao-multi-agente` | Sub-agentes só em tarefas grandes | Core Loop decide contexto |
| `descoberta-skills` | Já existe `npx skills find` | comando externo |
| `client-ops` | Reorganizado como contexto | `Contextos/cliente.md` |

## Política de Deprecação

Skills são movidas para `_deprecated/` quando:
1. Substituídas por versão melhor
2. Funcionalidade virou nativa (ex: browser)
3. Sub-agentes absorveram (orquestração)
4. Comando externo disponível

**Não deletar** — manter em `_deprecated/` por 90 dias para referência.

## Promoção Reversa

Se Bruno precisar de uma skill deprecada:
```bash
# Trazer de volta
mv 01_Kothar/habilidades/_deprecated/[skill].md 01_Kothar/habilidades/
```

## Auditoria Futura

A cada release:
- [ ] Listar skills não usadas em 90 dias
- [ ] Propor deprecação se Bruno concordar
- [ ] Mover para `_deprecated/`
- [ ] Atualizar `catalogo-habilidades.md`
