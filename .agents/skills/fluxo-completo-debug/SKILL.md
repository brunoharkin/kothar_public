---
name: fluxo-completo-debug
description: >-
  Skill do Kothar: Skill: Debug com Fluxo Completo. Ativar quando necessário para execução da habilidade fluxo-completo-debug.
---

# Skill: Debug com Fluxo Completo

## Quando usar
- Antes de corrigir QUALQUER bug de cliente
- Quando o sintoma aparece em um lugar mas a causa pode estar em outro
- Quando há funções compartilhadas

## Passo a passo

### 1. RECONHECER O SINTOMA
- Capturar print
- Capturar logs do frontend (console + network)
- Capturar stack trace (se houver)
- Reproduzir o bug (passos exatos)

### 2. MAPEAR O FLUXO COMPLETO
```
Usuário clica em [X]
  -> chama função Y (arquivo:linha)
  -> Y consulta banco? (qual tabela? qual query?)
  -> Y chama API externa? (qual endpoint?)
  -> Y modifica estado? (qual?)
  -> Y retorna? (o que?)
  -> UI re-renderiza? (em quê?)
```

### 3. IDENTIFICAR CALL SITES
```bash
grep -rn "nomeDaFuncao" --include="*.ts" --include="*.tsx"
```
Listar TODOS os lugares que usam a função. **Cada um é um risco.**

### 4. IDENTIFICAR IMPACTO COLATERAL
- A função tem testes? (ver `__tests__/`)
- Mudar nomenclatura quebra imports?
- Mudar retorno quebra quem consome?
- Mudar tipo do parâmetro quebra quem chama?

### 5. CAUSA RAIZ COM EVIDÊNCIA
Não "acho que é X". **Mostre:**
- O log que prova
- O arquivo:linha exato
- A query que falha
- O teste que reproduz

### 6. CORREÇÃO MÍNIMA
- Mudar o MÍNIMO possível
- Se for rename -> usar alias (não deletar nome antigo)
- Se for lógica -> branch nova (não refatorar existente)
- Preservar interface pública

### 7. TESTE E VALIDAÇÃO AUTOMÁTICA
1. **Validação Sintática:** Executar `~/.kothar/scripts/validador.sh` para atestar a integridade do código.
2. **Pontuação de Qualidade:** Executar `python3 ~/.kothar/scripts/analise-codigo.py [arquivo_alterado]` e garantir score >= 90.
3. **Build local:** Compilar localmente para checar regressões de empacotamento.
4. **Abrir app / Reproduzir:** Executar passos exatos do bug original no navegador.
5. **Verificar Console/Network:** Sem novos erros de console e sem retornos de rede do tipo 4xx/5xx.
6. **Testar happy path e edge cases.**

### 8. DOOR DE DOOR
- [ ] Sintoma desapareceu?
- [ ] Nenhum log novo de erro ou aviso?
- [ ] Nenhuma feature vizinha quebrou?
- [ ] Validador sintático (`validador.sh`) passou com sucesso?
- [ ] Score de qualidade do analisador de código é >= 90?
- [ ] Testes automatizados integrados passam?

## Anti-padrões
- "Provavelmente é X" — busque evidência
- Mexer em 3 arquivos quando 1 resolve
- "Já corrigi, depois testamos" — teste É a correção
- Confiar em print sem ler logs
- Refatorar durante bugfix (risco alto)

## Ferramentas úteis
- `grep -rn` para call sites
- `git log -p` para entender mudanças recentes
- `console.log` estratégico (com cleanup depois)
- Browser DevTools (Network + Console tabs)
- Lighthouse (se for performance)
