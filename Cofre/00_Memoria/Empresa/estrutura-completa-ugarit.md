# Estrutura Completa da Softhouse — Ugarit Digital

**Documento de referência operacional (versão refatorada)** — arquitetura do ecossistema de produtos (Orbytwin, CRM Sophia, ChronoDesk), os 8 departamentos + Agente Monitor, a camada de identidade única, o Mapa Matador, os handoffs entre agentes, a cultura de auto-evolução, e dados de mercado (julho/2026). Fonte única — qualquer coisa que divergir daqui em outro lugar deve ser atualizada, não o contrário.

> Hermes é seu agente pessoal e não participa do fluxo comercial/CRM.

---

## Por Que Ugarit Digital — A Origem do Nome

Ugarit foi uma cidade portuária de mais de 3.000 anos atrás, na costa da Síria — um dos grandes polos cosmopolitas do Mediterrâneo Antigo, ponto de encontro entre Egito, impérios da Mesopotâmia, o mundo Hitita e Chipre. Sua marca na história: foi lá que nasceu um dos primeiros alfabetos verdadeiros — 30 sinais simples substituindo sistemas de escrita com centenas de símbolos, tornando a escrita acessível a muito mais gente, e lançando as bases dos alfabetos fenício, grego, latino, árabe e hebraico. Os escribas de Ugarit dominavam vários idiomas e sistemas de escrita ao mesmo tempo, usados na correspondência comercial com os povos vizinhos — e o acervo de tábuas de argila encontrado lá preservou tudo: comércio, diplomacia, lei e mitologia (o Ciclo de Baal), com um rigor que virou memória permanente da civilização.

Três fios conectam isso à Ugarit Digital: **(1) o alfabeto** — pegar uma tecnologia complexa (escrita cuneiforme / IA generativa) e simplificar pra algo que qualquer um pode usar sem virar especialista; **(2) a cidade-ponte** — conectar sistemas diferentes numa identidade só, como Ugarit conectava povos e escritas; **(3) o arquivo que sobreviveu 3.000 anos** — memória permanente e cultura de auto-evolução como princípio, não acidente.

**Resposta curta (conversa casual, ~20 segundos):**
*"Ugarit foi uma cidade antiga que deu ao mundo um dos primeiros alfabetos — pegou uma escrita complexa de centenas de símbolos e reduziu pra 30 sinais que qualquer um podia aprender. A gente faz a mesma coisa com IA: pega uma tecnologia complexa demais pra maioria construir sozinha com segurança, e simplifica pro dono de negócio usar sem precisar virar especialista. Daí o nome."*

**Resposta longa (pitch, site, conteúdo institucional):**
*"Ugarit foi uma cidade portuária de mais de 3.000 anos atrás, na costa da Síria — um dos grandes centros cosmopolitas do Mediterrâneo Antigo, ponto de encontro entre Egito, impérios da Mesopotâmia e do mundo Hitita, e Chipre. O que a torna especial não é só isso: foi lá que nasceu um dos primeiros alfabetos verdadeiros da história — 30 sinais simples substituindo sistemas de escrita com centenas de símbolos, tornando o conhecimento acessível a muito mais gente. Chamamos a empresa de Ugarit Digital porque é exatamente isso que fazemos: pegamos a complexidade real de construir e manter agentes de IA com segurança — que hoje só grandes empresas com time técnico dominam — e simplificamos pra qualquer negócio usar, sem precisar virar especialista pra isso."*

---

## Índice

1. Diagnóstico Rápido (1.1 Roster Completo de Agentes)
2. Panorama de Mercado
3. Posicionamento e ICP (3.1 Por Que Não Fazer Sozinho · 3.2 Modelo de Custo)
4. Mapa do Funil — P1-P5 ↔ E1-E13
5. O Ecossistema de Produtos — Orbytwin, CRM Sophia e ChronoDesk
6. Estrutura Organizacional — Os 8 Departamentos + Agente Monitor
7. Motor de Conteúdo → Lead (7.1 Segmentação de Remarketing)
8. Camada de Identidade Única e Memória Permanente
9. Automação "Mapa Matador" — Inteligência Pré-Reunião
10. Handoffs Entre Agentes — De Quem Pra Quem
11. Cultura de Auto-Evolução
12. Recorrência vs. Projetos Concluídos
13. KPIs — Visão Executiva
14. Stack de Ferramentas
15. Roadmap de Implementação
16. Pontos em Aberto

---

## 1. Diagnóstico Rápido

Você já fez a maior parte do trabalho de design — inclusive a parte mais difícil: como as ferramentas se conectam sem duplicar dado. O que faltava era consolidar tudo num documento sem contradição, com cada agente tendo identidade clara (nome, função, departamento, etapa do funil), cada handoff documentado, e o time humano real refletido — não um fundador solo fazendo tudo.

### 1.1 Time Humano

| Pessoa | Função |
|---|---|
| **Você** | Visão de produto, prioridade, reunião de vendas quando necessário |
| **Jonas** | Desenvolvimento — braço técnico que constrói o que está no escopo assinado |
| **Freelancer de tráfego** | Vendas/tráfego pago, apoio comercial |

O escopo definido na reunião e anexado ao contrato é a especificação objetiva — quem desenvolve (você, Jonas, ou outro freelancer que entrar depois) executa o que está ali, não decide o que construir na hora. Isso elimina ambiguidade de execução mesmo com mais de uma pessoa no código.

### 1.2 Roster Completo de Agentes

Cada agente com contato direto (lead ou cliente) ganhou nome próprio. Agentes 100% de bastidor mantêm nome mesmo sem falar com ninguém de fora — facilita referência interna e deixa claro quem faz o quê.

| Nome | Função | Departamento | Etapa do Funil |
|---|---|---|---|
| **Marina** | Reconhece o lead, cria o registro de entrada, cuida de palavra-chave e remarketing | Aquisição & Marketing | E1-E3 |
| **Fernando** | Qualifica (DOR→ESTRUTURA→VERBA→URGÊNCIA), aplica score e tier | Qualificação (SDR) | E1-E4 |
| **Rafael** | Monta o dossiê pré-reunião (Mapa Matador) — Instagram, site, Google, pixel de tráfego | Vendas (apoio) | E4 (pré-reunião) |
| **Orbytwin** | Gera link de reunião, transcreve, exibe dossiê no teleprompter, define status pós-reunião e sincroniza com o funil | Vendas (apoio) | E4 |
| **Nauta** | Publica, analisa e ajusta campanha de tráfego pago | Aquisição & Marketing | Alimenta o topo (pré-E1) |
| **Beatriz** | Monitora saúde do cliente, alerta, coleta feedback | Sucesso do Cliente | E11-E13 |
| **Zaya** | Orquestra o ChronoDesk inteiro — financeiro, projetos, agenda, comunicação, e as conexões com CRM Sophia e Orbytwin | Financeiro & Operações (transversal) | Pós-contrato (E6+) |
| **Otávio** (Agente Monitor) | Observa as métricas de todos os departamentos, sinaliza desvio | Transversal | Todas |

Mapa Matador, Rafael e Orbytwin **não fazem** venda nem discutem preço — só preparam e registram. Você e o freelancer conduzem reunião; Jonas (e você) desenvolvem dentro do escopo assinado — os agentes cobrem o resto.

---

## 2. Panorama de Mercado

- O mercado global de **agentes de IA autônomos** saiu de US$ 5-8 bilhões em 2024/2025 pra uma projeção de US$ 47-52 bilhões até 2030 — crescimento anual composto de ~45% (MarketsAndMarkets).
- No Brasil, **75% dos líderes empresariais** esperam ter agentes de IA operando com autonomia em processos críticos até o final de 2026.
- Gartner/IDC projetam **~40% das aplicações empresariais** incorporando agentes de IA até o fim de 2026, contra menos de 5% em 2025.
- Investimento em IA no Brasil deve superar **US$ 2,4 bilhões em 2026**; automação inteligente no país deve movimentar **R$ 12,4 bilhões**.
- ROI médio de projetos de automação com IA: **257% em três anos** (Forrester).
- Em micro-SaaS, a tendência é **verticalização** — exatamente o que vocês fazem. Só **~5% das PMEs no Brasil** usam algum SaaS hoje.
- WhatsApp: **+170 milhões de usuários ativos/mês no Brasil**, 95% das mensagens lidas em até 10 minutos.

### 2.1 Dados Reais de Mercado & Busca (Validados via AIsa / Google Brasil)

Aferição direta via DataForSEO/AIsa mapeando os cohorts ativos da Ugarit:
- **Advocacia (Alto Custo de Tráfego)**: Escritórios jurídicos no Brasil pagam lances agressivos de Google Ads — `advogado trabalhista` tem CPC médio de **$4.08 USD (~R$ 23,00)** com 60.500 buscas/mês, e termos como `advogados criminais online` chegam a **$7.99 USD (~R$ 45,00/clique)**. Perder um lead no WhatsApp por demora de atendimento significa queimar dezenas de reais por clique sem retorno.
- **Clínicas de Estética (Demanda Reprimida & Software Legado)**: O ecossistema clínico é dominado por ERPs de gestão de agenda (ex: `clinica nas nuvens` com 40.500 buscas/mês), mas o gargalo operacional crítico é a secretária física sem capacidade de qualificar e confirmar consultas em tempo hábil.
- **Agentes B2B & Softhouse**: Termos transacionais como `pipeline de vendas` (1.300 buscas/mês, KD 10, CPC $5.13 USD) possuem concorrência orgânica baixa no Brasil ($KD \le 15$), abrindo espaço para autoridade da Ugarit como softhouse especializada em agentes de IA.

> ⚠️ A Meta muda a cobrança da API do WhatsApp Business em duas etapas — **1º de agosto/2026** (token do Meta Business Agent) e **1º de outubro/2026** (toda mensagem de serviço dentro da janela de 24h passa a ser cobrada, hoje gratuita). Mapeie volume de mensagens/mês por cliente antes de outubro.

---

## 3. Posicionamento e ICP

### 3.0 Estratégia de Nicho em Cohort

Crescimento não é aleatório nem um cliente de cada vez — é por **cohort de nicho**, com critério de saída antes de abrir o próximo:

1. **Escolhe um cohort de nichos com fácil acesso agora** — hoje: advocacia + clínica de estética, trabalhados em paralelo, não em sequência
2. **Piso de viabilidade:** ~R$ 20 mil/mês em receita recorrente somando os clientes daquele nicho — na prática, ~5 clientes
3. **Ao bater o piso, ~3 meses de foco total no cohort** — analisando dado real, ajustando o fluxo, iterando o que quebra e o que converte
4. **O fluxo que funciona se replica; a comunicação não.** O padrão de funil validado (etapas, gatilhos, o que pergunta, onde qualifica) se repete entre clientes do mesmo nicho — tom de voz, dados da empresa e contexto são sempre personalizados por cliente
5. **Só depois de padrão validado + case pronto, abre o nicho pro público** — acesso ao CRM Sophia liberado via palavra-chave pra quem for daquele nicho (Seção 7)
6. **Próximo nicho continua a escala, não recomeça do zero** — prioriza nicho que aproveita o que já está pronto e aprende um padrão novo em cima da base existente

**Ainda em aberto:** o critério exato de "case bom o suficiente pra abrir o nicho" (tempo mínimo rodando, métrica de resultado, disposição do cliente em virar prova pública) e o critério formal de escolha do próximo nicho — ver Seção 16.

| Critério | Definição |
|---|---|
| Segmento | Empresas físicas e online — cohort atual: advocacia e clínica de estética. Prova social já validada: padaria, farmácia, e-commerce |
| Faturamento do cliente | De abaixo de R$ 20 mil (só com ROI claro) até R$ 100 mil+/mês (prioridade máxima). Zona ideal: R$ 50-100 mil+/mês |
| Ticket mínimo | R$ 10 mil |
| Pré-requisito de venda | Diagnóstico do Fernando + dossiê do Rafael validando ROI antes de qualquer proposta |
| Prova social | Padaria, farmácia, e-commerce, fórum com gamificação, rede social da comunidade |

**Princípio central:** *"Não vendemos esperança, vendemos soluções."* Nenhuma proposta sai sem diagnóstico validado.

### 3.1 Por Que Não Fazer Sozinho — Argumento de Posicionamento

**Não basta construir:** um estudo do MIT (The GenAI Divide, 2025) mostra que ~95% das organizações não observam impacto mensurável no resultado financeiro com seus projetos de IA generativa — só 5% extraem valor real. A causa mais comum: tentar automatizar uma operação que a própria empresa nunca conseguiu descrever com clareza. A Deloitte aponta fragmentação de ferramentas como principal causa de falha de automação em PMEs. Mesmo Andrej Karpathy (cofundador da OpenAI) descreve os agentes de hoje como ainda cognitivamente limitados sem estrutura e supervisão por trás.

**Segurança — o risco real de fazer em casa:** a empresa média registra 223 incidentes de violação de política de dados ligados a IA generativa por mês. Mais da metade dos colaboradores de empresas brasileiras já colou dado corporativo numa IA generativa sem autorização. Incidente com "shadow AI" como fator contribuinte custa, em média, US$ 670 mil a mais que um vazamento típico.

**Custo — a conta que ninguém orça:** gasto real de token em produção costuma ficar 5-10x acima do que o piloto indicava. Agente mal construído já gerou US$ 437 de prejuízo puro rodando em loop a noite toda. Roteamento inteligente entre modelos reduz gasto em 30-70%.

### 3.2 Seu Modelo de Custo — Diferencial Formalizado

- **Ecossistema Ugarit (padrão):** cliente usa a infraestrutura de modelos própria de vocês — sem custo de API de terceiro repassado.
- **Traga suas credenciais:** cliente com contrato próprio (OpenAI, Anthropic, Google etc.) pluga as próprias chaves.

**Frase de posicionamento:** *"Não vendemos só a construção. Vendemos a estrutura que aguenta escala com segurança — com a opção de rodar no nosso ecossistema ou no seu, com suas próprias chaves. De qualquer forma, você não paga pela mesma IA duas vezes."*

---

## 4. Mapa do Funil — P1-P5 ↔ E1-E13

### 4.1 O Cross-Walk

| Macro | Bloco | Etapas |
|---|---|---|
| **P1 — Prospecção** | PROSPECÇÃO | E1, E2, E3 |
| **P2 — Reunião Qualificada** | PROSPECÇÃO | E4 |
| **P3 — Contrato** | VENDAS | E5, E6 |
| **P4 — Desenvolvimento** | DESENVOLVIMENTO | E7, E8, E9, E10 |
| **P5 — Concluído** | PÓS-VENDA | E11, E12, E13 |

O bloco PROSPECÇÃO é o único que se divide em dois marcos macro (P1 e P2) — E1/E2/E3 ficam em P1, só E4 vira P2.

### 4.2 Divergências Entre Documentação e Painel ao Vivo

| Etapa | Documentação | Painel ao vivo | Risco |
|---|---|---|---|
| E1 | Entrada | Em Triagem | Baixo |
| E9 | Entregue | Pronto p/ Entrega | **Alto** — ver 4.3 |
| P2 | Reunião Qualificada | Qualificação | Médio |
| P5 | Concluído | Entregue | Médio |

### 4.3 Quando a Garantia (E10) Começa a Contar

Trave: *"sai de E9 quando o cliente confirma recebimento, não quando o time termina de construir."*

> **Quando alguém "vira lead":** no exato momento em que toca qualquer um dos 4 canais de entrada (form do site, WhatsApp, DM/ADM do Instagram, comentário em vídeo — orgânico ou ads) e Marina cria o registro no CRM Sophia. Antes disso é só um espectador anônimo; depois disso, tem User ID e entra na Seção 8 (memória permanente) — mesmo que nunca converse com ninguém.

### 4.4 Critérios de Entrada/Saída — Versão Consolidada

| E | Etapa | Critério de ENTRADA | Critério de SAÍDA |
|---|---|---|---|
| E1 | Em Triagem | Lead capturado — Marina cria o registro no CRM Sophia (Seção 5.3) | Palavra-chave de intenção (Fluxo SDR) → Fernando inicia DOR→ESTRUTURA→VERBA→URGÊNCIA **·** Palavra-chave de curiosidade (Fluxo Material) → recebe conteúdo e vai direto pra **E3/Aquecimento**, sem passar por Fernando ainda |
| E2 | Desqualificado | Fora do ICP mesmo após tentativa de qualificação | Estado permanente |
| E3 | Sem Interação (= "Aquecimento") | Três portas de entrada: **(1)** score < 40 depois de falar com Fernando, **(2)** parou de responder Fernando no meio da qualificação, **(3)** recebeu só material (Fluxo Material) e nunca chegou a falar com Fernando | Reengajou e responde → Fernando (re)avalia score → E4 se qualificar |
| E4 | Reunião | Fernando qualifica (score ≥ 40) → Orbytwin agenda automaticamente (Seção 5.2) | Status definido por você no Orbytwin: **Aprovado** → E5, **Não fechou** → volta pra E3 |
| E5 | Proposta Enviada | Status "Aprovado" no Orbytwin | Proposta aceita → E6 (Ganho) **ou** recusada → **Perdido** (motivo registrado, alimenta Seção 11) |
| E6 | Contrato Assinado | Proposta aceita, 20% pago | Kickoff → Zaya cria o projeto no ChronoDesk |
| E7 | Em Execução | Kickoff realizado | Build pronto para teste interno |
| E8 | Em Testes | Build em homologação com o cliente | Cliente valida funcionamento |
| E9 | Pronto p/ Entrega | Testes aprovados | Cliente confirma recebimento |
| E10 | Em Garantia | Entrega confirmada + pagamento total | 30 dias sem chamado crítico |
| E11 | Cliente Mensal | Contrato recorrente ativo | Churn ou upsell (Seção 12) |
| E12 | Cliente Único | Projeto fechado sem recorrência | Gatilho de reativação (Seção 12) |
| E13 | Entrega Concluída | Garantia encerrada sem pendência | Vira case (Seção 12) |

---

## 5. O Ecossistema de Produtos — Orbytwin, CRM Sophia e ChronoDesk e LinkDaBio

### 5.0 O Que É Vendido, De Fato

Isso corrige uma leitura errada de rodadas anteriores: **as ferramentas não são 4 produtos com 4 motivos de compra.** O que é vendido é **um serviço** — construir e operar um agente de IA com funil mensurado do primeiro clique até a conversão. As ferramentas são **vias de acesso** a esse serviço, cada uma com um papel diferente, não itens de catálogo separados:

- **CRM Sophia não é vendido.** É a infraestrutura onde o serviço roda — não existe "funil mensurado desde o primeiro clique" sem ele, então ele vem **embutido no plano** de quem contrata a criação de um agente. Painel próprio/dedicado é exceção negociada à parte, não o padrão.
- **Orbytwin é aberto ao público**, sem venda nenhuma — grava, transcreve e centraliza reunião pra qualquer um, autoatendimento.
- **ChronoDesk é convite** — produto à parte, vendido por assinatura mensal/anual pra outro desenvolvedor/agência que também constrói produto pra terceiros.
- **LinkDaBio não passa por funil nenhum** — ninguém tem reunião pra contratar link na bio. Detalhe completo em 5.5.

As próprias ferramentas nasceram de dor interna — "em vez de contratar ferramenta de terceiro, construímos a nossa" — e isso é o case que sustenta o conteúdo (Seção 7.2), não o produto anunciado.

### 5.1 Princípio: Organismos Independentes, Sincronizados Quando Conectados

Cada ferramenta é completa e autossuficiente, com banco de dados próprio e isolado — funciona sozinha, sem depender de nenhuma outra. Quando duas ou mais são conectadas pelo mesmo cliente, elas passam a se comunicar por API e sincronizar os dados que se sobrepõem — mesmo funil, mesma agenda, mesmos contatos — sem duplicar nem divergir. Na sua definição: **cada um funciona como um organismo único** — sozinho ou conectado.

**Progressão de conexão, na prática:**
- Cliente usa só o **Orbytwin** → grava, transcreve, agenda reunião com sua própria agenda isolada
- Cliente contrata o serviço principal → o **CRM Sophia** vem junto, embutido — as agendas se sincronizam, a reunião criada em um aparece idêntica no outro
- Cliente adiciona o **ChronoDesk** (caso seja dev/agência) → os três se conectam — funil, WhatsApp, geração de reunião e contatos passam a ser um dado só, mesmo cada ferramenta mantendo sua própria base isolada por trás

### 5.2 Orbytwin — Reunião de Ponta a Ponta

**Cadeia de função, todas as etapas automáticas:**
1. Fernando qualifica o lead (score ≥ 40) → Orbytwin entra sozinho: gera o link da reunião (Google Calendar/Meet), agenda na agenda sincronizada e devolve o link pro lead — sem toque manual
2. Rafael monta o dossiê (Mapa Matador, Seção 9) e envia pro Orbytwin
3. Na hora da reunião, o **teleprompter do Orbytwin mostra um bloco de notas com o dossiê completo** — o que Fernando coletou no WhatsApp + o que Rafael encontrou na varredura pública — visível pra você durante a própria ligação, sem abrir outro documento
4. Ao final, **você define o status da reunião dentro do próprio Orbytwin**: **Aprovado** (dispara criação da proposta, move o lead pra E5 — Proposta Enviada) ou **Não fechou** (motivo obrigatório, lead volta pra nutrição/aquecimento em E3) — a etapa do lead no CRM Sophia muda automaticamente a partir desse status. Contrato (E6) só acontece depois, quando a proposta em si é aceita — dois portões, não um só.

Isso fecha o loop: qualificação → dossiê → reunião com contexto completo na tela → decisão → funil atualizado, tudo sem passo manual entre as etapas.

**Fora do funil de vendas:** Orbytwin também é usado por qualquer pessoa de fora, sem qualificação nenhuma — só pra gravar/transcrever/centralizar reunião própria. Esse uso não passa por Fernando nem gera lead — é a única ferramenta genuamente autoatendimento e aberta desde o primeiro acesso.

### 5.3 CRM Sophia — A Infraestrutura Onde o Serviço Roda

Todo lead entra **sempre** pelo CRM Sophia — cai na etapa "Lead de Entrada" (E1). Marina cria o registro assim que o lead aparece em qualquer canal, e Fernando assume a qualificação. CRM Sophia é o dono do funil por etapa individual, do WhatsApp/Instagram e da análise de tráfego pago (Nauta) — **mas isso é entrega do serviço contratado, não um produto que o cliente compra separadamente.** O acesso ao CRM por parte de terceiros (público que ainda não é cliente) é liberado só por nicho já validado, via palavra-chave (Seção 7.2) — nunca aberto de forma genérica.

### 5.4 ChronoDesk — Dois Usos Diferentes

**Uso interno (pós-contrato do serviço principal):** nenhum lead entra no ChronoDesk antes do contrato assinado. A partir de E6, Zaya cria o contrato, armazena, e só então cria o projeto usando o escopo anexado.

**Uso externo (produto próprio, por convite):** ChronoDesk também é vendido como SaaS independente pra outro desenvolvedor/agência que constrói produto pra terceiros — "o banco de dados onde a pessoa vê todos os departamentos da empresa dela, métricas, contratos, notas fiscais, gestão completa". Fluxo: pessoa deixa o dado → entra na fila de espera → um agente qualifica esse lead → gera o convite → pessoa paga mensalidade ou anuidade. *(Preço ainda não definido — ver Seção 16.)*

**O que é manual dentro do ChronoDesk (uso interno):**
- Criação do contrato em si
- Registro de saída/entrada avulsa — toda vez que você paga ou recebe algo fora do padrão, você (ou uma foto do recibo pra Zaya, Seção 6.3) lança na hora

**O que já é automático:**
- Custos recorrentes mensais — configurado uma vez, repete sozinho
- Gasto com tráfego pago — puxado direto da API do CRM Sophia (dado do Nauta), sem lançamento manual
- Receita de contrato/nota fiscal — Zaya já tem o dado assim que o contrato é criado

**Departamentos com métrica automática:** a página nativa de Departamentos do ChronoDesk usa o funil sincronizado (CRM Sophia) como base pra métrica. Se o departamento já existe, a métrica atualiza sozinha; se não existe ainda, Zaya cria o departamento automaticamente, sempre usando a estrutura do funil como referência.

**Por que a extração completa de dado importa tanto:** garante que qualquer análise feita em cima desse dado (Zaya, Rafael, Otávio) seja precisa. Dado incompleto na entrada vira decisão errada na saída, em qualquer ponto do ecossistema.

> **Ponto de atenção de segurança:** se ChronoDesk vira SaaS pra outras agências, o dado de cada cliente-dev (e dos clientes DELES) precisa ficar isolado entre si e da base interna de vocês — vazamento aqui vaza dado de concorrente-cliente, não só de vocês. Confirmar que o isolamento por conta (Row Level Security, já mencionado na doc técnica original) cobre esse cenário multi-tenant antes de abrir convites.

### 5.5 LinkDaBio — Sem Funil, Sem Reunião

Diferente de tudo acima, LinkDaBio não passa por nenhuma etapa do funil comercial — é autoatendimento puro, com dois canais de descoberta:

1. **Vitrine própria:** usado no Instagram da própria Ugarit, com marca d'água — quem clica descobre que é uma ferramenta contratável
2. **Busca orgânica direta:** alguém procura "ferramenta de link na bio" e encontra, competindo direto com Linktree/Beacons — sem precisar ter visto nenhum conteúdo de bastidores antes

**Modelo:** grátis até 3 páginas, depois R$ 19,90/mês (com desconto no plano anual). Marca d'água some só no plano pago. *(Mecanismo anti-abuso de múltiplas contas gratuitas é decisão de produto, já resolvida à parte — fora do escopo deste documento.)*

---

## 6. Estrutura Organizacional — Os 8 Departamentos + Agente Monitor

Cada departamento tem seu território — sem sobreposição. Todos seguem o mesmo padrão: missão, quem opera, o que aceita/não aceita, como opera, métricas.

### 6.1 Aquisição & Marketing
**Missão:** gerar atenção, capturar leads, nutrir quem não está pronto pro SDR. Cobre P1 (E1-E3).
**Quem opera:** você cria o conteúdo · **Marina** cuida do resto (palavra-chave, remarketing, performance).
**Aceita:** conteúdo, gestão de palavra-chave, tráfego, remarketing. **Não aceita:** qualificar lead (é SDR), prometer prazo/preço (é Vendas).

**Tarefas de Marina:** cria o registro de entrada do lead no CRM Sophia (Seção 5.3) · configura fluxo de cada palavra-chave (material ou SDR) · analisa performance · gerencia Pixel/GTM · cria segmentos de remarketing · dispara boas-vindas (regras na Seção 8.2).

> Automação de comentário em post viral precisa de fila (queue), não só disparo direto — se 400 pessoas comentam numa hora, nem todas recebem resposta instantânea (ver 8.2). Priorize por palavra-chave de maior intenção.

#### 6.1.1 Tráfego Pago — Fases + Nauta

**Fase 1 (agora):** impulsionar só conteúdo orgânico validado — sem Nauta dedicado ainda.
**Fase 2:** **Nauta** publica campanha, analisa métricas e gera/ajusta campanhas. Não fala com o lead — opera só com a plataforma de anúncios, e alimenta o ChronoDesk automaticamente com o dado de gasto (Seção 5.4).

**Por que isso exige leitura constante do algoritmo:** o Meta Ads mudou de forma estrutural em 2026. O algoritmo (Andromeda) e o ecossistema Advantage+ decidem automaticamente público, posicionamento e formato — o trabalho deixou de ser "quem eu miro" e virou "que sinal e criativo eu entrego pro algoritmo aprender."

O que Nauta precisa saber e monitorar continuamente:
- Desde fevereiro/2026, toda campanha nova sobe com Advantage+ Creative ativado por padrão
- Advantage+ Shopping é campanha padrão pra e-commerce, reduzindo CPA em ~17% em média
- O algoritmo aprende com volume e diversidade de criativo (mínimo 5-10 criativos), não com segmentação manual apertada
- Sinal de conversão "sujo" desperdiça o orçamento de aprendizado — checar antes de qualquer campanha nova
- Orçamento mínimo pro algoritmo aprender direito: geralmente a partir de R$ 100-200/dia
- A Meta ativa novas features do Advantage+ automaticamente, às vezes sem aviso — checar o Gerenciador de Anúncios com regularidade

**Humano vs. Nauta (Fase 2):**

| | Humano especialista | Nauta |
|---|---|---|
| Forças | Julgamento criativo, leitura de mercado | Roda 24/7, ajusta lance/orçamento em tempo real, custo marginal baixo |
| Riscos | Custo fixo, tempo de contratação | Decisão de budget real — precisa de teto de gasto e alçada de aprovação |

**Recomendação:** modelo híbrido — Nauta cuida do mecânico (lance, orçamento, pausar criativo fraco), pessoa cuida do criativo.

**KPIs:** Leads gerados (mês) · CPL (tendência) · Taxa Comentário→Fluxo (>15%) · Taxa Conteúdo→SDR (8-12%) · CAC (<20-25% do ticket médio) · ROAS (>3x quando houver pago).

### 6.2 Qualificação (SDR Fernando)
**Missão:** qualificar leads e agendar reuniões só com quem tem potencial real. Cobre P1→P2 (E1→E4). **Nunca discute preço final nem fecha.**
**Quem opera:** 100% Fernando.

**Como opera:** recebe o lead que Marina registrou → roda DOR → ESTRUTURA → VERBA → URGÊNCIA → QUALIFICADO → aplica score e faturamento → ao qualificar, Orbytwin assume o agendamento automaticamente (Seção 5.2) → atualiza a memória permanente.

**SLA por faturamento:**

| Faturamento mensal | SLA de agendamento |
|---|---|
| ≥ R$ 100 mil | Até 24h |
| R$ 50-100 mil | Até 48h |
| R$ 20-50 mil | 7 dias + diagnóstico completo |
| Abaixo de R$ 20 mil | Só agenda se o diagnóstico mostrar ROI claro |

**Roteamento por score:** ≥70 = lead quente, handoff prioritário pro Closer (a reunião continua acontecendo, só mais rápido) · 40-69 = reunião padrão (E4) · <40 = volta pra nutrição (E3).

> Vale um critério explícito pra **E2 (Desqualificado)**, separado de E3: fora do ICP por segmento, ou faturamento abaixo do mínimo mesmo após nutrição.

**KPIs:** Taxa de Qualificação (>25-35%) · Show-up (>70%) · Tempo médio até agendar leads quentes (<48h) · Score médio (>55) · Taxa de No-show (<25%).

### 6.3 Vendas (Closer / Pré-Venda)
**Missão:** transformar reunião qualificada em contrato + pagamento inicial. Cobre E4→E6.
**Quem opera:** você conduz a reunião e define o status · **Rafael** monta o dossiê antes · **Orbytwin** gera o link, transcreve e sincroniza o resultado.
**Aceita:** diagnosticar, propor, negociar, fechar. **Não aceita:** prometer prazo sem alinhar com Delivery.

**Como opera:** recebe o dossiê de Rafael via teleprompter do Orbytwin (Seção 5.2) → conduz a reunião de diagnóstico → monta escopo + proposta (E5) → negocia → define status Aprovado/Não fechou dentro do Orbytwin → se aprovado, envia contrato, confirma pagamento inicial (E6) → Zaya assume a partir daqui.

**KPIs:** Reunião→Proposta (>70%) · Proposta→Contrato (30-40%) · Ticket médio · Ciclo de vendas (<15-20 dias) · % projetos recorrentes.

### 6.4 Delivery (Projetos)
**Missão:** entregar com qualidade, no prazo, dentro do escopo. Cobre E6→E10.
**Quem opera:** você desenvolve · **Zaya**/ChronoDesk cuida do tracking e comunicação de progresso.
**Aceita:** construir, testar, entregar dentro do escopo assinado. **Não aceita:** aceitar mudança de escopo sem repassar pra Vendas, liberar código sem pagamento total confirmado.

**Como opera:** contrato + pagamento inicial → Zaya cria o projeto no ChronoDesk usando o escopo do contrato → escopo quebrado em tarefas → link de acompanhamento em tempo real gerado (o cliente também pode, pela própria URL, solicitar demanda, enviar mensagem **e agendar reunião** direto) → desenvolvimento, testes, homologação → código só ativa após pagamento total → projeto único: entrega código-fonte; recorrente: entrega código + cria usuário admin na estrutura isolada do cliente → 30 dias de garantia (relógio começa na confirmação de recebimento).

**KPIs:** On-time delivery (>85%) · Escopo controlado (>90%) · NPS pós-entrega (>8,5) · Retrabalho (<15%) · Margem por projeto (>50-60%) · Conclusão de pagamento (>95%).

### 6.5 Sucesso do Cliente
**Missão:** garantir resultado, reter e expandir. Atua após E10/E11/E12.
**Quem opera:** você conduz reunião de acompanhamento quando necessário · **Beatriz** monitora saúde, alerta e coleta feedback.
**Aceita:** acompanhar, reter, identificar upsell, coletar feedback. **Não aceita:** negociar valor de novo contrato sozinha (volta pra Vendas).

**Como opera:** onboarding → acompanha resultados → health check → identifica dores novas → oferece módulos/projetos → cuida de renovação → coleta cases (alimenta Marketing, 6.1).

**KPIs:** Churn (<5-7%) · NRR (>100%) · % clientes com 2º projeto (>25-30%) · Health Score (>70) · Taxa de renovação (>80%).

### 6.6 Produto & Plataforma
**Missão:** evoluir os produtos próprios (BioLeads, Orbytwin, ChronoDesk, CRM Sophia) e a operação interna.
**Quem opera:** você desenvolve e evolui.
**Aceita:** roadmap, desenvolvimento, infraestrutura. **Não aceita:** desenvolver customização exclusiva de um cliente sem passar por Delivery.

**KPIs:** Features no prazo (>80%) · Uptime (>99,5%) · Resolução de bugs críticos (<48h).

### 6.7 Financeiro & Operações
**Missão:** controlar a saúde financeira. **Zaya**, dentro do ChronoDesk, registra nota fiscal, recebimento, despesa, calcula margem por projeto, lucro líquido, burn rate, runway — inclusive do CPF, não só da empresa.
**Quem opera:** 100% Zaya/ChronoDesk.
**Aceita:** registrar, calcular, projetar. **Não aceita:** decidir sozinha sobre desconto/condição comercial.

**Painel semanal (7 números):** receita do mês · MRR · custos totais · lucro líquido · margem média por projeto · inadimplência · fluxo de caixa projetado (30/60 dias).

**KPIs:** margem bruta por projeto e da empresa · lucro líquido · burn rate · runway · inadimplência · ponto de equilíbrio.

### 6.8 Inteligência & Dados (Transversal)
**Missão:** garantir reconhecimento do usuário em qualquer canal, memória permanente, qualidade de dado. Arquitetura completa na Seção 8.
**Quem opera:** 100% agente/sistema.
**Aceita:** reconhecer, unificar, manter memória, dar suporte a decisão. **Não aceita:** tomar decisão comercial sozinho.

**KPIs:** Taxa de reconhecimento (>90%) · Completude da memória (>85%) · Taxa de match entre canais (>80%).

### 6.9 Agente Monitor (Otávio) — Camada de Supervisão

**Missão:** consolidar a saúde de todos os departamentos/agentes num ponto único — essencial porque, sozinho, você não vai checar vários painéis todo dia. **Não é o Hermes.**
**Quem opera:** 100% Otávio.
**Aceita:** observar, consolidar, alertar. **Não aceita:** ação corretiva sozinho nos outros agentes (por enquanto — ver Seção 16).

**Como opera:** observa as métricas-norte de cada departamento (Seção 13) → sinaliza quando algo sai da meta → reporta pra você.

**KPI:** tempo entre uma métrica sair da meta e você ser notificado.

---

## 7. Motor de Conteúdo → Lead

**Canais de entrada (os 4 que existem hoje):** formulário do site · número de WhatsApp · DM direto pro Instagram (ADM) · comentário em vídeo, orgânico ou impulsionado (ads). Qualquer um desses 4 toques faz Marina criar o lead — ver definição de "vira lead" na Seção 4.

**Pilares:** análise de ferramentas (topo) · bastidores de construção (meio, confiança técnica) · segurança (meio/fundo) · conteúdo institucional (topo) · feedback de clientes (fundo, prova social).

**Mecânica da palavra-chave:** cada vídeo tem uma palavra-chave única na CTA → comentário dispara automação → **Fluxo Material** (entrega recurso, vai pra Aquecimento/E3) ou **Fluxo SDR** (puxa pra conversa com Fernando, entra em qualificação). Documente qual palavra dispara qual fluxo numa planilha viva.

### 7.1 Segmentação de Remarketing — Quem Entra, Quem Não Entra

Isso responde direto a pergunta de quais leads alimentam campanha de remarketing (Nauta, Seção 6.1.1) — não é "todo mundo que já foi lead", é segmentado por intenção:

| Segmento | Quem é | Objetivo do remarketing | Entra? |
|---|---|---|---|
| **Aquecimento** (E3 — as 3 portas da Seção 4.4) | Score baixo, parou de responder, ou só recebeu material | Nutrir até a primeira conversa real com Fernando | ✅ Prioridade máxima — é o público que mais justifica verba |
| **Não fechou / Perdido** (pós-E4 ou pós-E5) | Já teve reunião ou proposta, não avançou | Reconquista — já conhece a solução, só faltou o gatilho certo | ✅ Alta prioridade, criativo diferente (não é "primeira apresentação") |
| **Desqualificado** (E2) | Fora do ICP mesmo após tentativa | — | ❌ Nunca — verba gasta em quem estruturalmente não pode ser cliente |
| **Em negociação ativa** (dentro de E4/E5 agora) | Sendo atendido nesse momento por Fernando ou por você | — | ❌ Suspenso enquanto durar — remarketing concorre com a conversa real, não ajuda |
| **Cliente ativo** (E11) | Contrato recorrente rodando | Upsell/expansão, não aquisição | ✅ Audiência separada, criativo de expansão (nunca o mesmo anúncio de captação) |
| **Cliente único passado** (E12/E13) | Projeto entregue, sem recorrência | Reativação | ✅ Audiência separada, criativo que reconhece o histórico |

**Regra prática:** toda audiência de remarketing carrega a tag de segmento (mesma lógica das tags do Orbytwin, Seção 5.2) — Nauta nunca mistura "Aquecimento" com "Cliente ativo" na mesma campanha, porque a mensagem certa muda completamente de um pro outro.

### 7.3 Matriz de Palavras-Chave Validadas (Google Brasil via AIsa)

Dados apurados via DataForSEO/AIsa para direcionar a criação de conteúdo orgânico (Marina) e campanhas pagas (Nauta):

| Cohort / Nicho | Palavra-Chave | Volume Mensal | Dificuldade (KD) | CPC Médio (USD) | Intenção | Aplicação no Funil |
|---|---|---|---|---|---|---|
| **Advocacia** | `advogado trabalhista` | 60.500 | 16 | $4.08 (~R$ 23) | Informacional/Comercial | Conteúdo de dor sobre perda de leads |
| **Advocacia** | `advogados criminais online` | 50 | - | $7.99 (~R$ 45) | Comercial | Demonstração do custo de ignorar lead |
| **Advocacia** | `advogados de familia online` | 90 | - | $4.92 (~R$ 28) | Comercial | Triagem ágil 24/7 com Agente Lea |
| **Advocacia** | `advogados online agora` | 50 | 44 | $3.01 (~R$ 17) | Comercial | Urgência: atendimento em menos de 1 minuto |
| **Clínicas** | `clinica nas nuvens` | 40.500 | 11 | $0.20 | Navegacional | Integração via Webhook / Não concorrência com ERP |
| **Clínicas** | `minha consulta` | 27.100 | 4 | $0.60 | Navegacional | Confirmação ativa de consulta no WhatsApp |
| **Clínicas** | `agendamento consulta estetica` | 1.000+ | <20 | $1.20 | Transacional | Qualificação automática de procedimentos alto ticket |
| **Softhouse B2B** | `pipeline de vendas` | 1.300 | 10 | $5.13 (~R$ 29) | Comercial | Landing page: "Onde seu pipeline morre no WhatsApp" |
| **Softhouse B2B** | `vendas online` | 8.100 | 15 | $3.95 (~R$ 22) | Comercial | Posicionamento de agentes autônomos de conversão |

---

## 8. Camada de Identidade Única e Memória Permanente

**Princípio:** independente de onde a pessoa aparecer, o sistema sabe quem ela é, em que etapa está, e continua a conversa de onde parou. A extração completa de dado não é só pra memória — é pra garantir precisão de análise em qualquer ponto do ecossistema (Seção 5.4).

| Canal | Como identifica |
|---|---|
| Instagram (comentário/DM) | Instagram User ID + username |
| WhatsApp | Número de telefone |
| Site/Formulário | Email + telefone + cookies |
| Anúncios (Meta) | Pixel + Click ID + dados do formulário |

**Memória permanente por User ID:** nome, telefone, email, Instagram, empresa, faturamento, dores, etapa (E1-E13), histórico completo, materiais recebidos, propostas, reuniões, score, tags, última interação, fonte original. Mora no CRM Sophia — sincroniza com ChronoDesk a partir de E6 (Seção 5.1).

### 8.1 Caminho Para a VSL Personalizada

| Nível | Como funciona | Complexidade |
|---|---|---|
| 1 — Landing personalizada | Link único carrega o User ID; página insere o nome como texto ao redor do vídeo | Baixa |
| 2 — Áudio dinâmico | TTS grava o nome, costura no ponto certo do áudio | Média |
| 3 — Vídeo gerado por pessoa | IA generativa de vídeo com lip-sync dizendo o nome | Alta |

**Recomendação:** comece no Nível 1.

### 8.2 Método Seguro de Automação no Instagram

Princípio: **toda automação dispara depois do primeiro passo do usuário — nunca antes.**

1. Usuário comenta a palavra-chave (abre a janela de mensagem)
2. Fluxo inteligente responde (Seção 7)
3. Se o usuário SEGUIR a conta depois, Marina manda boas-vindas simples — sem venda
4. Se o admin manda mensagem primeiro, reconhecimento inteligente ativa a IA

**Regras técnicas:** sempre API oficial da Meta (Graph API) · janela de 24h respeitada · fila de envio em picos de comentário · redobrar cuidado em contas novas (tolerância a erro menor).

---

## 9. Automação "Mapa Matador" — Inteligência Pré-Reunião (Rafael)

**Onde entra:** entre o agendamento automático do Orbytwin (E4) e a reunião de fato acontecer.

**O que Rafael faz:** pega os dados que Fernando já coletou → varre dado público — Instagram e site (usando nossas próprias chaves de API), busca no Google, LinkedIn/Facebook se existirem, Reclame Aqui, CNPJ quando disponível, concorrentes próximos, **se a empresa já roda tráfego pago (verifica pixel instalado no site)**, análise do funil atual dela → organiza e interpreta → gera o dossiê com 8 seções: resumo executivo, visão da empresa, análise de Instagram, análise de site, sinais de oportunidade, pontos de atenção, roteiro de perguntas, hipótese de solução prévia.

**Entrega:** o dossiê não fica só num documento separado — Rafael envia direto pro Orbytwin, que exibe como bloco de notas no teleprompter durante a própria reunião (Seção 5.2). Você não precisa alternar entre telas.

**Regras:** só dado público · nunca inventa · sempre mostra a fonte · atualiza a memória permanente · empresa pequena/sem presença digital → dossiê mais enxuto, avisando isso.

**Timing:** dispara assim que Orbytwin agenda; gera em 5-15 min.

> **LGPD:** dado público de empresa pra prospecção B2B tem base legal mais tranquila que perfilamento de pessoa física. Seja seletivo sobre o que vira campo **permanente** do User ID.

---

## 10. Handoffs Entre Agentes — De Quem Pra Quem

| Etapa | Quem fala com o lead | O que é passado adiante |
|---|---|---|
| E1-E3 (Prospecção) | **Marina** | User ID + canal de origem + histórico → Fernando |
| E4 (Qualificação) | **Fernando** | Diagnóstico + score + tier → Orbytwin (agendamento automático) |
| E4 (pré-reunião) | **Rafael** — não fala com o lead | Dossiê → Orbytwin (teleprompter) |
| E4 (reunião) | Você, com **Orbytwin** gerando link/transcrevendo | Status Aprovado/Não fechou → atualiza etapa no CRM Sophia automaticamente |
| E6→E10 (Delivery) | Você (desenvolvimento) + **Zaya**/ChronoDesk | Projeto entregue + histórico → Sucesso do Cliente |
| E11-E13 (CS) | Você (reunião quando necessário) + **Beatriz** | Feedback/case → Marketing (fecha o loop) |
| Todas as etapas | **Otávio** observa (não fala com o lead) | Sinaliza desvio de métrica → você |

---

## 11. Cultura de Auto-Evolução — Registrar, Aprender, Não Repetir

**Princípio:** cada agente registra o resultado de cada ação relevante — o que funcionou, o que não funcionou — e isso vira parte da memória do sistema, não só do lead individual.

**Como funciona na prática:** toda decisão importante fica registrada com o resultado (Fernando classificou Tier A e não fechou; Nauta pausou um criativo). Esse histórico vira input pro próprio agente ajustar o próximo caso parecido.

**Onde mora:** histórico do User ID (Seção 8) pra decisões ligadas a um lead específico; log separado por agente/departamento pra padrões que se repetem entre leads diferentes.

---

## 12. Recorrência vs. Projetos Concluídos

| Etapa | Situação | O que acontece |
|---|---|---|
| E11 — Cliente Mensal | Recorrente | Beatriz assume: check-in periódico, SLA de suporte, monitoramento técnico |
| E12 — Cliente Único | Concluído | Reativação: 30/60/90 dias após E13, Beatriz avalia gatilhos de expansão |
| E13 — Entrega Concluída | Garantia encerrada sem pendência | Dispara reativação (E12) ou check-in de satisfação (E11) |

**Loop de feedback:** feedback positivo vira matéria-prima de conteúdo (Seção 7), fechando o funil de volta ao topo.

---

## 13. KPIs — Visão Executiva

| Departamento | KPI Norte |
|---|---|
| Aquisição & Marketing | CAC (<20-25% do ticket médio) |
| Qualificação (SDR) | Taxa de Qualificação (>25-35%) |
| Vendas (Closer) | Proposta→Contrato (30-40%) |
| Delivery | Margem por Projeto (>50-60%) |
| Sucesso do Cliente | NRR (>100%) |
| Produto & Plataforma | Uptime (>99,5%) |
| Financeiro | Lucro Líquido do Mês |
| Inteligência & Dados | Taxa de Match entre Canais (>80%) |
| Agente Monitor (Otávio) | Tempo entre desvio de métrica e notificação |

---

## 14. Stack de Ferramentas

| Função | Situação |
|---|---|
| Reunião de ponta a ponta (link, transcrição, teleprompter, status) | **Orbytwin** — resolvido (Seção 5.2) |
| CRM pré-contrato / funil de leads / canais | **CRM Sophia** — resolvido (Seção 5.3) |
| Delivery + Portal do Cliente + Financeiro (empresa e CPF) | **ChronoDesk**, operado por **Zaya** — resolvido (Seção 5.4) |
| WhatsApp (Fernando/Marina) | **Evolution API**, self-hosted na VPS — aplicar fila/rate-limit |
| Automação de Instagram | API oficial da Meta — regras na Seção 8.2 |
| Identidade unificada / memória | Seção 8 — a formalizar tecnicamente |
| Modelos de IA por trás dos agentes | Ecossistema próprio (padrão) ou credenciais do cliente — ver 3.2 |

---

## 15. Roadmap de Implementação

1. Aplicar fila/rate-limit na Evolution API com a mesma disciplina da Seção 8.2 — não é urgência, mas fecha o risco residual de canal
2. Consolidar este documento como fonte única
3. Travar critérios em aberto: saída de E9 (4.3), critério de E2 (6.2), regra de convivência Zaya × Fernando/Marina no WhatsApp
4. Implementar o fluxo corrigido de automação no Instagram (8.2)
5. Implementar o Nível 1 da VSL personalizada (8.1)
6. Confirmar que o agendamento automático do Orbytwin (5.2) e a entrega do dossiê de Rafael no teleprompter estão realmente conectados ponta a ponta
7. Construir o Agente Monitor/Otávio (6.9) — mesmo que a primeira versão seja simples
8. Confirmar que a página nativa de Departamentos do ChronoDesk está puxando métrica do funil sincronizado automaticamente (5.4)
9. Decidir o modelo híbrido humano+Nauta pra tráfego pago Fase 2 (6.1.1)
10. Implementar o log de aprendizado por agente (Seção 11)
11. Investigar o volume atual do funil (poucos leads nas etapas iniciais do painel)

---

## 16. Pontos em Aberto

- **Disciplina de fila/rate-limit na Evolution API:** não é risco urgente, mas vale aplicar antes de aumentar volume
- **Regra Zaya × Fernando/Marina:** confirmar que Zaya só manda mensagem avulsa por comando seu, nunca em lead dentro de fluxo ativo
- **Critério explícito de E2:** regra objetiva separando "desqualificado" de "esfriou"
- **Tráfego pago Fase 2:** quando abrir e com que modelo exato
- **Volume atual do funil:** poucos leads nas etapas iniciais do painel — ambiente de teste ou gargalo real?
- **Autonomia de Otávio:** só observa e alerta, ou em algum momento passa a agir sozinho sobre os outros agentes?
- **Onde mora o log de aprendizado (Seção 11):** dentro do ChronoDesk, ou base separada?
- **Orbytwin, CRM Sophia e ChronoDesk como produtos vendáveis separadamente:** os planos nativos do ChronoDesk (Bronze/Prata/Ouro/Diamond) e o modelo "organismo único" da Seção 5.1 indicam potencial white-label pros três, não só uso interno — vale formalizar isso como linha de produto
- **Fórum + rede social:** produto vendável para clientes, ativo de comunidade da própria marca, ou os dois?
- **Critério de qualidade pra abrir nicho ao público:** piso financeiro (~R$20 mil/mês, ~5 clientes) já está definido — falta o critério de *case bom o suficiente* pra virar prova pública, não só "deu certo"
- **Preço do ChronoDesk como SaaS externo:** mensalidade ou anuidade, valor ainda não definido (Seção 5.4)

