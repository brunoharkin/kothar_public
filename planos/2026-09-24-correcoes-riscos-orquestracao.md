# Plano — Correção dos riscos principais da orquestração

## Objetivo

Tornar o Kothar mais confiável e verificável, reduzindo falsos positivos de saúde,
divergências de memória/RAG, gates não bloqueantes e alegações de delegação que não
possam ser comprovadas.

## Escopo aprovado

1. Remover defaults de credenciais efetivos e tornar o health check honesto.
2. Consolidar caminhos canônicos do Cofre/RAG e corrigir indexação/preload.
3. Tornar scanner, pós-validação e auditoria estrutural bloqueantes quando houver
   violação real.
4. Criar uma camada verificável para registry/transições, resolver nomes de agentes
   e registrar delegações efetivas.
5. Executar validação final de sintaxe, testes, segurança e consistência.

## Fora do escopo

- Reescrever todos os agentes Python.
- Trocar banco de dados ou provedor de modelo.
- Alterar frontend.
- Criar infraestrutura externa de sandbox/worktree sem contrato operacional definido.
- Commit ou push automático.

## Ordem de implementação

### Fase 1 — Configuração e saúde

- centralizar configuração de caminhos;
- eliminar senhas/tokens padrão utilizáveis;
- separar configuração obrigatória de desenvolvimento;
- corrigir contagem de falhas do health check;
- retornar código diferente de zero em falhas críticas.

### Fase 2 — Memória e RAG

- definir um único caminho canônico do Cofre;
- alinhar `ContextEmbedder`, leitor de sessões, watcher e scripts;
- impedir indexação silenciosa em caminhos alternativos;
- registrar origem e estado da indexação;
- testar preload com Chroma indisponível e disponível.

### Fase 3 — Gates

- scanner aceitar todos os contratos de ferramenta de escrita;
- pós-validação exigir arquivo explícito;
- auditoria estrutural falhar em violações bloqueantes;
- distinguir aviso de bloqueio;
- manter logs sem dados sensíveis.

### Fase 4 — Orquestração

- criar consumidor único do registry e das transições;
- resolver aliases de agentes;
- validar que cada passo aponta para agente conhecido;
- registrar `delegation_requested`, `delegation_started` e
  `delegation_completed` somente quando ocorrerem;
- não declarar background/swarm se não houver executor real.

### Fase 5 — Validação

- compilação Python;
- testes existentes;
- testes focados nos novos contratos;
- scan de credenciais;
- health check;
- validação da configuração;
- revisão de diff e DoD.

## Riscos controlados

- credenciais previsíveis em defaults;
- falso positivo de sistema saudável;
- perda de contexto por caminhos divergentes;
- escrita insegura não bloqueada;
- routing/transições somente declarativos;
- métricas que alegam agentes não executados.

## Critérios binários de aceite

- [x] configuração sem segredo utilizável por default;
- [x] health check falha quando componente crítico está ausente;
- [x] memória/RAG usam caminho canônico único;
- [x] hooks bloqueiam violações reais;
- [x] blueprint não contém agente sem alias resolvível;
- [x] delegação é registrada apenas com evidência;
- [x] compilação passa;
- [x] scan dirigido bloqueia segredo literal;
- [x] suíte unitária/contratos passa (`21/21`);
- [x] suíte sem integração externa passa (`20/20`);
- [x] health check verde (`32/32`);
- [x] RAG indexado e persistido (`3095` chunks em `7` coleções);
- [ ] suíte de integração da API — bloqueada pelo socket Docker indisponível neste runtime.
