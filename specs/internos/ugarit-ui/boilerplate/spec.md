---
feature: ugarit-ui-boilerplate
projeto: ugarit-ui
tipo: interno
criado: 2026-05-24
status: aprovado
---

# Spec: Ugarit UI — Boilerplate de Frontend de Agência

## Descrição
Template Next.js reutilizável para a Ugarit Digital criar desde landing pages simples até SaaS completos com qualidade de agência.

## Cenários de Uso

- **Cenário 1 — Site simples**: Cliente pede landing page de 1 página. Desenvolvedor usa o template, troca textos, cores e imagens, faz deploy em 1 dia.
- **Cenário 2 — SaaS**: Produto interno precisa de dashboard + autenticação + landing. Desenvolvedor parte do boilerplate com todas as peças prontas.
- **Cenário 3 — Campanha**: Landing page de campanha com animações GSAP e seções modulares montadas sob demanda.

## Requisitos Funcionais

### Stack obrigatória
- Next.js 15 (App Router) + React 19 + TypeScript estrito
- Tailwind CSS 4 com design tokens centralizados
- shadcn/ui como base de componentes
- GSAP (todos os plugins gratuitos) + @gsap/react para animações
- Framer Motion para transições de página e microinterações

### Design System
- Tokens de cor semânticos (brand, neutral, success, warning, error)
- Tipografia: Geist Sans + Geist Mono (variáveis CSS)
- Escala de espaçamento consistente
- Dark mode nativo (CSS variables + next-themes)
- Modo responsivo: mobile-first, breakpoints: sm/md/lg/xl/2xl

### Componentes de Landing Page
- `Navbar` — fixa, blur no scroll, menu mobile com drawer
- `Hero` — headline animada (SplitText GSAP), CTA duplo, background com efeito
- `BentoGrid` — grade de features com cards animados no scroll
- `Features` — lista de features com ícones e descrições
- `Pricing` — planos com toggle mensal/anual, highlight do plano recomendado
- `FAQ` — accordion com animação suave
- `Footer` — links, social, copyright

### Componentes de Dashboard SaaS
- `Sidebar` — colapsável, navegação por ícone+label, indicador de rota ativa
- `DashboardHeader` — título da página, breadcrumb, ações, avatar
- `DataTable` — tabela com sorting, filtros, paginação (TanStack Table)
- `StatsCards` — cards de métricas com variação percentual
- `EmptyState` — estado vazio padronizado

### Animações GSAP (componentes reutilizáveis)
- `ScrollReveal` — revela elementos ao entrar no viewport
- `TextSplit` — anima palavras ou letras individualmente
- `Parallax` — efeito parallax no scroll (ScrollTrigger)
- `CountUp` — contador animado para métricas
- `MagneticButton` — botão com efeito magnético (mouse proximity)

### Estrutura de Projeto
- `src/app/(marketing)/` — rotas de landing/site
- `src/app/(dashboard)/` — rotas de SaaS autenticado
- `src/components/marketing/` — seções de landing
- `src/components/dashboard/` — componentes de SaaS
- `src/components/animations/` — wrappers GSAP reutilizáveis
- `src/components/ui/` — shadcn base components
- `src/lib/animations/` — presets e utilitários GSAP
- `src/styles/globals.css` — tokens CSS + Tailwind base

## Critérios de Sucesso

- [ ] `npm run dev` funciona sem erros
- [ ] Landing page completa renderiza com todas as seções
- [ ] Dashboard skeleton renderiza com sidebar + header + conteúdo
- [ ] Animações GSAP funcionam em scroll sem travar (60fps)
- [ ] Dark mode funciona em todas as páginas e componentes
- [ ] Build de produção sem erros TypeScript
- [ ] 100% responsivo (mobile + tablet + desktop)

## Localização
`/home/bruno/ugarit-ui/`

## Entidades-chave
- `UgaritUI` — o template em si
- `DesignTokens` — variáveis CSS de cor/tipografia/espaçamento
- `MarketingComponents` — seções de landing reutilizáveis
- `DashboardComponents` — UI de SaaS
- `GSAPAnimations` — wrappers de animação reutilizáveis
