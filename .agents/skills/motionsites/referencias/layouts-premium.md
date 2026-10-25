# 🏛️ Banco de Referências de Layouts — MotionSites & Ugarit Digital

Catálogo arquitetural de layouts modernos de alta conversão, bento grids e seções estruturadas para uso no ecossistema Ugarit Digital.

---

## 1. Hero Sections de Alto Impacto

### Padrão A: "Dark Luxury Minimalist" (SaaS & Agências)
- **Composição:**
  - Badge flutuante centralizado no topo com borda sutil e gradiente radial: `pill-badge` com status pulse (`bg-emerald-500/10 text-emerald-400 border-emerald-500/20`).
  - H1 com tipografia forte, tracking apertado (`tracking-tight`), palavras-chave com gradiente metálico ou de alto contraste (`from-white via-zinc-200 to-zinc-500`).
  - Parágrafo de apoio em 2 linhas com `text-zinc-400 max-w-2xl text-lg`.
  - Grupo de CTAs: Botão Primário sólido luminoso com brilho sutil + Botão Secundário outline com efeito backdrop-blur.
  - Mockup / Terminal / Preview interativo centralizado logo abaixo, cortado suavemente por máscara de fade inferior (`mask-image: linear-gradient(...)`).

### Padrão B: "Split Hero com Terminal / Live Agent"
- **Composição:**
  - 50% Coluna Esquerda: Proposta de valor clara, prova social (logos de clientes em grayscale opaco), campo de captura ou CTA imediato.
  - 50% Coluna Direita: Container interativo ativo (ex: terminal de teste do agente, calculadora dinâmica ou demonstração em tempo real).

---

## 2. Bento Grids de Funcionalidades (Padrão 2026)

Em vez de colunas de cards idênticas e monótonas:
- **Grid Asimétrica de 3 ou 4 Colunas:**
  - **Card 1 (Grande, 2 cols, 2 rows):** Visualização interativa da feature principal com animação contínua (ex: fluxo de automação, canvas de IA).
  - **Card 2 (Médio, 1 col, 2 rows):** Métrica em tempo real ou visualização de dados (contador animado com sparkline).
  - **Card 3 (Largo, 2 cols, 1 row):** Integrações (logos conectados por fios animados em SVG/Canvas).
  - **Card 4 (Compacto, 1 col, 1 row):** Badge de segurança ou selo com micro-interação ao passar o mouse.
- **Estilo Visual:**
  - Fundo: `bg-zinc-950/60` com `backdrop-blur-md`
  - Borda: `border border-zinc-800/80 hover:border-zinc-700 transition-colors duration-300`
  - Spotlight Effect: Gradiente radial seguindo o cursor do mouse.

---

## 3. Pricing Tables com Foco em Decisão

- **Estrutura de 3 Planos:**
  - Plano Recomendado / Destaque elevado com anel luminoso (`ring-1 ring-emerald-500/50 shadow-2xl shadow-emerald-500/10`).
  - Toggle de ciclo de cobrança (Mensal / Anual) com desconto claro indicado por badge animado.
  - Lista de features com ícones de check SVG minimalistas (sem emojis amadores).
  - Escopo explícito: sem ambiguidade no que está incluso e piso de investimento.

---

## 4. Modais de Conversão & Diagnóstico

- Fundo com overlay de escurecimento profundo (`bg-black/80 backdrop-blur-sm`).
- Container modal centralizado com animação de scale e fade (`scale-95 opacity-0` para `scale-100 opacity-100` em 200ms).
- Formulários com labels flutuantes ou em cima dos inputs com foco iluminado (`ring-1 ring-zinc-400`).
- Sem scroll desnecessário: tudo visível em uma única viewport desktop.

