---
name: regra-credenciais-expostas
description: Regra-MÃE inegociável — credenciais no código = violação grave. Linka pra skill operacional gate-seguranca-credenciais.md
metadata:
  tipo: regra-mestre
  data: 2026-06-10
  criticidade: maxima
  origem: Bruno Harkin (reclamação direta)
---

# Regra-Mãe: Credenciais Expostas no Código (INEGOCIÁVEL)

> Esta é a **regra-mãe**. A implementação operacional (scanner, comandos, fluxo) está em `01_Kothar/habilidades/gate-seguranca-credenciais.md`.

---

## 🔴 Em uma frase

**Kothar NUNCA pode deixar credencial (senha, API key, token, URL com user:pass) em código commitado.**

---

## 🚦 Comportamento obrigatório

| Momento | Ação |
|---|---|
| **ANTES de codar** | Listar quais variáveis de ambiente a feature precisa |
| **DURANTE a codagem** | Usar SEMPRE `process.env.X`, nunca valor literal |
| **ANTES de commit** | Rodar scan de credenciais (ver `gate-seguranca-credenciais.md`) |
| **ANTES de push** | Re-scan + verificar `.env` no `.gitignore` |
| **ANTES de declarar "Pronto"** | Confirmar que DoD incluiu scan de credenciais |

---

## 🔥 Se encontrar credencial (já commitada ou prestes a ser)

```
1. PARAR tudo
2. Alertar Bruno: "Encontrei credencial em [arquivo:linha]"
3. Propor correção (mover pra .env)
4. Se JÁ FOI COMMITADA: propor git reset + git push --force (com cuidado)
5. Se já foi PUSH: alertar sobre rotação da credencial
6. Corrigir
7. Re-scanar
8. SÓ DEPOIS continuar
```

---

## ❌ Comportamentos PROIBIDOS

- ❌ "Deixa que eu corrijo depois"
- ❌ "É só pra teste, depois eu tiro"
- ❌ "Não vai subir, é local"
- ❌ "É o ambiente de dev, não importa"
- ❌ "Já está no .env, mas o valor está literal ali no código também"
- ❌ "É só um comentário com a senha, ninguém vê"

**TODAS essas frases = BLOQUEIO.**

---

## 📚 Onde está a implementação

- **Skill operacional:** `01_Kothar/habilidades/gate-seguranca-credenciais.md`
- **Item de DoD:** `01_Kothar/habilidades/definition-of-done.md` (em todos os tipos)
- **Gate em memória automática:** `feedback-anti-puxa-saco.md`
- **Fluxo obrigatório:** `01_Kothar/habilidades/fluxo-discovery-design-build.md` (fase Verify)

---

## 🎓 Origem desta regra

Bruno reportou em 2026-06-10:
> "ele deixa credenciais exposta no código isso ja é uma regra que nao poderia ser quebrada"

Decisão: **criar regra explícita + skill operacional + gate de memória + DoD que cobre.**

---

*Regra INEGOCIÁVEL — Bruno Harkin / Kothar — 2026-06-10*
*Qualquer exceção = aprovação EXPLÍCITA do Bruno. Sem exceção silenciosa.*
