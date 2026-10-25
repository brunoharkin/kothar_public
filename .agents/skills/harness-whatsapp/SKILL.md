---
name: harness-whatsapp
description: Projetar, implementar e revisar a harness de agentes conversacionais e WhatsApp com processamento assíncrono, persistência, ferramentas e avaliação. Aplicar em webhooks, filas, workers, memória e envio; não em tarefas apenas de copy.
---

# Harness para agentes e WhatsApp

Ative quando a tarefa alterar a operação de um agente conversacional: canal, ingresso, execução, ferramentas, contexto, memória ou envio. Leia o fluxo existente e identifique contratos antes de modificar. Esta habilidade não certifica produção nem substitui `kothar-seguranca` ou `gate-producao` quando aplicáveis.

## Arquitetura e invariantes

- Separe adaptador do provedor, ingresso, inbox/fila persistente, workers, execução cognitiva, ferramentas autorizadas, memória, outbox e observabilidade. Framework e broker são escolhas por carga medida; Postgres pode atender sem adicionar broker. Não prometa capacidade com benchmark de terceiros.
- No webhook: validar assinatura conforme SDK/provedor e URL pública efetiva, limites de tamanho/tipo e esquema. Persistir evento e chave única por tenant/provedor/evento em transação antes do ACK de aceitação. Falha de persistência exige resposta compatível com retry do provedor; não confirmar perda. Desafios de verificação têm contrato próprio.
- Não bloquear ACK com debounce, mídia ou LLM. Agrupar texto no worker por conversa com janela e espera máxima limitadas; preservar eventos originais. Limites distribuídos por origem, tenant e conversa, backpressure e orçamento de tokens/custo impedem loops entre bots.
- Worker deve reclamar trabalho atomicamente com lease, recuperação e fencing/versionamento. Preserve ordem por conversa e paralelismo entre conversas. `SKIP LOCKED` pode ajudar na disputa de jobs, mas não assegura FIFO por conversa nem exactly-once.
- Deduplique também efeitos de ferramentas. Retry transitório com backoff/jitter, limite de tentativas e idade; erro permanente vai para estado terminal com revisão. Nunca repetir pagamento/agendamento apenas porque houve timeout.
- Gere intenção de envio em outbox persistente, com identificador estável e transação com o estado da execução. Timeout de envio pode ter efeito ocorrido: reconciliar com provedor antes de repetir. Não prometer exactly-once externo sem suporte comprovado.
- Modele separadamente: recebido, persistido, processando, resposta preparada, envio pendente, aceito pelo provedor, enviado, entregue, lido, falhou e envio incerto. Callback autenticado pode ser duplicado ou fora de ordem; não confundir aceitação com entrega.
- Particione contexto, checkpoints, memória, ferramentas e cache por tenant/conta/canal/conversa. Telefone ou hash sozinho não autoriza acesso. RAM pode ser cache descartável, nunca fonte exclusiva de estado durável, sessão, dedupe ou limite distribuído.
- Separe histórico completo com retenção, contexto recente limitado, resumo versionado e fatos duráveis com proveniência/correção/exclusão. Recuperação RAG respeita ACL; conteúdo recebido é dado não confiável, nunca política ou autorização de ferramenta.
- Mídia: download com origem permitida e proteção SSRF, limites reais de bytes/duração/tipo, timeout e processamento isolado. Transcrição é conteúdo não confiável. Formato sem suporte deve receber resposta explícita.
- Ferramentas têm allowlist, esquema, autorização server-side e confirmação proporcional ao efeito. Handoff humano pausa automação com estado persistido e retomada explícita. Não vazar segredos/PII em traces, prompts, logs ou dados de treino.
- Registrar correlação sem payload sensível: fila/idade, latência por etapa, retries, duplicatas, erros, custo e resultado de negócio. Alertas e runbooks precisam permitir intervenção.

## Evidência antes de entregar

Mapear entrada → estado → transformação → ferramenta → envio → confirmação. Para cada fronteira registrar contrato, dono do estado, falha e recuperação. Exercitar duplicata, crash após persistir, disputa entre workers, lease expirado, callback fora de ordem, timeout após envio, tenant adversário, mídia maliciosa, loop de bots e indisponibilidade do banco. Testes de schema/dataset não comprovam esses comportamentos.

Usar `datasets/harness-whatsapp-avaliacao-v1.jsonl` como rubrica de cenários; manter separado de treino. Avaliar respostas reais do modelo e testes de integração antes de afirmar melhoria. Regras e exemplos não alteram pesos; fine-tuning exige pipeline, licença/base definidos e avaliação comparativa. Não importar conversas reais ou traces brutos automaticamente.

## Origem e limites

Síntese original da aula fornecida por Bruno em 17/10/2026 e da trilha pública https://rhawk.pro/trilha/harness-assincrona-para-whatsapp . Inbox/outbox, isolamento, reconciliação e critérios adversariais são adaptações de engenharia para o Kothar; não são alegações sobre a implementação privada do professor. Não copiar conteúdo restrito nem executar testes contra o site de referência.
