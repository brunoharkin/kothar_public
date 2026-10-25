---
name: especificacao-projetos
description: Especificar features e projetos com rigor antes de implementar, usando spec-driven development para evitar alucinação
version: 1.0.0
ferramenta: spec-kit (github/spec-kit)
---

# Habilidade: Especificação de Projetos

## Por que existe

O Kothar trabalha com 5+ clientes e 12+ aplicações internas. Sem especificação formal, o risco de implementar a coisa errada, esquecer contexto ou contradizer decisões anteriores é alto. Esta habilidade garante que **nada é implementado sem estar especificado e validado**.

## Fluxo padrão

```
Demanda → Spec → Clarificação → Checklist → Plano → Tarefas → Análise → Implementação
```

### 1. `/speckit-constitution`
Define os princípios e arquitetura do projeto. Executar **uma vez por projeto**.
Salvo em: `specs/<projeto>/constitution.md`

### 2. `/speckit-specify <descrição>`
Transforma a demanda em especificação estruturada com:
- Cenários de usuário
- Requisitos funcionais
- Critérios de sucesso
- Entidades-chave
- Ambiguidades identificadas (máx. 3)

Salvo em: `specs/<projeto>/<feature>/spec.md`

### 3. `/speckit-clarify`
Resolve as ambiguidades antes de planejar. Evita retrabalho.
Executar **antes** do `/speckit-plan`.

### 4. `/speckit-checklist`
Valida qualidade da spec: completude, clareza, consistência.
Executar **após** o `/speckit-specify`.

### 5. `/speckit-plan`
Gera plano técnico de implementação a partir da spec validada.
Salvo em: `specs/<projeto>/<feature>/plan.md`

### 6. `/speckit-tasks`
Deriva lista de tarefas executáveis do plano.
Salvo em: `specs/<projeto>/<feature>/tasks.md`

### 7. `/speckit-analyze`
Verifica consistência entre spec, plano e tarefas.
Executar **antes** de implementar.

### 8. `/speckit-implement`
Implementação guiada pela spec aprovada.

## Estrutura de pastas

```
Cofre/01_Kothar/specs/
├── clientes/
│   └── <nome-cliente>/
│       ├── constitution.md
│       └── <feature>/
│           ├── spec.md
│           ├── plan.md
│           └── tasks.md
└── internos/
    └── <nome-app>/
        ├── constitution.md
        └── <feature>/
```

## Regra

Nenhuma feature é implementada sem spec aprovada. Se vier uma demanda pelo WhatsApp ou diretamente, o primeiro passo é sempre `/speckit-specify`.

## Repositório de Specs
→ [[specs]] — índice de todas as specs de clientes e projetos internos

## Voltar
← [[catalogo-habilidades]]
