---
name: definition-of-done
description: Critérios binários de "feito" por tipo de feature. Impede que Kothar declare feature pronta sem estar realmente funcional.
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: qualidade
---

# Skill: Definition of Done (DoD)

> "Terminei" pra Kothar = TODOS os critérios deste checklist, marcados como ✅.
> Se QUALQUER um for ❌ ou não aplicável, a feature **NÃO ESTÁ PRONTA**.

---

## 🎯 Regra-Mãe

Kothar **NUNCA** escreve "✅ Pronto" sem antes verificar cada item do DoD específico do tipo de feature. Se algum item falhar, volta pra Build, não pra Ship.
Toda entrega precisa ter pelo menos um indicador de assertividade executável validado com sucesso via `validador.sh` e score >= 90 em `analise-codigo.py`.

---

## 📋 DoD: Frontend (página/componente)

```
□ Código compila sem erros TypeScript/lint
□ TODOS os botões têm handler funcional (testado em browser)
□ TODOS os formulários têm validação + feedback visual
□ Layout responsivo em 3 tamanhos (mobile/tablet/desktop)
□ Estados tratados: loading / erro / vazio / sucesso
□ Sem credenciais no código (snake_case, .env, etc.)
□ Nenhum import quebrado / variável não usada
□ Sem código morto (console.log, comentários obsoletos, arquivos orfãos)
□ Visual IDÊNTICO ao que estava antes (a não ser que mudança de visual seja o escopo)
□ Testado em browser real (não só "compilou")
□ Print/screenshot do estado funcional anexado à entrega
```

---

## 📋 DoD: Backend (rota/endpoint/serviço)

```
□ Rota testada com curl/Postman/Insomnia (request + response)
□ Schema do banco validado (sem campos faltando, sem migration quebrada)
□ Erros tratados: input inválido, não encontrado, falha de DB, timeout
□ Log de erro não expõe credencial ou dado sensível
□ Autenticação/autorização aplicada (se rota privada)
□ Rate limit aplicado (se rota pública)
□ Sem credencial hardcoded (DATABASE_URL, API_KEY, etc.)
□ Sem variável não usada / import quebrado
□ Documentação da rota atualizada (descrição, params, response)
□ Sem regressão em rotas existentes (smoke test em rotas vizinhas)
```

---

## 📋 DoD: Feature Fullstack (frontend + backend + DB)

```
□ DoD de Frontend ✅
□ DoD de Backend ✅
□ Integração testada ponta-a-ponta (cenário real, não mock)
□ Migration aplicada em ambiente de homologação
□ Dados de teste realistas (não "test" / "asdf")
□ Rollback testado (se migration, saber desfazer)
□ Feature flags (se aplicável) — desativar não quebra sistema
□ Telemetria básica: como vou saber que está funcionando em prod?
```

---

## 📋 DoD: Feature de Agente IA (TOFU/MOFU/BOFU/CS no Kothar)

```
□ Persona definida (arquétipo, tom, restrições)
□ System prompt testado com 5+ cenários reais
□ Resposta fora do escopo é recusada (não alucina)
□ Métricas de sucesso definidas (conversão, tempo, satisfação)
□ Fallback quando IA falha (resposta padrão, escalação pra humano)
□ Custo por interação calculado (tokens × preço modelo)
□ Sem prompt injection (tentativas de burlar instruções)
□ Logs de conversa gravados (LGPD: consentimento + retenção)
□ Limite de tokens/mensagem respeitado
```

---

## 📋 DoD: Página/Painel Administrativo

```
□ DoD de Frontend ✅
□ DoD de Backend ✅ (se tiver persistência)
□ Integração com banco de dados testada
□ Permissões aplicadas (quem pode ver / editar / deletar)
□ Auditoria (quem fez o quê, quando)
□ Performance: carrega em < 2s com 100 registros
□ Sem N+1 query (verificar com log de queries)
□ Mensagens de erro claras pro usuário (não "Erro 500")
□ Estado vazio tratado (mensagem amigável, não tela em branco)
```

---

## 📋 DoD: Migração / Mudança de Infra

```
□ Backup completo ANTES de executar
□ Plano de rollback testado (não "sei que funciona")
□ Janela de manutenção definida (comunicar usuários)
□ Smoke test pré-migração (saber o que estava funcionando)
□ Execução em homologação ANTES de produção
□ Monitoramento ativo durante e após (logs, métricas, alertas)
□ DNS/SSL atualizado se IP mudou
□ Documentação atualizada (runbook, README, etc.)
□ Custo recorrente comparado (antes vs depois)
```

---

## 🚦 Como usar (workflow)

```
1. ANTES de começar a feature, Kothar cola o DoD correspondente na resposta
2. Conforme vai implementando, marca os itens que já estão ✅
3. Se algum item for ❌ ou "?", PARA e resolve ANTES de continuar
4. SÓ no final, quando TUDO estiver ✅, escreve "✅ Pronto"
5. Se Bruno pedir pra pular algum item: anota o motivo explicitamente
```

---

## ⚠️ Exceções (registrar sempre)

Às vezes o Bruno vai pedir pra entregar com DoD parcial. **Tudo bem**, mas:
- Listar quais itens estão pendentes
- Bruno aprovar explicitamente
- Criar ticket/nota pra resolver depois
- **Nunca** declarar "Pronto" se o que tá pendente é coisa crítica (segurança, funcional básico)

---

## 🔗 Skills relacionadas

- `principio-menor-escopo.md` — escopo positivo/negativo ANTES de começar
- `fluxo-discovery-design-build.md` — DoD é parte da fase Build/Verify
- `gate-seguranca-credenciais.md` — item obrigatório em todo DoD
- `analise-bugs.md` — pra debugar quando DoD falha

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
