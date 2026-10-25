---
name: frontend-ugarit-ui
versao: 1.5.2
data: 2026-08-09
projeto: kothar
tipo: habilidade
status: validada
descricao: Frontend modular de nível de agência — Next.js v14+ (App Router) + Co-localização por Funcionalidades + Acessibilidade + Performance + pt-BR obrigatório + Paleta Adaptativa + Dashboards Premium
---

# 🎨 FRONTEND UGARIT v1.5.2 (Estética Premium e Identidade Visual)

> **Função:** Criar interfaces limpas, acessíveis, de altíssimo padrão estético (Premium) e sem redundâncias estruturais, seguindo o padrão da Ugarit Digital. **A regra de PT-BR é INEGOCIÁVEL** para todos os termos customizados do projeto.

---

## 🎨 1. Identidade Visual e Paletas Adaptativas por Projeto

O Kothar **NUNCA** deve inventar combinações de cores aleatórias do zero ou assumir que existe apenas uma paleta genérica. A interface deve ser visualmente consistente com o projeto ativo:

1. **Investigar o Projeto Ativo**:
   - Antes de criar ou alterar qualquer tela, o Kothar deve ler as variáveis de estilo globais do projeto (ex: `globals.css`, `tailwind.config.js`, ou arquivos de tema) para entender a paleta e os tokens já definidos.
2. **Definição de Novas Paletas**:
   - Se for um projeto novo ou sem cores definidas, o Kothar deve verificar se existe uma paleta específica na pasta de design `/home/bruno-harkin/Cofre/.paletas/[nome-projeto]/` e ler as cores de `paleta.html` ou `identidade-final.html`.
   - Caso nenhuma paleta seja encontrada, o Kothar deve propor uma paleta minimalista de alto nível ao usuário e esperar aprovação antes de codificar.

---

## 🚫 2. Regras Rígidas de Temas e Contraste (Claro/Escuro)

Para evitar quebras visuais e elementos ilegíveis (como texto branco sobre fundo branco), siga rigorosamente as diretrizes de contraste:

### A. Tema Escuro (Dark Mode — Padrão)
*   **Fundo Geral**: Deve ser escuro profundo (ex: `#010204`, `#0B0F1C` ou equivalentes do projeto).
*   **Superfícies (Cards, Modais, Containers)**: Devem usar tons de azul profundo semi-transparentes ou cinzas muito escuros (nunca fundos claros).
*   **Restrição do Branco Puro (`#FFFFFF`)**: O branco puro é restrito **exclusivamente a ícones, letras de destaque, títulos importantes e marcadores de estado ativo**. Todo o resto (textos secundários, bordas, divisórias) deve usar cores escuras ou opacas com baixa luminosidade para manter a estética luxuosa.

### B. Tema Claro (Light Mode)
*   **Fundo Geral**: Deve ser claro/branco puro (ex: `#FFFFFF` ou cinzas claros como `#F8FAFC`).
*   **Contraste de Elementos**: Todos os textos, ícones, contornos de botões e funções principais **devem usar cores escuras** (como `#010204`, cinza-chumbo `#1E293B` ou azul profundo).
*   **PROIBIDO**: NUNCA utilizar textos brancos, ícones brancos ou botões com baixo contraste sobre fundos claros. O botão ou texto deve ser perfeitamente legível.

---

## 📈 3. Dashboards Minimalistas e Animações Premium

O front-end não deve ser simplório ou estático. Ele deve impressionar visualmente no primeiro impacto (Wow Effect):

1. **Dashboard Minimalista e Moderno**:
   - Usar layouts limpos com grades bem distribuídas (`grid`, `flex`).
   - Implementar **Glassmorphism** (efeito vidro fosco) usando classes do Tailwind como `backdrop-blur-md bg-white/5` ou `bg-black/40` com bordas ultra-finas semi-transparentes (`border-white/10`).
   - Manter as bordas dos cards totalmente alinhadas e com proporções geométricas limpas.
2. **Micro-interações e Linhas Animadas**:
   - Usar efeitos hover de iluminação (gradiente de borda que segue o cursor ou brilha na interação).
   - Adicionar barras de progresso animadas, loaders sutis e transições suaves de página utilizando **GSAP** (ScrollTrigger, timelines) ou CSS transitions nativas.
3. **Gráficos Ilustrativos e Otimizados**:
   - Evitar tabelas sem graça para expor dados visuais importantes. Usar gráficos dinâmicos e ilustrativos.
   - Utilizar a biblioteca **Recharts** (ou Chart.js) configurada com:
     - Linhas finas curvas com gradiente sob a área da linha (`defs` com gradientes lineares de opacidade decrescente).
     - Pontos em destaque brilhantes (usando filtros de sombra `filter="url(#glow)"`).
     - Efeitos de entrada de animação suave ao carregar o dashboard.

---

## 📦 4. Ícones e Emojis Profissionais

*   **PROIBIDO**: NUNCA usar emojis informais estilo WhatsApp (como 🚀, 🎨, ⚠️, 🔴, 🟢) em botões, menus, títulos ou notificações de dashboards profissionais.
*   **PERMITIDO**: Usar estritamente ícones vetorizados da biblioteca **Lucide React** (ou equivalentes SVG).
*   **Indicadores de Status**: Para estados (ex: Online, Sucesso, Pendente), criar pequenos círculos HTML com bordas e efeitos de pulso de luz (`animate-pulse`) usando cores adequadas (verde, amarelo, vermelho), em vez de usar emojis de bolinhas coloridas (como 🟢 ou 🔴).

---

## 🧪 5. Estratégia de Testes do Frontend

1. **Testes Unitários / Lógica**:
   - Usar **Vitest** para testar utilitários funcionais e custom hooks locais da feature.
2. **Testes E2E (Fim a Fim)**:
   - Usar **Playwright** para garantir que fluxos cruciais da tela (login, envio de dados, navegação entre abas do dashboard) funcionam sem erros.

---

## 📁 Estrutura de Diretórios Modular (Inspirado em `bulletproof-react`)

Organizar o projeto **por funcionalidade (features)** em vez de tipos técnicos para evitar acúmulo de arquivos soltos:

```
frontend/                            ← Raiz do Frontend
├── app/                             ← Rotas e Páginas (App Router)
│   ├── (privado)/
│   │   ├── painel/
│   │   │   └── page.tsx             ← Server Component (Página)
│   │   │   └── loading.tsx          ← Skeleton loader específico
│   │   └── configuracoes/
│   ├── api/                         ← Handlers de rotas de API globais
│   ├── layout.tsx                   ← Layout raiz do sistema
│   └── globals.css                  ← CSS global (Tailwind)
│
├── funcionalidades/                 ← Diretório Modular de Features
│   ├── [nome-funcionalidade]/       ← Ex: autenticacao, painel, contatos, disparos
│   │   ├── api/                     ← Chamadas de API e Server Actions locais
│   │   ├── componentes/             ← Componentes exclusivos da feature (gráficos, formulários)
│   │   ├── hooks/                   ← Custom Hooks da feature
│   │   ├── tipos/                   ← Interfaces TypeScript da feature
│   │   ├── utils/                   ← Utilitários locais
│   │   └── testes/                  ← Testes locais da feature (Vitest / Playwright)
│   
├── componentes-globais/             ← Componentes estruturais reusados em todo o projeto
│   ├── ui/                          ← Elementos base do shadcn/ui (Button, Input, etc.)
│   └── layout/                      ← Componentes de navegação estrutural (header, sidebar)
```
