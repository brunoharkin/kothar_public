# Trace Page — Kothar v3.0

Página de análise de traces para visualização de Input/Output.

## Estrutura

```
trace/frontend/paginas/trace/
├── trace.page.tsx     # Componente principal
├── trace.styles.css   # Estilos (dark theme)
└── trace.types.ts     # Tipos TypeScript
```

## Funcionalidades

- [x] **Modo Chat**: Visualização em formato de conversa com Input/Output lado a lado
- [x] **Modo Tabela**: Visualização em tabela com ID, Tool, Status, Duration
- [x] **Sidebar de Detalhes**: Painel lateral com JSON completo do trace selecionado
- [x] **Syntax Highlighting**: Cores para JSON (keys, strings, numbers, booleans)
- [x] **Responsivo**: Adapta-se para mobile

## Uso

```tsx
import { TracePage } from './trace.page';

function App() {
  return <TracePage />;
}
```

## Visual

### Modo Chat
```
┌─────────────────────────────────────────────────────────┐
│ [Read] ● 18:45:00 • 120ms                              │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────┐        │
│ │ 📥 Input            │ │ 📤 Output           │        │
│ │ {                   │ │ {                   │        │
│ │   "file_path": ...  │ │   "content": "..."  │        │
│ │ }                   │ │ }                   │        │
│ └─────────────────────┘ └─────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Modo Tabela
```
┌──────┬──────┬────────┬──────────┬────────────┐
│ ID   │ Tool │ Status │ Duration │ Timestamp  │
├──────┼──────┼────────┼──────────┼────────────┤
│ tr-001│ Read │ ●      │ 120ms    │ 18:45:00  │
└──────┴──────┴────────┴──────────┴────────────┘
```

## Próximos Passos

- [ ] Integrar com API real de traces
- [ ] Adicionar filtros por tool/data
- [ ] Implementar busca de traces
- [ ] Adicionar exportação JSON/CSV

---
*Ugarit Digital — Kothar v3.0*
