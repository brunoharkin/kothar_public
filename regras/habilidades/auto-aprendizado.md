---
name: auto-aprendizado
description: Diretrizes e templates para o Kothar gerar suas próprias skills automaticamente
version: 1.0
projeto: kothar
tipo: habilidade
---

# Skill: Auto-aprendizado de Habilidades (Auto-Learning)

## Objetivo
Documentar e persistir novos conhecimentos, soluções de bugs específicos e preferências do usuário de forma automatizada no Obsidian, criando um "segundo cérebro" dinâmico para futuras sessões.

## Gatilho (Quando usar)
Ao final de qualquer tarefa complexa, resolução de bug crítico ou quando o usuário disser "aprenda isso", se não existir uma skill correspondente em `habilidades/`.

## Lógica de Criação
Crie um arquivo na pasta `01_Kothar/habilidades/auto-criadas/skill-aprendida-[slug].md` contendo:
- Frontmatter com `auto-aprendida: true`, data e projeto.
- Rationale e Contexto.
- O que deu certo e como fazer (código, fluxos, comandos).
- Indicadores de validação automatizados.
- Preferências identificadas do usuário.
