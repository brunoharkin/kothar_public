---
tipo: plano-mestre
produto: bioleads
status: aprovado-para-execução
autor: Kothar
data: 2026-06-01
relacionado:
  - "[[spec-track-a-precisao]]"
  - "[[bioleads]]"
---

# Plano Mestre — Precisão + Novas Fontes (MCP) do BioLeads

← [[bioleads]] · [[spec-track-a-precisao]]

> **Objetivo único:** o BioLeads passa a entregar **lead qualificado confiável** —
> só afirma o que verificou, busca em todas as fontes possíveis (Google, redes,
> internet) e nunca trata falha de coleta como "não existe". À prova de falhas por
> design: cada fonte tem retry, fallback, estado tri-state e proveniência.

---

## 0. Princípio norteador (a regra de ouro)

**"Só afirmar o que foi verificado."**
Todo campo tem três estados, nunca dois:

| Estado | Significado | Exemplo |
|--------|-------------|---------|
| `True` / valor | verificado e confirmado | tem pixel Meta (achou `fbq(`) |
| `False` | verificado e ausente | site leu OK, não há pixel |
| `None` / "não verificado" | **não foi possível checar** | site deu 403 / timeout |

O bug atual nº1 é colapsar `None` em `False`. Isso acaba aqui.

---

## 1. Mapa de fontes por sinal (qual "MCP"/fonte para o quê)

Verdade técnica: o **backend usa APIs HTTP**, não MCP embutido. Os MCP (Windsor,
instagram) estão ligados ao **agente Kothar**, para operação/relatório do Bruno.
Para o produto, a mesma qualidade entra via **API REST** das fontes.

| Sinal do lead | Fonte precisa | Tipo | Frio ou pós-conversão | Estado |
|---|---|---|---|---|
| Existe / nome oficial / telefone / endereço / rating / horário | **Google Places (New)** | API key | frio | ✅ ligado/testado |
| CNPJ / razão social / sócios / CNAE | **ReceitaWS** | API | frio | ✅ existe |
| Tem site / pixel / email / WhatsApp / social links | **Site scraper** | scraping | frio | 🔧 Track A |
| Performance / Core Web Vitals | **PageSpeed** | API key | frio | ✅ existe |
| Consistência de postagem / seguidores (IG) | **Scrape IG público** | scraping | frio | 🔄 robustecer |
| Roda anúncio? (público) | **Meta Ad Library** | API | frio | 🔒 gate + Identity Verification |
| Dados reais de campanha / GA4 / Ads do lead | **Windsor.ai API** | API key | **pós-conversão** (lead conecta) | 🆕 Track B |
| Validação de número WhatsApp (sem enviar msg) | **OpenWA Gateway** (mesma stack do disparo) | REST | frio | 🆕 Track B |

> **NÃO usamos Brave Search.** A descoberta é Google Places (primário) → Google CSE → DuckDuckGo (fallback grátis). O código atual prioriza Brave — o Track A **remove** o Brave.
> **BioLeads é independente do disparo-em-massa.** Não chamamos o backend do disparo. Reaproveitamos só a *stack* de WhatsApp (OpenWA Gateway REST), com cliente próprio no bioleads.

**Regra de papel do Windsor:** ele só lê contas conectadas (Ugarit + clientes).
Para prospect frio, NÃO serve. Entra quando o lead vira cliente e conecta a conta
→ aí o dossiê vira dashboard real. Confirmado por evidência (2026-06-01): no Windsor
do Bruno só há `instagram_public=ugarit_digital`, `facebook`, `googleanalytics4` etc.,
todas próprias/de clientes.

---

## 2. Arquitetura de confiança (camada nova, transversal)

Toda fonte grava, junto do dado, sua **proveniência e confiança** em
`enrichment.google_services` (já existe o padrão `_src_*`). Padronizar:

```
google_services = {
  "_src_phone": "places",        # quem preencheu
  "_src_email": "site",
  "_site_fetch": "ok|blocked|unreachable|js_only",
  "_email_validation": {"has_mx": true|false|null, "confidence": "high|medium|low"},
  "_completeness": 0.0..1.0,
  "_sources_tried": ["places","site","brave","cnpj"],
}
```

O frontend lê isso e mostra **badge de confiança** + "não verificado" vs "não tem".

---

## 3. Fases (ordem de execução)

### Fase 0 — Fundação ✅ CONCLUÍDA (2026-06-01)
- [x] `.env` criado (estava faltando — causa do "nada conecta").
- [x] Conflito de porta resolvido (Postgres bioleads em host **5433**; 5432 é do linkdabio).
- [x] Postgres + Redis + backend + worker + frontend em Docker, healthy.
- [x] Migrations aplicadas (head `c589b9db47c7`, 9 tabelas).
- [x] Chave Google configurada (Places/CSE/PageSpeed) e **testada**.
- [x] `start.sh` reescrito como lançador Docker à prova de falhas.
- [x] Erro de shell `~/.local/bin/env` corrigido.

### Fase 1 — Track A: Precisão (corrige "não acerta nada")
Detalhe completo em [[spec-track-a-precisao]]. Resumo executável:

- **A1. Scraper robusto, falha ≠ ausência** — retry com 2º UA, tratar 403/429,
  `fetch_status` tri-state; pipeline grava `None` (não `False`) quando o fetch falha.
- **A2. Não apagar email com MX inconclusivo** — `has_mx: True|False|None`;
  só remove email se sintaxe inválida OU (`mx_checked=True` e `has_mx=False`).
- **A3. Email ofuscado** — decode Cloudflare `data-cfemail`, `mailto:`, `[arroba]`/`(at)`.
- **A4. Descoberta: Places primário + merge, SEM Brave** — remover `_search_brave` do
  `google_search.py`. Cadeia nova: **Places âncora → CSE → DDG** complementam
  (merge por `nome_normalizado+telefone`), nunca sobrescrevem dado estruturado.
- **A5. Transparência no card** — badge "não verificado" vs "não tem"; fonte por campo.

**Done Fase 1:** conferência manual de 5 leads reais → nenhum campo "sem X" quando X existe.

### Fase 2 — Track B: Novas fontes
- **B1. Meta Ad Library (público)** — destravar `ENABLE_META_ADS_LOOKUP` após
  Identity Verification em facebook.com/ads/library/api. Responde "roda anúncio?".
  Cruzar com pixel: *roda anúncio mas sem pixel = dor de venda forte*.
- **B2. IG público robusto** — frequência de postagem / consistência / seguidores de
  qualquer handle. Fallback em cascata (Graph própria → scrape público → CSE).
- **B3. Windsor.ai API (pós-conversão)** — integração `integrations/windsor.py`:
  backend chama Windsor REST com API key para leads que **conectaram** a conta.
  Alimenta o dossiê com dados reais (Meta Ads/GA4). Feature-flag `ENABLE_WINDSOR`.
- **B4. Validação WhatsApp via OpenWA Gateway (mesma stack do disparo)** — o bioleads
  NÃO chama o backend do disparo. Cria cliente próprio `integrations/openwa.py` apontando
  para o mesmo gateway (`OPENWA_URL` :2785, header `X-API-Key`). Endpoint:
  `GET /api/sessions/:id/contacts/check/:numero` → `{ exists, whatsappId }`.
  **Não envia mensagem** — só confere se o número tem WhatsApp. Flag `ENABLE_WHATSAPP_VALIDATION`.

**Done Fase 2:** cada fonte atrás de flag, com fallback, sem quebrar o pipeline se cair.

### Fase 3 — Dossiê → Proposta (visão)
- Consolidar sinais num **dossiê comercial** (já há score + dores).
- Gerador de proposta que usa o dossiê (sem constância social, site sem pixel,
  anúncio sem rastreio → argumentos de venda automáticos).
- Pós-fechamento: lead conecta conta → Windsor liga o dashboard real (loop fechado).

---

## 4. Princípios à prova de falhas (engenharia — valem para TODA fonte)

1. **Tri-state sempre** — nunca colapsar "desconhecido" em "ausente".
2. **Retry com backoff** — 2 tentativas, UA alternativo, backoff curto.
3. **Timeout explícito** em toda chamada (já há 15-30s; padronizar).
4. **Cadeia de fallback** — Places→CSE→DDG (sem Brave); Graph→scrape→CSE. Uma cair, a próxima assume.
5. **Isolamento de falha** — cada etapa em `try/except`; erro vai pra `enrichment_errors`,
   nunca derruba o lead inteiro (padrão já presente em `enrichment_tasks.py`).
6. **Idempotência** — reprocessar um lead não duplica nem corrompe; gap-fill só preenche vazio.
7. **Feature flags** — toda fonte nova nasce atrás de flag (`ENABLE_*`), default off em prod.
8. **Cache** — MX por domínio (já existe), Places por `place_id`, IG por handle. Reduz custo/erro.
9. **Rate-limit** — `asyncio.sleep` entre páginas/etapas; respeitar limites de cada API.
10. **Circuit-breaker leve** — se uma fonte falha N vezes seguidas, pular por X min (Redis).
11. **Proveniência obrigatória** — todo dado gravado registra `_src_*` e confiança.
12. **Testes de extrator** — email ofuscado, MX inconclusivo, merge Places+Brave, tri-state.
13. **Observabilidade** — logs estruturados por etapa; `enrichment_errors` visível no admin.
14. **Migrations seguras** — flags de pixel viram nullable; toda migração reversível (downgrade).
15. **Rollback por flag** — desligar uma fonte = flipar a flag, sem deploy.

---

## 5. Riscos & mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| A4 muda busca de produção | nomes/contagem diferentes | validar 3 nichos reais antes de subir; flag de fonte |
| Custo Places sobe (primário) | $ | cache por place_id; teto de 50; medir antes/depois |
| Scraper bloqueado (Cloudflare/JS) | dados faltando | tri-state "não verificado" (não mente); 2º UA; futuro: render headless |
| Meta Ad Library exige verificação | B1 travado | gate já existe; segue como item bloqueado até aprovação |
| Windsor confundido com fonte fria | construir errado | papel fixado: SÓ pós-conversão; documentado aqui e na memória |
| Reboot derruba stack | "banco sumiu" | `start.sh` Docker; opção `restart: unless-stopped` (a decidir) |

---

## 6. Rollback

- **Track A**: cada correção é isolada por arquivo; reverter = `git revert` do commit.
  A4 (a mais arriscada) fica atrás de flag de fonte → desligar sem revert.
- **Track B**: tudo atrás de `ENABLE_*` → desligar a flag desabilita a fonte na hora.
- **Migrations**: cada uma com `downgrade()` testado.

---

## 7. Checklist de execução (vivo)

**Fase 0** — [x] tudo concluído.
**Fase 1 (Track A)** — ordem: A2 → A1 → A3 → A4 → A5 → migration nullable + testes.
**Fase 2 (Track B)** — B1 (após verificação) · B2 · B3 (pós-conversão) · B4 (OpenWA Gateway, cliente próprio).
**Fase 3** — dossiê consolidado → gerador de proposta → loop Windsor.

**Regra Ugarit:** nada implementado sem spec aprovada. Fase 1 já tem spec
([[spec-track-a-precisao]]). Fase 2/3 ganham spec própria antes de codar.
