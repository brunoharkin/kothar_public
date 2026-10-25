← [[specs]]

# Especificação do Produto: Disparo em Massa (Ugarit v2)

**Branch do Projeto**: `master`

**Criado**: 2026-05-25
**Atualizado**: 2026-06-15

**Status**: MVP em Ajustes Finais (Interno Ugarit Digital)

**Entrada**: Plataforma SaaS de disparo de mensagens via WhatsApp com funil de resposta automático conduzido por IA (GPT-4o-mini), sistema multi-usuário, controle de saldo/créditos (PIX Mercado Pago), geração de variações semânticas de mensagens, marketplace/vitrine de chips, aquecimento coletivo e gestão de grupos.


## Cenários de Usuário e Testes *(obrigatório)*

### Cenário de Usuário 1 - Disparo em Massa Controlado (Prioridade: P1)

Como operador de marketing do cliente, eu quero disparar 2.000+ mensagens do WhatsApp divididas entre múltiplos chips/números com atraso configurável, para alcançar clientes potenciais sem sofrer bloqueios automáticos da plataforma.

**Por que esta prioridade**: É a base do produto (o motor de disparo). Sem ele não há mensagens a responder ou analisar.

**Teste Independente**: Enviar uma lista de 50 contatos de teste e verificar se todas as mensagens são disparadas com sucesso respeitando o delay randômico entre 10 e 30 segundos, sem travar a aplicação.

**Cenários de Aceitação**:

1. **Dado** uma lista de contatos importada e a campanha iniciada, **Quando** o sistema envia a mensagem, **Então** o status do contato muda para `Enviada`.
2. **Dado** o processo de envio ativo, **Quando** o WhatsApp sinaliza que a mensagem foi visualizada, **Então** o status no banco de dados atualiza para `Lida`.

---

### Cenário de Usuário 2 - Conversação Pós-Disparo com Agente GPT (Prioridade: P1)

Como contratante do serviço, eu quero que, ao receber uma resposta à primeira mensagem (ex: "oi tudo bem"), um agente inteligente (GPT) responda automaticamente contornando objeções e apresentando a oferta na segunda e terceira mensagens de forma natural.

**Por que esta prioridade**: É o diferencial competitivo do produto para melhorar a taxa de conversão pós-disparo inicial.

**Teste Independente**: Simular uma resposta de um cliente teste e validar se o agenteGPT responde com o prompt configurado para o nicho (ex: Cardápio Digital ou Landing Page) dentro de 5 segundos.

**Cenários de Aceitação**:

1. **Dado** um contato que respondeu à mensagem de prospecção, **Quando** o agente processa a resposta, **Então** ele envia a segunda mensagem (explicando quem é e pedindo permissão para enviar o link/material).
2. **Dado** que o cliente permitiu ("pode mandar"), **Quando** o webhook de resposta é ativado, **Then** o agente envia a terceira mensagem contendo o material demonstrativo (ex: cardápio personalizado com o nome da empresa do cliente).

---

### Cenário de Usuário 3 - Painel Metrificado de Desempenho (Prioridade: P2)

Como administrador do sistema, eu quero visualizar um painel web que mostre as taxas de envio, abertura, resposta e conversão final (aceites do material) em tempo real, para otimizar os scripts e acompanhar a performance.

**Por que esta prioridade**: Permite identificar gargalos e campanhas que estão performando mal.

**Teste Independente**: Acessar o dashboard web e verificar se os números consolidados batem exatamente com os registros da tabela de mensagens no PostgreSQL.

**Cenários de Aceitação**:

1. **Dado** que disparos foram efetuados e respondidos, **Quando** eu abro o painel de métricas, **Então** visualizo as porcentagens de `Abertura` (Mensagens Lidas / Enviadas), `Resposta` (Respondidas / Enviadas) e `Conversão` (Permissões de Envio Concedidas / Enviadas).

---

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE permitir a criação de campanhas vinculando múltiplos números de WhatsApp (chips) para alternância e mitigação de bloqueio.
- **FR-002**: O sistema DEVE persistir todas as campanhas, contatos, mensagens enviadas, status de leitura e logs de chat no banco de dados **PostgreSQL**.
- **FR-003**: O sistema DEVE usar inteligência artificial (OpenAI API) para processar respostas recebidas dos contatos.
- **FR-004**: O agente GPT DEVE respeitar a árvore de conversação de 3 etapas (1. Prospecção -> 2. Filtro e Explicação -> 3. Envio da Demonstração/Material).
- **FR-005**: O sistema DEVE disponibilizar uma API REST para expor métricas agregadas das campanhas.
- **FR-006**: O painel web DEVE renderizar gráficos de performance e tabelas de conversão em tempo real.

### Entidades Chave

- **Campanha**: Representa a ação de disparo, contendo configurações de atraso, o prompt do agente GPT associado, o texto da primeira mensagem e o status geral.
- **Contato / Destinatário**: Representa a pessoa prospectada, com nome, telefone, empresa (se extraído), status atual do funil e histórico da conversa.
- **Mensagem Log**: Registro individual de cada texto enviado ou recebido para auditoria e cálculo de métricas.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: O painel web deve carregar os dados de métricas agregadas em menos de 1.5 segundos.
- **SC-002**: 95% das mensagens recebidas dos clientes devem ser respondidas pelo agente GPT em menos de 10 segundos.
- **SC-003**: A arquitetura deve suportar o controle e throttling de disparos a fim de enviar no mínimo 2.000 mensagens/dia sem travamento ou loops infinitos de envio.

## Premissas e Limitações

- O operador deve conectar a conta do WhatsApp Web escaneando o QR Code na interface da aplicação.
- A persistência no PostgreSQL será centralizada na mesma infraestrutura onde roda o servidor de backend.
- O WhatsApp Web oficial (via whatsapp-web.js) exige que a sessão da aba do navegador virtual (Puppeteer) esteja ativa para funcionar.
