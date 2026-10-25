# Constituição do Projeto: Disparo em Massa

## Princípios Fundamentais

### I. Organização e Limpeza ("Arrumar a Casa")
Antes de qualquer nova funcionalidade complexa, o código deve ser limpo e estruturado. Não trabalhamos em cima de bagunça. Cada módulo deve ter uma responsabilidade clara, separando rotas Express, lógica do bot WhatsApp (whatsapp-web.js) e lógica de inteligência artificial (agente GPT).

### II. Segurança e Privacidade do Cliente
Todas as chaves de API, credenciais do WhatsApp e dados sensíveis devem ser isolados em variáveis de ambiente (`.env`). Nunca expor credenciais em arquivos de código ou logs.

### III. Persistência Robusta com PostgreSQL
Toda a persistência de campanhas, contatos, métricas de abertura, taxas de resposta e logs de mensagens deve ser feita em banco de dados PostgreSQL. Abandonar o uso de arquivos locais ou JSON voláteis para dados críticos do projeto.

### IV. Mensuração e Transparência (Painel Metrificado)
Todas as ações de disparo e interações pós-disparo devem gerar métricas rastreáveis. A taxa de conversão, taxa de abertura (leitura) e taxa de resposta precisam ser expostas através de endpoints limpos e consumidas por um painel transparente para o cliente.

## Restrições e Requisitos de Qualidade

- **Escalabilidade**: O sistema de envio deve prever throttling e controle de tempo entre envios (delay dinâmico/randômico) para evitar bloqueios ao atingir a escala de milhares de disparos (meta inicial: 2.000 disparos).
- **Tratamento de Erros**: Falhas na conexão com o WhatsApp, limite de taxa (rate limiting) da API da OpenAI ou erros de banco de dados devem ser tratados graciosamente, registrando o status de falha de disparo sem derrubar o servidor.

## Governança

- Qualquer alteração arquitetural deve ser refletida na documentação técnica no Obsidian.
- O fluxo de desenvolvimento sempre seguirá a especificação prévia do Spec-Kit.

**Versão**: 1.0.0 | **Ratificado**: 2026-05-25 | **Última Alteração**: 2026-05-25
