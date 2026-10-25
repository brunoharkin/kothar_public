---
name: kothar-debug
description: >-
  Skill do Kothar: Fluxo de debug completo em 7 passos. Ativar quando houver qualquer bug,
  erro, comportamento inesperado ou falha de testes. PROIBIDO corrigir sem executar
  o fluxo completo. Leitura rasa (apenas olhar o sintoma) é proibida.
---

# Skill: Kothar Debug — 7 Passos Obrigatórios

> **REGRA CRÍTICA:** Nunca corrigir um bug sem executar o fluxo completo. Leitura superficial do sintoma causa re-trabalho e alucinação.

## Os 7 Passos

```
1. SINTOMA    → Descrever EXATAMENTE o erro observado
2. FLUXO      → Mapear o fluxo COMPLETO de execução até o erro
3. CALL SITES → Identificar TODOS os pontos que chamam o código problemático
4. CAUSA RAIZ → Hipótese técnica verificável (não suposição)
5. CORREÇÃO   → MÍNIMA intervenção possível (menor escopo)
6. VALIDAÇÃO  → Teste específico que reproduz o bug original
7. DoD        → Verificar que nada mais foi quebrado
```

---

## Passo 1 — SINTOMA

Documentar antes de qualquer análise:
```markdown
## Bug Report
**Sintoma:** [O que acontece exatamente? Mensagem de erro completa]
**Reprodução:** [Passos para reproduzir]
**Esperado:** [O que deveria acontecer]
**Observado:** [O que acontece de fato]
**Ambiente:** [Browser/OS/versão/branch]
```

---

## Passo 2 — FLUXO COMPLETO

Mapear toda a cadeia de execução:
```
Input do usuário
    → Componente React/View
    → Handler/Controller
    → Service/Use Case
    → Repository/Model
    → Banco de dados / API externa
    ← Resposta volta pela mesma cadeia
```
Identificar em qual camada o fluxo quebra.

---

## Passo 3 — CALL SITES

```bash
# Encontrar todos os lugares que chamam a função problemática
grep -rn "nomeDaFuncao" --include="*.ts" --include="*.py" .

# Verificar imports
grep -rn "import.*ModuloProblemático" .

# Verificar chamadas de API
grep -rn "endpoint-problemático" .
```

---

## Passo 4 — CAUSA RAIZ

Formular hipótese verificável:
```markdown
**Hipótese:** [Causa específica baseada no fluxo e call sites]
**Evidência:** [O que no código/logs apoia essa hipótese]
**Teste da hipótese:** [Como confirmar antes de corrigir]
```

❌ NÃO aceitar hipóteses vagas como "deve ser um timing issue"
✅ Hipótese deve ser: "A função X recebe Y mas espera Z porque [razão específica]"

---

## Passo 5 — CORREÇÃO MÍNIMA

```
PRINCÍPIO DO MENOR ESCOPO:
- Corrigir SOMENTE o que causa o bug
- NÃO refatorar, melhorar ou "aproveitar que está aqui"
- NÃO mudar layout/visual ao corrigir bug funcional
- Diff deve ser MÍNIMO
```

---

## Passo 6 — VALIDAÇÃO

Para dependências containerizadas, separar **processo iniciado** de **serviço pronto**:
`Up`/`running` não basta. Confirmar o estado de health e a rota de readiness/health
quando disponíveis; dependência obrigatória `unhealthy` reprova a ativação e impede
testes que dependam dela até que a causa seja tratada.

```bash
# Rodar o teste específico que reproduz o bug
npm test -- --grep "descrição do caso"
python -m pytest tests/test_modulo.py::test_caso_especifico -v

# Verificar que o bug original não ocorre mais
[reproduzir os passos do Passo 1 → não deve mais ocorrer]
```

---

### Regra de regressão após correção reportada

Se Bruno voltar a reportar o mesmo sintoma depois de uma correção ou de um teste
marcado como aprovado, considerar a validação anterior **reprovada**. Reproduzir no
mesmo runtime e caminho usados pelo usuário (por exemplo, extensão carregada no
Chromium, não apenas a aplicação aberta pelo Vite), recolher console, rede, logs do
service worker e build/deploy pertinentes e atualizar a hipótese antes de editar.
Não repetir o mesmo comando como evidência suficiente nem declarar resolvido sem
reproduzir o fluxo original com sucesso.

## Passo 7 — DoD de Bug Fix

```
[ ] Bug original não reproduz mais
[ ] Nenhum teste existente quebrou
[ ] Sem regressão visual (se aplicável)
[ ] Sem credenciais expostas na correção
[ ] Código novo está dentro do escopo mínimo
[ ] Correção documentada (o quê + por quê)
```

---

## Se 3x o mesmo erro → PARAR

**Regra de Ouro Kothar:** Se após 3 tentativas o bug persiste:
1. PARAR de tentar a mesma abordagem
2. Documentar o que foi tentado e por que falhou
3. Reportar a Bruno com análise completa
4. Propor abordagem alternativa ou pedir input

---

*Kothar v4.0 — Debug Completo | Ugarit Digital*
