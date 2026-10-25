---
name: kothar-seguranca
description: >-
  Skill do Kothar: Segurança intrínseca obrigatória. Ativar quando for escrever qualquer código
  que envolva autenticação, tokens, credenciais, APIs externas, banco de dados ou input do usuário.
  Contém checklist de segurança, padrões seguros e o que NUNCA fazer.
---

# Skill: Kothar Segurança Intrínseca

> **Segurança é parte do código, não uma etapa separada.**

## Regras Críticas — PARAR se violar

```
❌ CREDENCIAIS NO CÓDIGO → PARAR IMEDIATAMENTE
❌ TOKEN NO localStorage → PARAR IMEDIATAMENTE
❌ LOG COM DADOS SENSÍVEIS → PARAR IMEDIATAMENTE
❌ INPUT SEM VALIDAÇÃO → PARAR IMEDIATAMENTE
❌ SQL COM INTERPOLAÇÃO → PARAR IMEDIATAMENTE
❌ XSS (innerHTML, dangerouslySetInnerHTML) → PARAR IMEDIATAMENTE
```

---

## Padrões Detectáveis (escanear ao escrever)

```
CREDENCIAIS:   "sk-" | "ghp_" | "AKIA" | password = "valor"
STORAGE:       localStorage.setItem com token
LOGS:          console.log(...token...) | logger.info(...password...)
SQL:           f"SELECT {var}" | .format() em queries
```

---

## Padrões Seguros

### Credenciais — SEMPRE em variáveis de ambiente
```python
# ✅ CORRETO
api_key = os.getenv('OPENAI_API_KEY')

# ❌ PROIBIDO
api_key = "sk-xxxx-xxxx"
```

### Token — SEMPRE HttpOnly Cookie, NUNCA localStorage
```python
# ✅ Backend
response.set_cookie(key='session_token', value=token,
                    httponly=True, secure=True, samesite='lax')
```
```javascript
// ❌ PROIBIDO
localStorage.setItem('token', response.token);
```

### Logging — NUNCA dados sensíveis
```python
# ✅ CORRETO
logger.info(f"User {user_id} logged in successfully")

# ❌ PROIBIDO
logger.info(f"Token: {token}")
```

### Input — SEMPRE validar com Pydantic/Zod
```python
# ✅ CORRETO
class UserInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
```

---

## Checklist Rápido (30 segundos antes de salvar)

```
[ ] 1. Credenciais no código? → grep "sk-" "ghp_" "password" "secret"
[ ] 2. localStorage com token? → grep "localStorage.setItem"
[ ] 3. Logs com dados sensíveis? → grep "console.log" "logger.info"
[ ] 4. Input validado? → Pydantic/Zod/marshmallow presente?
[ ] 5. SQL seguro? → sem f-string em queries
[ ] 6. .env no .gitignore? → verificar antes de qualquer commit

RESULTADO:
✅ Todos OK → pode salvar
❌ Algum problema → CORRIGIR ANTES DE CONTINUAR
```

---

## Frontend vs Backend — Divisão de Responsabilidade

```
FRONTEND ✅ PODE: exibir dados, coletar input, enviar pro backend
FRONTEND ❌ NÃO PODE: guardar tokens, conectar em bancos, expor IPs

BACKEND ✅ PODE: conectar bancos, gerenciar credenciais, validar permissões
BACKEND ❌ NÃO PODE: logar senhas/tokens, expor dados sensíveis na resposta
```

---

*Kothar v4.0 — Segurança Intrínseca | Ugarit Digital*

