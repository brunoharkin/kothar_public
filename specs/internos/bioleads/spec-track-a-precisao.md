---
tipo: spec
produto: bioleads
track: A — Precisão
status: aguardando-aprovação
autor: Kothar
data: 2026-06-01
---

# Spec — Track A: Precisão do Enriquecimento (BioLeads)

← [[bioleads]]

## 1. Problema

O BioLeads **registra dado vazio/errado como verdade**. Ao conferir manualmente,
Bruno encontra divergência constante: marca "sem site" quando tem, "sem email"
quando o email está na página, "sem pixel" quando o pixel existe. Isso destrói a
confiança no produto e inviabiliza o objetivo final (gerar dossiê comercial e
proposta a partir dos dados).

**Causa raiz: falha de coleta é tratada como ausência de dado.** Quando o scraper
não consegue ler o site (403, JS, timeout), o pipeline grava `False`/vazio em vez
de "desconhecido". A validação de email apaga emails válidos quando o DNS é
inconclusivo. A ordem de descoberta prioriza a fonte mais ruidosa (Brave web)
sobre a estruturada (Google Places).

## 2. Objetivo

Fazer o BioLeads **só afirmar o que de fato verificou**. Quando não conseguir
verificar, deve dizer "não verificado" — nunca "não tem". Subir a precisão dos
campos críticos (site, email, telefone, pixel, nome/identidade) usando as APIs
que já existem, sem nova infraestrutura.

## 3. Escopo (5 correções)

### A1 — Scraper robusto, falha ≠ ausência
**Arquivo:** `backend/app/integrations/site_scraper.py`, `enrichment_tasks.py`

- `_fetch_html` ([site_scraper.py:120](../../../../bioleads/backend/app/integrations/site_scraper.py#L120))
  hoje só aceita HTTP 200 e retorna `None` em qualquer falha.
- Mudanças:
  - Retry com 2º User-Agent (mobile/bot-tolerante) e backoff curto.
  - Tratar 403/429 com retry; seguir até `max_redirects=5`.
  - Distinguir três estados de fetch: **ok**, **bloqueado/inacessível**,
    **inexistente**. Retornar `fetch_status` no dict.
- No pipeline ([enrichment_tasks.py:60-119](../../../../bioleads/backend/app/tasks/enrichment_tasks.py#L60-L119)):
  - Quando `fetch_status != "ok"`, **NÃO** gravar `has_pixel=False`,
    `has_gtag=False` etc. Deixar como `None` (= desconhecido) e registrar
    `_src` / motivo em `google_services["_site_fetch"]`.
  - Booleans de pixel passam a ser tri-state (True / False / None) na leitura.

**Aceite A1:**
- Site que devolve 403 na 1ª tentativa e 200 na 2ª → dados extraídos.
- Site genuinamente fora do ar → `has_pixel=None` (não `False`) e card mostra
  "site não verificado", não "sem pixel".

### A2 — Não apagar email quando o MX é inconclusivo
**Arquivo:** `backend/app/integrations/email_validator.py`, `enrichment_tasks.py`

- Hoje, timeout/erro de DNS retorna `has_mx=False`
  ([email_validator.py](../../../../bioleads/backend/app/integrations/email_validator.py))
  e a consolidação apaga o email
  ([enrichment_tasks.py:488-491](../../../../bioleads/backend/app/tasks/enrichment_tasks.py#L488-L491)).
- Mudanças:
  - `validate_email` passa a distinguir `has_mx: True | False | None`
    (None = não foi possível resolver). Campo novo `mx_checked: bool`.
  - Consolidação só apaga o email quando `is_valid_syntax=False` **ou**
    (`mx_checked=True` **e** `has_mx=False`). MX inconclusivo → **mantém** o
    email e marca `confidence="medium"`.

**Aceite A2:**
- Email sintaticamente válido com DNS em timeout → email **preservado**,
  `_email_validation.confidence="medium"`.
- Email de domínio comprovadamente sem MX → removido (comportamento atual).

### A3 — Decodificar email ofuscado
**Arquivo:** `backend/app/integrations/site_scraper.py`

- O regex atual ([site_scraper.py:74](../../../../bioleads/backend/app/integrations/site_scraper.py#L74))
  só pega email em texto cru.
- Adicionar, antes da extração:
  - Decode de Cloudflare email-protection (`data-cfemail="..."` → XOR decode).
  - Normalizar ofuscações comuns: `(arroba)`, `[at]`, ` at `, `(ponto)`, `[dot]`.
  - Capturar `mailto:` explicitamente (inclui querystring `?subject=`).

**Aceite A3:**
- Página com `data-cfemail` → email decodificado e extraído.
- Página com `contato (arroba) empresa.com.br` → `contato@empresa.com.br`.

### A4 — Descoberta: Places primário + merge, SEM Brave
**Arquivo:** `backend/app/integrations/google_search.py`

- Hoje a prioridade é Brave → `return` no 1º com resultado
  ([google_search.py:244-260](../../../../bioleads/backend/app/integrations/google_search.py#L244-L260)),
  ofuscando o Google Places (fonte estruturada/precisa).
- **Não usamos Brave.** Remover `_search_brave` (e os parsers `_parse_brave_*`) do fluxo.
- Mudança: `search_businesses` passa a:
  1. Rodar **Google Places (New)** como fonte primária quando houver chave.
  2. Rodar **Google CSE** como **complemento** (não substituto): mesclar por
     chave `nome_normalizado + telefone`, preenchendo lacunas — nunca
     sobrescrever campo estruturado do Places com dado raspado.
  3. **DuckDuckGo** permanece como fallback final (sem chave).
- Cadeia final: **Places → CSE → DDG**. Preservar teto de 50 e deduplicação por nome.

**Aceite A4:**
- Busca "dentista em Campinas" com chave Places → nomes oficiais do Maps,
  telefone nacional e endereço estruturado (não título de página quebrado).
- Nenhuma chamada ao Brave em nenhum caminho.
- Sem chave Places → cai para CSE → DDG.

### A5 — Transparência de confiança no card
**Arquivo:** frontend do detalhe do lead + leitura tri-state no backend

- Expor no card a diferença entre **"não verificado"** (fetch falhou / sem
  dado) e **"verificado: não tem"**. Usar os campos `_site_fetch`,
  `_email_validation`, `_src_*` já existentes em `google_services`.

**Aceite A5:**
- Card mostra badge "site não verificado" quando `_site_fetch != ok`.
- Campos com dado confirmado mostram a fonte (`Places`, `site`, `CNPJ`…).

## 4. Fora de escopo (vai pro Track B / outra spec)

- Meta Ad Library (Identity Verification) — "roda anúncio?".
- Consistência de postagem do prospect.
- Validação de número via OpenWA Gateway (mesma stack do disparo, cliente próprio — bioleads é independente do disparo).
- Dossiê → gerador de proposta.
- Windsor.ai (só faz sentido pós-conversão, quando o cliente conecta a conta).

## 5. Riscos / atenção

- **A4 muda comportamento de produção** da busca: validar com 2-3 nichos reais
  antes de subir. Custo Places sobe (mais chamadas) — aceitável pela precisão.
- A1/A2 são correções de bug de baixo risco (só param de apagar/falsear dado).
- Migration: os booleans de pixel viram nullable — checar schema/Alembic.

## 6. Plano de implementação (ordem)

1. A2 (email_validator + consolidação) — menor, isola o "email some".
2. A1 (fetch tri-state + pipeline não falseia) — base pra tudo.
3. A3 (ofuscação de email) — depende de A1.
4. A4 (ordem de descoberta) — maior, testar com nichos reais.
5. A5 (frontend de confiança) — fecha o ciclo de transparência.
6. Migration nullable nos flags de pixel (se necessário) + verificação.

## 7. Critério de pronto (Definition of Done)

- Conferência manual de 5 leads reais: nenhum campo "sem X" quando X existe.
- Quando a coleta falha, o card diz "não verificado" — nunca "não tem".
- Testes dos extratores (email ofuscado, MX inconclusivo, merge Places+Brave).
