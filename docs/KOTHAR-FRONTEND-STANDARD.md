# 🏛️ KOTHAR FRONTEND GOLD STANDARD (Padrão Ouro UI/UX) - v2.0 (Open-Design Data-Heavy)

Este documento é a **DIRETRIZ MESTRA ABSOLUTA** para todos os agentes Kothar ao construir ou refatorar interfaces (React/Next/Vite). As regras aqui descritas são inspiradas nos padrões matemáticos de design de nível global, especificamente fundindo a precisão do **Linear App**, a invisibilidade estrutural da **Vercel** e a engenharia de componentes do **Shadcn**.

Qualquer interface que não siga estas regras será considerada falha.

---

## 1. Regra Zero: Estética "Data-Heavy"
O frontend da Kothar é construído para desenvolvedores, arquitetos e engenheiros de dados. A interface deve ser **séria, matemática e focada na leitura e densidade de informação**.

**O QUE É TOTALMENTE PROIBIDO:**
- Temas "Cyberpunk" ou "Neon" (brilhos excessivos, roxo e rosa choque, verde-limão piscante).
- Componentes flutuantes em bolhas gigantes, bordas exageradas (>12px radius para botões/cards comuns).
- Estilo genérico de IA (gradientes complexos em tudo).
- Contrastes violentos (branco puro #FFFFFF sobre preto puro #000000).

---

## 2. Tipografia (A Engenharia das Letras)
A tipografia deve parecer "compilada e otimizada", não apenas "desenhada".

### Fontes Permitidas
- **Primária:** `Geist Sans` ou `Inter Variable`.
- **Secundária / Código:** `Geist Mono` ou `Berkeley Mono`.
- **Ligaduras (Obrigatório):** Ativar suporte a ligaduras (`"liga", "cv01", "ss03"` no Inter) para criar glifos perfeitamente conectados e estruturados.

### A Regra do Tracking Negativo (Letter Spacing)
- **Cabeçalhos (Display / H1 - 32px a 72px):** Obrigatório uso agressivo de `letter-spacing` negativo (Exemplo: `-1.58px` a `-2.88px`). Isso cria blocos de texto densos e imponentes, similares à interface da Vercel e Linear.
- **Textos Secundários / Body (14px a 16px):** `letter-spacing` normal. Foco máximo em legibilidade.

### Pesos (Font-Weights) Exatos
- `400` (Regular): Textos de parágrafos longos, logs, tabelas normais.
- `500` / `510`: **O peso assinatura da Kothar.** Usar em labels de UI, links, botões e navegação. Cria sutileza sem o peso agressivo do bold.
- `600` (Semi-bold): Apenas cabeçalhos e títulos.
- *NUNCA usar peso 700, 800 ou 900* exceto em micro-badges (10px).

---

## 3. Sombras, Bordas e O Modelo de "Border-as-Shadow"

O design padrão CSS (`border: 1px solid cor`) está **banido** para containers e cards modernos. 
A Kothar adota o sistema da **Vercel de Shadow-as-Border** para garantir renderização perfeita.

### O Método Vercel/Linear
Ao invés de:
`border: 1px solid rgba(255,255,255,0.08);`

Use:
`box-shadow: 0px 0px 0px 1px rgba(255, 255, 255, 0.08);`

- **Sombra de Cartão Data-Heavy Padrão:**
  `box-shadow: rgba(0,0,0,0.08) 0px 0px 0px 1px, rgba(0,0,0,0.04) 0px 2px 2px, inset 0px 0px 0px 1px rgba(255,255,255,0.02);`
  Isso gera uma borda perfeita de 1px com uma profundidade ambiente levíssima e um anel interno de iluminação imperceptível.

### Raios (Border Radius) Matemáticos
- **Micro (2px):** Badges, tags pequenas e botões de toolbar.
- **Card/Input (6px a 8px):** O padrão absoluto para botões primários, caixas de busca e formulários.
- **Painéis (12px):** Módulos principais e containers de tela.
- **Full Pill (9999px):** Apenas status chips (Ex: [Online]).

---

## 4. O Sistema de Cores Acromático

A interface é construída nas sombras, onde a cor é usada apenas como semântica de alerta, não como decoração.

### Escala de Fundo (Dark Mode Padrão)
- **Marketing Black:** `#08090a` (Fundo global da página / O vazio).
- **Panel Dark:** `#0f1011` (Módulo de sidebar, áreas isoladas).
- **Surface Elevation:** `#171717` a `#191a1b` (Cartões e botões escuros).

### Escala de Texto (Contraste Suave)
- **Texto Primário:** `#f7f8f8` (Nunca branco puro, para evitar fadiga ocular).
- **Texto Secundário / Body:** `#d0d6e0` ou `#a1a1aa` (Cinza claro, neutro).
- **Texto Terciário / Muted:** `#62666d` ou `#71717a` (Para metadados, links inativos e timestamps).

### A Cor de Destaque
- **Brand Indigo/Blue:** `#5e6ad2` ou `#0070f5`. Usada com parcimônia absoluta e clínica apenas em Calls-to-Action reais.
- **Workflow / Status:** 
  - Verde de Sucesso: `#10b981`
  - Vermelho de Erro/Ship: `#ff5b4f` ou `#ef4444`

---

## 5. Micro-Interações (Velocidade e Respeito)
- **Tempo e Curva:** Transições devem durar entre `150ms` e `200ms` usando `ease-out`. 
- **Efeitos de Hover:** Opacidade ou intensificação leve do fundo transparente (`rgba(255,255,255,0.02) -> 0.05`).
- **Animações Elásticas (Bouncy):** Proibidas. Dados não pulam. Dados se atualizam.

---

## 6. Filosofia do Vazio (Whitespace)
O fundo preto `#08090a` é o canvas. Margens e paddings não separam elementos, eles isolam informações.
- Use a escala de **8px** matematicamente: `4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px`.
- Não use divisores visuais maciços (linhas cinzas grossas). O espaço vazio deve atuar como separador natural de blocos de informação.
