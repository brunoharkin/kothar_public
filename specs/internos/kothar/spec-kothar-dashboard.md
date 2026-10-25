---
tipo: spec
produto: kothar
status: aprovada
autor: Kothar
data: 2026-06-01
---
# Spec — Kothar Dashboard (MVP)

← [[kothar]]

## 1. Problema

Bruno gerencia múltiplas aplicações (BioLeads, disparo-em-massa, futuros produtos) que dependem de infraestrutura compartilhada — principalmente o WhatsApp Gateway (OpenWA). Hoje, para conectar um chip novo ou ver o status de uma sessão, precisa entrar no painel do disparo-em-massa, que é uma ferramenta de outra função. Quando novos produtos surgirem, o problema se multiplica.

## 2. Solução

Painel central da Ugarit (Kothar Dashboard) com módulo de controle do WhatsApp Gateway. Cada produto se conecta via API key com permissão específica. Bruno gerencia tudo num lugar sem entrar em cada app.

## 3. MVP — Módulo WA

### Tela: Dashboard (/)
- Cards de status de cada chip: número, nome, status (conectado / desconectado / aguardando QR)
- Indicador de uptime
- Animação GSAP nos cards de status

### Tela: Centro WA (/whatsapp)
- Lista de chips (sessões) com status em tempo real
- Botão "Adicionar chip" → abre modal com QR Code
- QR atualiza automaticamente via SSE até conectar (polling no backend a cada 5s)
- Ao conectar: QR some, status vira "● Conectado", número aparece
- Botão "Desconectar" por chip

### Tela: Detalhe do chip (/whatsapp/[id])
- Nome, número detectado, status, data de conexão
- Apps vinculadas (campo editável no MVP — apenas informativo)
- Botão desconectar / reconectar

## 4. Backend (Fastify)

### Rotas
```
GET  /api/chips                  ← lista todos os chips do gateway
GET  /api/chips/:id/status       ← status de um chip específico
GET  /api/chips/:id/qr           ← SSE: stream do QR Code até conectar
POST /api/chips                  ← criar nova sessão no gateway
POST /api/chips/:id/start        ← iniciar sessão
POST /api/chips/:id/stop         ← parar sessão
DELETE /api/chips/:id            ← remover sessão
```

### Autenticação
- Header `X-Kothar-Secret: {HERMES_SECRET}` em todas as rotas
- Sem JWT no MVP — painel é uso pessoal do Bruno

### Proxy para OpenWA
O backend do Kothar faz proxy para o OpenWA Gateway. Não expõe o gateway diretamente — toda chamada passa pelo Kothar.

```
Frontend → Kothar Backend → OpenWA Gateway (:2785)
```

## 5. Variáveis de ambiente

```env
# Kothar
HERMES_SECRET=change-me           # senha de acesso ao painel

# OpenWA Gateway
OPENWA_URL=http://localhost:2785
OPENWA_API_KEY=dev-admin-key

# App
PORT=3100
NODE_ENV=development
```

## 6. Fora de escopo no MVP

- Permissões granulares por app (qual app pode fazer o quê)
- Log de chamadas por app
- Múltiplos usuários / login
- Notificações quando chip desconecta

## 7. Design

- Visual: painel dark premium, padrão Ugarit (mesmo estilo do BioLeads)
- Gráficos dinâmicos com GSAP / Framer Motion
- Cards de status com indicador de pulso (● verde / ● amarelo / ● vermelho)
- QR Code renderizado em canvas ou via lib `qrcode`

## 8. Plano de implementação

**Ordem de execução:**
1. Scaffolding do projeto (Next.js + Fastify + Docker)
2. Backend: rotas de chips (proxy para OpenWA)
3. Frontend: layout base + dashboard
4. Frontend: tela de chips + lista com status
5. Frontend: modal QR Code com SSE em tempo real
6. Frontend: tela de detalhe do chip
7. Docker Compose + variáveis + teste local
8. (Deploy na VPS — fora do MVP imediato)

## 9. Definition of Done

- [ ] Consegue ver todos os chips conectados ao OpenWA
- [ ] Consegue conectar um chip novo via QR Code na tela (sem abrir outro painel)
- [ ] Status atualiza em tempo real sem recarregar a página
- [ ] BioLeads consegue chamar o gateway via Kothar sem tocar no disparo-em-massa
