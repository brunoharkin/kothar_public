---
name: scaffolding-ugarit
description: >-
  Gerador de boilerplate automático seguindo o padrão Ugarit (pastas em português, kebab-case, sem src/components/utils). Cria estrutura completa para nova página, endpoint, serviço ou componente com um comando.
---

# Skill: Scaffolding Ugarit (Gerador de Boilerplate)

> **Fonte:** Thariq (Anthropic): "Code Scaffolding Skills that generate framework boilerplate are especially useful when your scaffolding has natural language requirements that can't be purely covered by code."
> 
> **Padrão Ugarit:** Estrutura de pastas em português, sem nomes genéricos (`src`, `components`, `utils`), organizado por funcionalidade e não por tipo de arquivo.

---

## 🏗️ Padrão de Estrutura Ugarit

```
{projeto}/
├── frontend/
│   ├── paginas/
│   │   └── {nome-da-pagina}/
│   │       ├── {nome-da-pagina}.jsx    ← componente principal
│   │       ├── estilos.css             ← estilos específicos da página
│   │       └── logica.js               ← lógica da página (hooks, etc.)
│   └── componentes/
│       └── {nome-componente}/
│           ├── {NomeComponente}.jsx
│           └── estilos.css
├── backend/
│   ├── rotas/
│   │   └── {nome-rota}.js
│   ├── {servico}/
│   │   ├── {servico}.js                ← lógica principal
│   │   └── {servico}-validacao.js      ← validação
│   └── banco-de-dados/
│       └── {nome}-schema.js
└── features/                           ← planos RPI por feature
```

---

## 🛠️ Templates de Scaffolding

### Template: Nova Página Frontend

**Quando o Kothar receber:** "cria uma nova página de {nome}"

**Criar:**
```
frontend/paginas/{kebab-case-nome}/
├── {kebab-case-nome}.jsx
├── estilos.css
└── logica.js
```

**Conteúdo de `{nome}.jsx`:**
```jsx
// {nome}.jsx — {Descrição breve da página}
import React from 'react';
import './estilos.css';
import { usar{NomeCamelCase} } from './logica';

function {NomePascalCase}() {
  const { /* estado e handlers */ } = usar{NomeCamelCase}();

  return (
    <main className="{kebab-case}-pagina">
      <h1>{Título da Página}</h1>
      {/* conteúdo aqui */}
    </main>
  );
}

export default {NomePascalCase};
```

**Conteúdo de `logica.js`:**
```javascript
// logica.js — Hooks e lógica da página {nome}
import { useState, useEffect } from 'react';

export function usar{NomeCamelCase}() {
  // estado aqui
  
  return {
    // retornar estado e handlers
  };
}
```

**Conteúdo de `estilos.css`:**
```css
/* estilos.css — Estilos da página {nome} */

.{kebab-case}-pagina {
  /* estilos da página */
}
```

---

### Template: Novo Endpoint Backend

**Quando o Kothar receber:** "cria um endpoint de {recurso}"

**Criar:**
```
backend/{recurso}/
├── {recurso}.js          ← handlers
├── {recurso}-rotas.js    ← definição das rotas
└── {recurso}-validacao.js ← validação de entrada
```

**Conteúdo de `{recurso}-rotas.js`:**
```javascript
// {recurso}-rotas.js — Rotas do recurso {recurso}
const express = require('express');
const roteador = express.Router();
const { listar{Recurso}, buscar{Recurso}, criar{Recurso} } = require('./{recurso}');
const { validar{Recurso} } = require('./{recurso}-validacao');

roteador.get('/', listar{Recurso});
roteador.get('/:id', buscar{Recurso});
roteador.post('/', validar{Recurso}, criar{Recurso});

module.exports = roteador;
```

**Conteúdo de `{recurso}.js`:**
```javascript
// {recurso}.js — Lógica do recurso {recurso}

async function listar{Recurso}(req, res) {
  try {
    // lógica aqui
    res.json({ dados: [] });
  } catch (erro) {
    console.error(`[${Recurso}] Erro ao listar:`, erro.message);
    res.status(500).json({ erro: 'Erro interno do servidor' });
  }
}

async function buscar{Recurso}(req, res) {
  try {
    const { id } = req.params;
    // lógica aqui
    res.json({ dado: null });
  } catch (erro) {
    console.error(`[${Recurso}] Erro ao buscar:`, erro.message);
    res.status(500).json({ erro: 'Erro interno do servidor' });
  }
}

async function criar{Recurso}(req, res) {
  try {
    const dados = req.body;
    // lógica aqui
    res.status(201).json({ mensagem: 'Criado com sucesso', id: null });
  } catch (erro) {
    console.error(`[${Recurso}] Erro ao criar:`, erro.message);
    res.status(500).json({ erro: 'Erro interno do servidor' });
  }
}

module.exports = { listar{Recurso}, buscar{Recurso}, criar{Recurso} };
```

---

### Template: Novo Componente Reutilizável

**Quando o Kothar receber:** "cria um componente de {nome}"

**Criar:**
```
frontend/componentes/{NomePascalCase}/
├── {NomePascalCase}.jsx
└── estilos.css
```

---

### Template: Nova Integração/Serviço

**Quando o Kothar receber:** "integra com {servico-externo}"

**Criar:**
```
backend/{servico-externo}/
├── cliente-{servico-externo}.js    ← cliente HTTP/SDK
├── {servico-externo}-config.js     ← configurações (sem credenciais!)
└── README.md                        ← como configurar
```

**Credenciais → SEMPRE no `.env` do projeto, nunca no código**

---

## 📏 Regras de Nomenclatura

| Elemento | Formato | Exemplo |
|---|---|---|
| Pasta de página | kebab-case | `paginas/tela-de-login/` |
| Pasta de componente | PascalCase | `componentes/BotaoConfirmar/` |
| Arquivo JSX/TSX | PascalCase | `TelaLogin.jsx` |
| Arquivo JS lógica | kebab-case | `logica-login.js` |
| Arquivo CSS | kebab-case | `estilos.css` |
| Função/Hook | camelCase em português | `usarAutenticacao()` |
| Variável | camelCase em português | `dadosUsuario` |
| Constante | SNAKE_UPPER_CASE | `TEMPO_SESSAO` |

**Proibido:**
- `src/`, `components/`, `utils/`, `helpers/`, `lib/`, `assets/` como nome de pasta
- Nomes em inglês para pastas de funcionalidade
- Abreviações (exceto: id, url, api, cpf, cnpj, pix, qr, pdf)

---

## 🔗 Integração com o Kothar

- **Gate G5 (Nomenclatura):** Esta skill define os nomes antes do guard bloquear
- **analise-codigo.py:** Verifica nomenclatura como um dos critérios de score
- **RPI Workflow:** Scaffolding é a primeira ação do IMPLEMENT após o PLAN ser aprovado

*Skill criada em 2026-08-12 — Baseada no padrão Ugarit e na filosofia de Code Scaffolding Skills do time Anthropic*
