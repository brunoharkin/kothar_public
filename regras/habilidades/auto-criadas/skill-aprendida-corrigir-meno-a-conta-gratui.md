---
name: skill-aprendida-corrigir-meno-a-conta-gratui
description: Habilidade gerada automaticamente para resolver Corrigir menção a conta gratuita na landing page e erro de Invalid Hook Call com Radix Switch
version: 1.0
projeto: Orbytwin
auto-aprendida: true
---

# Habilidade Auto-Criada: Corrigir Menção A Conta Gratuita Na Landing Page E Erro De Invalid Hook Call Com Radix Switch

## Contexto e Problema
- **Pedido original:** Corrigir menção a conta gratuita na landing page e erro de Invalid Hook Call com Radix Switch
- **Projeto relacionado:** Orbytwin
- **Arquivos modificados:** frontend/src/pages/LandingPage.tsx

## O que deu certo (Como resolver)
Foi removido qualquer texto sugerindo teste ou conta gratuita da LandingPage.tsx, pois o Orbytwin não oferece modalidade gratuita. Também foi apagado o cache do Vite (rm -rf node_modules/.vite) para corrigir o erro 'Invalid hook call' no componente Switch do Radix UI, que ocorre quando o Vite se confunde com dependências injetadas via HMR.

## Indicadores de Validação
- [ ] O código modificado passa no `validador.sh`
- [ ] O código obteve score >= 90 no analisador `analise-codigo.py`
