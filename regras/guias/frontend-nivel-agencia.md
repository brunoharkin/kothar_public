# GUIA: Desenvolvimento Frontend Nível Agência

> **Versão:** 1.0
> **Data:** 2026-06-25
> **Baseado em:** Setup 21st.dev + Framer Motion + Design System

---

## O Problema: "Site com Cara de IA"

O que separa um site de agência de um site gerado por IA:

| ❌ Site de IA | ✅ Site de Agência |
|---------------|-------------------|
| Gradientes em texto | Tipografia display com peso real |
| Cards idênticos em grid | Variedade de tamanhos e formatos |
| Blob de fundo | Superfícies planas + espaço |
| Hover com scale | Border reveal + shadow shift |
| Animações genéricas | Motion com propósito comunicativo |
| Cores azul/roxo padrão | Paleta única por projeto |

---

## As 4 Camadas do Setup

### Camada 1: Claude Code como IDE

```
✅ Lê o projeto inteiro
✅ Edita múltiplos arquivos simultaneamente
✅ Roda comandos em sequência
✅ Mantém contexto entre arquivos
```

### Camada 2: Sistema de Animação

**GSAP para marketing/landing:**
```bash
npm install gsap
```

**Framer Motion para React:**
```bash
npm install framer-motion
```

**Regras de timing:**
- Feedback: 100-150ms
- State change: 200-300ms
- Layout shift: 300-500ms
- Delight: < 1s

**Easing proibido:**
- ❌ `bounce.out` — parece brinquedo
- ❌ `elastic.out` — parece datado

**Easing correto:**
- ✅ `expo.out` — marketing
- ✅ `power2.out` — produto
- ✅ `power3.out` — transições

### Camada 3: Design System (Skill)

**Arquivo:** `/home/bruno/Cofre/.claude/skills/frontend-ugarit/SKILL.md`

Esta skill é **OBRIGATÓRIA** para qualquer projeto frontend.

**Tokens de cor (OKLCH):**
```css
:root {
  --brand: oklch(0.62 0.13 55);      /* âmbar editorial */
  --background: oklch(0.98 0.005 80); /* off-white quente */
  --foreground: oklch(0.15 0.008 80); /* near-black */
  --muted: oklch(0.94 0.003 80);
  --border: oklch(0.88 0.004 80);
}
```

**Hierarquia tipográfica:**
- Display: Fraunces, clamp(3.5rem, 9vw, 8rem)
- Headline: Fraunces, clamp(2rem, 4.5vw, 4rem)
- Body: Plus Jakarta Sans, 1.6 line-height
- Medida: max-width 65ch

### Camada 4: 21st.dev

Biblioteca de componentes prontos e bem desenhados.

**URL:** https://21st.dev

**Componentes disponíveis:**
- Heroes (múltiplos estilos)
- Pricing tables
- Testimonials
- Navbars
- Feature grids
- FAQ accordions

**Uso:**
1. Buscar componente desejado
2. Copiar código
3. Integrar no projeto
4. Adaptar ao design system

---

## Fluxo de Desenvolvimento

### 1. Shape (Aprovação de Direção)

Antes de codar, SEMPRE confirmar:

```
1. Tipo de projeto:
   □ Marketing/Landing
   □ SaaS/Produto
   □ Dashboard
   □ E-commerce
   □ Portfólio

2. Preset de fonte:
   □ studio (agências, design)
   □ luxury (premium, moda)
   □ tech (SaaS, startup)
   □ health (saúde, wellness)
   □ finance (fintech, jurídico)
   □ editorial (blog, conteúdo)

3. Cor de marca:
   □ Definir com cliente
   □ Sugerir 3 opções

4. Temperamento:
   □ Quente (serif, orgânico)
   □ Neutro
   □ Frio (geométrico)

5. Modo:
   □ Light-first
   □ Dark-first (com justificativa)
```

### 2. Setup do Projeto

```bash
# Criar projeto Next.js
npx create-next-app@latest meu-projeto --typescript --tailwind --app

# Instalar dependências
npm install framer-motion gsap
npm install -D @types/gsap

# Estrutura inicial
mkdir -p src/components/ui src/components/sections
```

### 3. Configuração do Design System

```tsx
// src/app/globals.css

:root {
  --brand: oklch(0.62 0.13 55);
  --background: oklch(0.98 0.005 80);
  --foreground: oklch(0.15 0.008 80);
  --muted: oklch(0.94 0.003 80);
  --border: oklch(0.88 0.004 80);
  --card: oklch(0.99 0.003 80);
}

.dark {
  --background: oklch(0.09 0.005 80);
  --foreground: oklch(0.95 0.005 80);
  --muted: oklch(0.18 0.005 80);
  --border: oklch(0.22 0.004 80);
  --card: oklch(0.12 0.005 80);
}
```

### 4. Componentes por Seção

**Navbar:**
```tsx
<Navbar 
  logo="Nome da marca"
  links={[{label: "Sobre", href: "#sobre"}]}
  cta="Começar"
/>
```

**Hero (ALINHADO À ESQUERDA):**
```tsx
<Hero
  eyebrow="Label da seção"
  headline="Headline em fonte display"
  subheadline="Texto de suporte com medida 65ch"
  ctaPrimary="CTA principal"
  ctaSecondary="Link secundário"
/>
```

**Features (SEM CARDS IDÊNTICOS):**
```tsx
<BentoGrid
  items={[
    {span: "col-span-2", ...},  // Feature grande
    {span: "col-span-1", ...},  // Features menores
    {span: "col-span-1", ...},
  ]}
/>
```

**Pricing:**
```tsx
<Pricing
  plans={[
    {name: "Básico", price: "R$99", features: [...]},
    {name: "Pro", price: "R$199", popular: true, features: [...]},
    {name: "Enterprise", price: "Sob consulta", features: [...]},
  ]}
/>
```

### 5. Animações por Contexto

**Marketing/Landing:**
```tsx
// Page load
gsap.from('.hero-content', {
  y: 40,
  opacity: 0,
  duration: 0.6,
  ease: 'expo.out',
  stagger: 0.1
})

// Scroll reveal
ScrollTrigger.create({
  trigger: '.section',
  start: 'top 80%',
  onEnter: () => gsap.to('.section-content', {
    y: 0,
    opacity: 1,
    duration: 0.6,
    ease: 'expo.out'
  })
})

// Hover em card
gsap.to('.card', {
  borderColor: 'var(--brand)',
  duration: 0.2
})
```

### 6. Checklist de Qualidade

**Antes de considerar "pronto":**

```
✅ Conteúdo real
   □ Sem "Lorem ipsum"
   □ Imagens com contexto correto
   □ Números específicos (não "100+")

✅ Semântica HTML
   □ <nav>, <main>, <section> corretos
   □ h1 único por página
   □ <button> para ações, <a> para links

✅ Estados
   □ Default
   □ Hover
   □ Focus (keyboard)
   □ Active
   □ Disabled
   □ Loading
   □ Empty
   □ Error

✅ Responsividade
   □ Mobile 375px
   □ Tablet 768px
   □ Desktop 1280px+

✅ Performance
   □ Imagens lazy-loaded
   □ Fontes com display: swap
   □ prefers-reduced-motion

✅ Acessibilidade
   □ Contraste 4.5:1 mínimo
   □ aria-labels em ícones
   □ Tab order lógico
```

---

## Padrões Anti-IA (PROIBIDOS)

```
❌ text-gradient (bg-clip-text)
❌ Blob/orb de fundo
❌ Badge com ✨ no hero
❌ Cores #6366f1, #8b5cf6
❌ rounded-full em cards
❌ font-bold tracking-tight em headings
❌ Trusted by com logos cinza
❌ Hero centrado com blob
❌ Grid com 3 cards idênticos
❌ Side-stripe border
❌ Hero-metric (números decorativos)
❌ Glassmorphism em cards
❌ Emoji na interface
❌ Loading "carregando..."
```

---

## Como Usar Este Guia

1. **Invoke a skill frontend-ugarit** automaticamente quando:
   - Usuário pede "criar site"
   - Usuário pede "criar landing page"
   - Usuário pede "criar frontend"

2. **Siga o fluxo Shape → Setup → Build → Quality**

3. **Use 21st.dev** para componentes complexos

4. **Aplique as leis de design** em cada decisão

5. **Teste no browser** antes de declarar pronto

---

## Referências

- Skill: `/home/bruno/Cofre/.claude/skills/frontend-ugarit/SKILL.md`
- 21st.dev: https://21st.dev
- GSAP: https://gsap.com/docs
- Framer Motion: https://www.framer.com/motion/
