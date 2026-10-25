---
name: auto-relatabilidade
description: >-
  Registrar no fim de cada resposta final os agentes, habilidades, ferramentas e verificações
  efetivamente usados na interação atual, incluindo limitações e ausência de uso.
---

# Skill: Auto-Relatabilidade (v3.0)

> Atualizado em 17/10/2026: relatório factual por interação, sem inferir execução pela disponibilidade de uma habilidade ou agente.

<!-- kothar-delivery-contract:start -->
## Relatório obrigatório de cada entrega

No fim de cada resposta final, inclusive consultas e entregas bloqueadas, apresente uma lista curta com:
- **Projeto:** projeto desta interação; use "não identificado" se faltar evidência.
- **Agentes:** agente principal e subagentes realmente acionados nesta interação, responsabilidade e resultado; sem delegação, declare "sem subagentes". Separe indisponível, interrompido e concluído. Roster disponível não significa execução.
- **Habilidades:** nomes reais das skills lidas e aplicadas nesta interação e a finalidade de cada uma. Busca RAG, índice ou catálogo não comprovam aplicação. Identifique consultas sem aplicação; se nenhuma foi aplicada, declare "nenhuma aplicada". Não invente um mínimo nem omita habilidades usadas para caber em um limite fixo.
- **Ferramentas e verificações:** ferramentas efetivamente chamadas, testes/comandos relevantes e resultados, sem argumentos sensíveis. Se não houve execução, declare "não executadas".
- **Resolução e pendências:** problemas encontrados e efetivamente corrigidos nesta interação. Lacunas identificadas devem ser resolvidas diretamente na execução. Se houver pendência estritamente externa ou bloqueio do usuário, declare explicitamente; quando todas as pendências forem sanadas e verificadas, declare "nenhuma pendência residual". Não repita agentes/habilidades de interações anteriores como se tivessem sido usados agora.

Produção é o padrão: ao trabalhar com autenticação, dados, APIs ou implantação, selecionar as skills de segurança pertinentes, incluindo `kothar-seguranca` e `gate-producao` quando aplicáveis. Aplicação precisa de evidências; citar o nome não equivale a passar o gate. Sem limite de login, sessão server-side, autorização, proteção de dados ou controle de exposição exigidos, a entrega de produção fica bloqueada.

Cada subagente devolve seu registro factual no handoff; o principal consolida sem transformar plano, busca, simulação ou falha em execução aprovada. O relatório é rastreabilidade e não substitui controles de segurança, testes nem revisão independente. Não force delegação ou ferramentas só para preencher a lista. Regras de economia de contexto e retomada preservam este contrato e as skills obrigatórias da tarefa atual.
<!-- kothar-delivery-contract:end -->

## Fonte dos registros e formato

```text
Relatório desta interação — [projeto: nome]
- Agentes: principal — responsabilidade; subagentes — resultado, ou sem subagentes.
- Habilidades: nomes reais — finalidade, ou nenhuma aplicada.
- Ferramentas/verificações: chamadas realizadas — resultados, ou não executadas.
- Limitações/pendências: fatos não verificados e próximos passos.
```

Atualizações de progresso não precisam repetir o relatório. Na resposta final de uma pergunta simples, usar um registro proporcional; não executar ferramentas ou delegar apenas para preencher campos.

Registrar os itens conforme o trabalho acontece. Na entrega, confrontar o registro com as chamadas observadas desta interação. Separar habilidades consultadas das aplicadas, agentes disponíveis dos executados e teste local de validação em produção. Sem verificação, declarar a limitação.

O principal consolida os registros dos subagentes com autoria, responsabilidade, resultado e interrupções. Contribuição parcial continua parcial; falha de runtime não significa revisão concluída.

Listar todos os nomes realmente usados, sem mínimo obrigatório ou corte artificial de cinco habilidades. Não apresentar regras gerais como nomes de skills inexistentes.

## Sincronização

O bloco entre os marcadores acima é o contrato canônico. Atualizar e verificar os pontos de entrada e manifests dos subagentes com:

```bash
python3 scripts/sincronizar-relatorio-entrega.py --apply
python3 scripts/sincronizar-relatorio-entrega.py --check
```

O check detecta divergência de instruções, inclusive em manifest novo; não comprova execução de hooks ou aplicação de habilidades pelo runtime.

Na retomada, preservar este contrato e selecionar as habilidades obrigatórias da tarefa atual. Não repetir como atual um agente ou ferramenta usado em outra interação.

## Conferência antes da entrega

- Projeto corresponde ao trabalho atual?
- Cada agente foi realmente acionado, com resultado correto?
- Cada habilidade aplicada tem finalidade sustentada pelo trabalho?
- Ferramentas, comandos e testes foram executados e têm resultado conhecido?
- Falhas, pendências e limitações do runtime estão explícitas?
- O registro evita segredos, dados pessoais e argumentos sensíveis?
- A conclusão respeita os gates de segurança, independentemente do rodapé?

Se um item foi declarado incorretamente, corrigir o registro e a conclusão. Não apresentar busca RAG, contagem de arquivos, simulação ou checklist como prova de proteção executável.
