---
name: auto-aprendizado
description: >-
  Diretrizes e templates para o Kothar gerar suas próprias skills automaticamente
---

# Skill: Auto-aprendizado de Habilidades (Auto-Learning)

## Objetivo
Documentar e persistir novos conhecimentos, soluções de bugs específicos e preferências do usuário de forma automatizada no Obsidian, criando um "segundo cérebro" dinâmico para futuras sessões.

## Gatilho (Quando usar)
Ao final de qualquer tarefa complexa, resolução de bug crítico ou quando o usuário disser "aprenda isso", se não existir uma skill correspondente em `habilidades/`.

## Lógica de Criação
Antes de persistir, localizar e confirmar o destino canônico do Cofre/Obsidian no
projeto ativo. Não presumir que `01_Kothar/habilidades/auto-criadas/` existe: essa
estrutura legada não está presente no Cofre atual. Skills canônicas do Kothar ficam
em `.agents/skills/` e podem ser compartilhadas pelo Cofre via link.

Se não houver pasta de memória configurada e existente, incorporar um aprendizado
aprovado a uma skill existente ou apresentar a proposta ao usuário; não criar
automaticamente uma nova pasta/arquivo fora do projeto autorizado.

Quando o destino estiver confirmado e a criação tiver sido autorizada, crie um
arquivo `skill-aprendida-[slug].md` contendo:
- Frontmatter com `auto-aprendida: true`, data e projeto.
- Rationale e Contexto.
- O que deu certo e como fazer (código, fluxos, comandos).
- Indicadores de validação automatizados.
- Preferências identificadas do usuário.
- Evidências mínimas e sanitizadas; nunca copiar transcript bruto, credenciais ou dados pessoais.
