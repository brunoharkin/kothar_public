---
name: amarracao-logica
description: >-
  Mapa completo de fluxo de dados conectando frontend ↔ backend ↔ DB ↔ UX. Sem buraco. Sem botão sem função. Sem feature quebrada. Aplicado em CADA feature antes de implementar.
---

# Skill: Amarração Lógica

> **Bruno foi explícito:** "nada pode ser criado e corrigir modificado sem ter a amaraacao completa da logica... o erro mais comum é eu manda ele cria algo e ele nao amarra a logica cria botoes sem fucoes logica quebrada desdo backend ao frontend nao pode ter erro"
>
> "o agente tem que pensar tanto na parte de desenvolvimento quanto na parte do usuario a experiencia do usuario nao pode ter erro"

---

## 🔴 A Regra (em uma frase)

**Antes de implementar QUALQUER feature, Kothar gera o mapa de amarração lógica: frontend ↔ backend ↔ DB ↔ UX. Sem buraco. Sem botão sem função. Sem feature quebrada.**

---

## 📋 Template do Mapa de Amarração

### Frontend → Backend
| Ação do usuário | Componente | Chama | Resultado visível |
|---|---|---|---|
| Clica "Salvar" | `FormularioX` | `POST /api/x` | Toast + redirect |
| Faz login | `TelaLogin` | `POST /api/auth` | Token + redirect |
| Lista items | `ListaY` | `GET /api/y` | Render cards |
| Edita item | `ModalEdicao` | `PATCH /api/y/:id` | Fecha modal + atualiza lista |
| Deleta item | `BotaoDeletar` | `DELETE /api/y/:id` | Confirma + remove da lista |

### Backend → DB
| Endpoint | Valida | Persiste | Retorna | Erros |
|---|---|---|---|---|
| `POST /api/x` | schema Zod | INSERT tabela_x | `{ id, ... }` | 400 (input), 401 (auth), 500 (db) |
| `GET /api/y` | auth + query | SELECT tabela_y | `[{ id, ... }]` | 401, 500 |
| `PATCH /api/y/:id` | schema + auth | UPDATE | `{ id, ... }` | 400, 401, 404, 500 |
| `DELETE /api/y/:id` | auth | DELETE | `{ ok: true }` | 401, 404, 500 |

### DB Schema
| Tabela | Campos | Relacionamentos |
|---|---|---|
| `usuarios` | id, email, password_hash, tenant_id | 1:N com `documentos` |
| `documentos` | id, titulo, conteudo, user_id | N:1 com `usuarios` |
| `tags` | id, nome, tenant_id | N:N com `documentos` |

### UX (fluxo do usuário)
1. **Estado inicial:** Usuário acessa `/x` → vê lista vazia + botão "Criar"
2. **Ação 1:** Clica "Criar" → modal abre com formulário
3. **Ação 2:** Preenche + clica "Salvar" → loading aparece no botão
4. **Loading:** Botão fica disabled + spinner, formulário fica disabled
5. **Sucesso:** Modal fecha + toast verde + item aparece na lista
6. **Erro validação:** Mensagem inline no campo específico (não toast)
7. **Erro servidor:** Toast vermelho + formulário volta a ficar editável + log do erro
8. **Estado vazio:** "Nenhum item ainda. Crie o primeiro." (não tela em branco)

---

## 🎯 Como aplicar (workflow)

### Passo 1: Bruno pede feature
Ex: "cria página de login"

### Passo 2: Kothar verifica pedido
"Pedido: login"

### Passo 3: Kothar GERA mapa de amarração ANTES de codar

```markdown
📋 **Feature: Login**

🧠 **Lógica amarrada:**

**Frontend → Backend:**
| Ação | Componente | Chama | Resultado |
|---|---|---|---|
| Submete form | `TelaLogin` | `POST /api/auth/login` | Token + redirect `/dashboard` |
| Esqueceu senha | `LinkEsqueciSenha` | `POST /api/auth/reset` | E-mail enviado |

**Backend → DB:**
| Endpoint | Valida | Persiste | Retorna | Erros |
|---|---|---|---|---|
| `POST /api/auth/login` | email + password | none (read) | `{ token, user }` | 401 (credenciais) |

**DB Schema:**
- Tabela `users`: id, email, password_hash, created_at

**UX:**
1. Usuário vê form: email + senha + botão "Entrar" + link "Esqueci"
2. Clica "Entrar" → loading no botão
3. Sucesso: redirect pra `/dashboard`
4. Erro: mensagem inline "E-mail ou senha incorretos"
5. Esqueci senha: pede e-mail → tela de confirmação
```

### Passo 4: Bruno aprova ou ajusta

### Passo 5: SÓ AGORA Kothar implementa

**Implementação segue EXATAMENTE o mapa. Sem criar botão novo que não está no mapa. Sem mudar UX que não foi aprovado.**

---

## 🔴 Comportamento PROIBIDO

- ❌ Criar botão sem handler (botão morto)
- ❌ Criar endpoint sem frontend que chama
- ❌ Criar tabela sem UI que usa
- ❌ Implementar UX diferente do que foi combinado
- ❌ Pular etapa "mapa de amarração" e ir direto pro código
- ❌ Inventar campos de formulário sem perguntar

---

## 🛠️ Auto-correção

Se Bruno disser:
- "esse botão não funciona" → Kothar volta no mapa, vê o que faltou
- "a UX tá quebrada" → Kothar re-define o fluxo de estados
- "tem campo que não foi pedido" → Kothar remove (princípio do menor escopo)
- "faltou validação no backend" → Kothar adiciona no mapa e implementa

---

## 🔗 Skills usadas em conjunto

- `resposta-final-pronta.md` — mapa vai no template de resposta
- `principio-menor-escopo.md` — só implementa o que tá no mapa
- `definition-of-done.md` — DoD valida se amarração tá completa
- `micro-rotinas.md` — R5 (verificar antes de pronto) inclui "mapa está completo?"

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*"o erro mais comum é eu manda ele cria algo e ele nao amarra a logica cria botoes sem fucoes" — Bruno*
*"nada pode ser criado e corrigir modificado sem ter a amaraacao completa da logica" — Bruno*
