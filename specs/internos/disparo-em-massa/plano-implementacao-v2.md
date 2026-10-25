← [[specs]]

# Plano de Implementação v2.0 — Disparo em Massa (Ugarit v2)

**Status**: Aprovado pelo Operador
**Data**: 2026-05-25
**Objetivo**: Escalar de ~1.300 msgs/dia (1 chip) para 20.000+ msgs/dia (multi-chip)

---

## Decisão de Stack

### API Oficial (WhatsApp Business API)
- Custo: US$ 0,05–0,15 por conversa iniciada
- 20.000/dia = US$ 30.000–90.000/mês
- **Inviável**

### whatsapp-web.js (atual)
- Puppeteer: ~300MB RAM/instância
- 35 chips = ~10,5 GB RAM → VPS cara (R$ 250–500/mês)

### Baileys (ESCOLHIDO)
- WebSocket puro: ~40MB/instância
- 35 chips = ~1,5 GB RAM → VPS barata (R$ 60–120/mês)
- Base de toda ferramenta comercial de disparo profissional
- Migração: só a camada `backend/chips/` muda

---

## Arquitetura v2.0

```
disparo-em-massa/
├── backend/
│   ├── inicializador.js
│   ├── chips/
│   │   ├── gerenciador-chips.js     — pool, rotação, healthcheck
│   │   ├── chip.js                  — abstração Baileys por instância
│   │   └── aquecedor-chips.js       — warm-up gradual de chips novos
│   ├── disparador/
│   │   ├── fila-disparo.js          — fila de mensagens
│   │   ├── agendador.js             — agendamento
│   │   └── politica-disparo.js      — regras de rotação, delay, limites
│   ├── mensagens/
│   │   ├── variador-templates.js    — alterna entre 3-5 templates
│   │   ├── personalizador.js        — {nome}, {empresa}, {cidade}
│   │   └── humanizador.js           — delay de digitação, online
│   ├── funil/
│   │   ├── controlador-funil.js     — máquina de estados
│   │   ├── etapa-prospeccao.js      — Msg 1: gancho
│   │   ├── etapa-filtro.js          — Msg 2: apresentação + permissão
│   │   └── etapa-entrega.js         — Msg 3: proposta/material
│   ├── inteligencia-artificial/
│   │   ├── agente.js                — existente (mantido)
│   │   └── classificador-resposta.js — positivo/negativo/objeção
│   ├── banco-de-dados/
│   │   ├── conexao.js
│   │   ├── migracoes/
│   │   └── repositorios/
│   └── retencao/
│       ├── simulador-presenca.js    — composing, available
│       └── gerador-audio.js         — TTS → ogg opus
└── frontend/
    └── paginas/
        ├── painel/
        ├── chips/
        └── campanhas/
```

---

## Capacidade por Configuração

| Chips | Delay médio | Msgs/chip/dia | Total/dia |
|---|---|---|---|
| 10 | 50s | 576 | 5.760 |
| 20 | 50s | 576 | 11.520 |
| 35 | 50s | 576 | **20.160** ✅ |
| 20 | 30s | 960 | 19.200 |

---

## Anti-Bloqueio (4 Camadas)

### Camada 1 — Rotação de Chip
- Nunca mesmo chip em mensagens consecutivas da mesma lista
- Round-robin com peso (chips mais antigos têm peso maior)
- Limite hard: chip para ao atingir `limite_diario`
- Janela de descanso: 6h após atingir 50% do limite

### Camada 2 — Delay com Jitter
- Base: configurável por campanha (30-60s)
- Jitter: ±30% exponencial
- Garantia: nunca mesmo intervalo duas vezes seguidas

### Camada 3 — Variação de Mensagem
- Operador cadastra 3-5 templates por campanha
- Seleção: template varia por contato + chip
- Personalização: {nome}, {empresa}, {cidade}
- Variação semântica: aplicada em cima do template

### Camada 4 — Warm-up
| Período | Limite diário | Delay mínimo |
|---|---|---|
| Dia 1–3 | 50 msgs | 90s |
| Dia 4–7 | 150 msgs | 60s |
| Dia 8–15 | 300 msgs | 45s |
| Dia 16+ | 500 msgs | 30s |

---

## Funil de Conversão (3 Etapas)

```
[Etapa 1 — Prospecção]
Chip X → "Oi {Nome}! Tudo certo?"
Template variado por chip + contato

↓ pessoa responde

[Etapa 2 — Filtro + Permissão]
GPT classifica: positivo | negativo | objeção

positivo/neutro:
"Oi! Me chamo {Vendedor}. Ajudo {tipo} a {valor}.
 Posso te enviar um modelo pra ver como ficaria?
 Aproveita e salva meu número 😊"

objeção:
GPT contorna → repete CTA

↓ autoriza

[Etapa 3 — Entrega]
Envia material contextualizado com dados do cliente:
- Cardápio personalizado
- Landing page demo
- PDF com nome/logo do prospect

↓ sem resposta em 48h → expirado
```

**Estados do funil:**
```
aguardando_1 → filtro_enviado → convertido
                              → recusado
             → expirado (48h sem resposta)
```

---

## Retenção

### Simulação de Digitando
```javascript
await chip.sendPresenceUpdate('composing', jid);
// aguarda tempo proporcional ao tamanho da mensagem (3-12s)
await chip.sendMessage(jid, { text: msg });
await chip.sendPresenceUpdate('paused', jid);
```

### Áudio (diferencial máximo)
- Taxa de abertura áudio WA: ~85% vs ~35% texto
- Etapa 2 pode ser áudio de 15-25s (apresentação pessoal)
- TTS: Google Cloud (grátis no tier baixo) ou ElevenLabs (US$ 5/mês)
- Formato: .ogg opus (compatível direto com WhatsApp via Baileys)

### Pedir para Salvar Número
- Sempre na Etapa 2
- Número salvo = relação estabelecida = abertura prioritária

---

## Schema PostgreSQL

```sql
CREATE TABLE chips (id, nome, numero, status, mensagens_hoje, limite_diario, ...);
CREATE TABLE campanhas (id, nome, status, templates JSONB, tipo, ...);
CREATE TABLE contatos (id, nome, numero UNIQUE, empresa, cidade, ...);
CREATE TABLE mensagens_log (id, campanha_id, contato_id, chip_id, template_usado, status, etapa_funil, ...);
CREATE TABLE conversas_funil (id, contato_id, campanha_id, etapa_atual, status, historico JSONB, ...);
```

---

## Métricas do Dashboard

```
Taxa de Envio       = Enviadas / Total
Taxa de Entrega     = Entregues / Enviadas
Taxa de Abertura    = Lidas / Entregues
Taxa de Resposta    = Respondidas / Enviadas
Taxa de Funil E2    = Etapa 2 / Respondidas
Taxa de Conversão   = Etapa 3 concluída / Respondidas

Por chip:
  - Msgs hoje / limite | Status | Taxa de risco
```

---

## Viabilidade Financeira

| Item | Custo/mês |
|---|---|
| 35 chips (recarga) | R$ 350 |
| VPS Hetzner 4GB (Baileys) | R$ 100 |
| OpenAI GPT-4o-mini | R$ 20 |
| **Total operacional** | **~R$ 470** |

| Modelo de cobrança | Valor |
|---|---|
| Setup + config | R$ 5.000–12.000 (único) |
| Manutenção mensal | R$ 1.500–3.000 |

---

## Fases e Prioridades

| # | Fase | Impacto |
|---|---|---|
| 1 | Arrumar a casa + PostgreSQL | Fundação |
| 2 | Multi-chip com Baileys | Crítico (escala) |
| 3 | Anti-bloqueio (rotação + delay + templates) | Crítico |
| 4 | Funil de conversão 3 etapas | Alto (conversão) |
| 5 | Retenção (digitando + áudio) | Alto (abertura) |
| 6 | Dashboard PostgreSQL | Médio |
