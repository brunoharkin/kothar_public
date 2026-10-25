# ⚡ Banco de Referências de Motion Design & Micro-Interações

Catálogo de curvas de animação, tokens de easing e padrões de micro-interações para interfaces com acabamento Awwwards/Motion UI.

---

## 1. Tokens de Curvas de Easing (Bézier Padrão)

```css
:root {
  /* Entrada elegante (Ultra Smooth) */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  
  /* Movimento fluido natural (Apple / Stripe style) */
  --ease-spring: cubic-bezier(0.25, 1, 0.5, 1);
  
  /* Saída rápida e responsiva */
  --ease-in-out-smooth: cubic-bezier(0.65, 0, 0.35, 1);
  
  /* Micro-interação de clique e hover */
  --ease-bounce-subtle: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 2. Micro-Interações Obrigatórias em Componentes

### A. Botões Primários com Efeito Magnético / Brilho
- **Hover:**
  - Leve expansão: `transform: scale(1.02);`
  - Gradiente radial interno ou border shine seguindo a luz: `border-color: rgba(255, 255, 255, 0.3);`
- **Active (Clique):**
  - Contração táctil rápida: `transform: scale(0.98); duration: 100ms;`

### B. Cards Interativos com Spotlight
- Background escuro com opacidade controlada.
- Ao passar o mouse, um círculo suave de gradiente radial de 250px ilumina a borda e o fundo:
  `background: radial-gradient(300px circle at var(--mouse-x) var(--mouse-y), rgba(255,255,255,0.06), transparent 80%);`

### C. Staggering de Listas e Grids
- Quando elementos entram em cena (Cards, Itens de menu, Badges):
  - Delay progressivo de `40ms` entre cada item sucessivo (`transition-delay: calc(var(--index) * 40ms)`).
  - Impede que todos os elementos apareçam ao mesmo tempo de forma dura.

---

## 3. Padrões de Framer Motion Recomendados

```typescript
// Fade In Up com Curva Suave
export const animacaoEntrada = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] }
};

// Transição de Container Stagger
export const containerStagger = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1
    }
  }
};
```

---

## 4. Diretriz de Desempenho e Acessibilidade

- Animar EXCLUSIVAMENTE propriedades aceleradas por GPU: `transform` e `opacity`.
- NUNCA animar `width`, `height`, `margin`, `top`, `left` (causam reflow/relayout e travam FPS).
- Respeitar sempre:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```

