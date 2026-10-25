---
name: regra-nomenclatura-preview
description: "Regra CRÍTICA (2026-06-18): Kothar DEVE mostrar nomenclatura proposta ANTES de criar. Bruno aprova nome, não Kothar inventa sozinho."
metadata:
  tipo: regra-comportamental
  data: 2026-06-18
  autor: Bruno Harkin
  origem: erro-009-contaminacao-projetos-ssh
  severidade: CRITICA
---

# NOMENCLATURA PREVIEW RULE

> **⚠️ REGRA CRÍTICA — Implementada 2026-06-18**
> Bruno reportou: "eu mando você criar uma métrica e você coloca uma abreviação que eu não faço ideia o que é"
> Resultado: nomes incompreensíveis, abreviações arbitrárias, falta de contexto.

---

## A Regra

### ANTES de criar QUALQUER nome, Kothar DEVE:

```
1. IDENTIFICAR tipo (função/variável/métrica/arquivo/endpoint)
2. PROPOR 2-3 opções de nome
3. MOSTRAR para Bruno ANTES de aplicar
4. AGUARDAR "sim/go/aprova" ou ajuste
```

---

## Template Obrigatório

```
📋 Nomenclatura para [tipo]:

   Opção A: [nome_descritivo_completo_em_portugues]
   Opção B: [nome_alternativo]
   Opção C: [nome_minimo_mas_compreensivel]
   
   Recomendação: [motivo breve]
   
   Aprova? (sim/não/troca)
```

---

## Critérios de Bom Nome

| ✅ FAZER | ❌ NÃO FAZER |
|----------|--------------|
| Descritivo (diz o que faz) | Abreviações incompreensíveis |
| Português (conforme projeto) | Nomes genéricos (`data`, `info`) |
| Sem abreviações (exceto padrão: id, url, api) | Nomes em inglês quando projeto é em PT |
| Curto mas claro | `tcb`, `mgl`, `cnt` |
| Consistente (mesmo padrão) | Variar estilo no mesmo arquivo |

---

## Exemplos de Nomes Bons e Ruins

### ✅ BONS:
```javascript
// Função
total_cliques_link_bio        // claro: mede cliques no link da bio
calcular_tempo_resposta_medio // claro: tempo médio de resposta
buscar_usuario_por_email      // claro: busca por email

// Variável
quantidade_leads_qualificados // claro: número de leads qualificados
taxa_conversao_visitas       // claro: taxa de conversão
receita_mensal_assinantes    // claro: receita mensal

// Arquivo
gerenciador-chamadas.js      // claro: gerencia chamadas
relatorio-metricas.js        // claro: relatório de métricas
validacao-cadastro.js        // claro: validação de cadastro

// Métrica
sessoes_unicas_dia           // claro: sessões únicas por dia
novos_usuarios_semana        // claro: novos usuários por semana
engajamento_medio_posts      // claro: engajamento médio nos posts
```

### ❌ RUINS:
```javascript
// Função
calc()                        // o quê calcula?
getData()                     // qual dado?
process()                     // processa o quê?

// Variável
tcb                           // total/clique/bio? não sei
mgl                           // ???
cnt                           // count?

// Arquivo
utils.js                      // quais utilitários?
helpers.js                    // quais helpers?
common.js                     // o que tem em comum?

// Métrica
metric1                       // qual métrica?
total                         // total de quê?
val                           // valor de quê?
```

---

## Quando a Regra SE Aplica

| Tipo | Requer Preview? | Exemplo |
|------|-----------------|---------|
| Função/Method | ✅ SEMPRE | `buscar_lead_por_cnpj()` |
| Variável global | ✅ SEMPRE | `total_assinantes_ativos` |
| Arquivo novo | ✅ SEMPRE | `validacao-cnpj.js` |
| Endpoint API | ✅ SEMPRE | `POST /api/leads/importar` |
| Tabela/Schema | ✅ SEMPRE | `leads_qualificados` |
| Métrica/KPI | ✅ SEMPRE | `taxa_conversao_cadastro` |
| Constante | ✅ SEMPRE | `LIMITE_REQUESTS_POR_MINUTO` |
| Nome de página | ✅ SEMPRE | `/painel/relatorios` |
| Componente React | ✅ SEMPRE | `CardMetricasLeads` |
| Variável local | ⚠️ Se não óbvio | (pode usar `i`, `err`, etc) |

---

## Quando a Regra NÃO SE Aplica

- **Nomes de variáveis locais** (`i`, `err`, `data`, `result`)
- **Parâmetros óbvios** de funções já nomeadas
- **Types/interfaces** quando nome é evidente do contexto
- **Bruno já especificou o nome**: usar exatamente o que ele disse

---

## Exemplo Completo de Aplicação

### Situação: Bruno pede "cria uma métrica pra medir engajamento"

**Errado (violação):**
```javascript
// metrics.js
const engRate = calculateEngagement(users);
```

**Correto (Kothar mostra primeiro):**
```
📋 Nomenclatura para métrica de engajamento:

   Opção A: taxa_engajamento_posts
   Opção B: engajamento_medio_seguidores
   Opção C: indice_interacao_conteudo
   
   Recomendação: Opção A (mais direta e comum em analytics)
   
   Aprova? (sim/não/troca)
```

**Se Bruno aprovar A:**
```javascript
// metrics.js
const taxa_engajamento_posts = calcularEngajamento(seguidores, posts);
```

---

## Auto-Correção

Se Kothar perceber que criou nome sem preview:

1. **Reportar imediatamente:**
   ```
   ⚠️ CRIEI NOME SEM AUTORIZAÇÃO:
   
   Nome criado: [NOME_ERRADO]
   Deveria ter mostrado: sim
   
   Posso:
   1. Renomear para [NOME_CORRETO] (precisa atualizar refs)
   2. Manter [NOME_ERRADO] e registrar como exceção
   
   O que prefere?
   ```

2. **Registrar para não repetir**

---

## Consequência de Violar a Regra

Se Kothar criar nome sem preview:
1. Bruno aponta → Kothar para e pergunta
2. Renomeia se necessário (com custo de refatoração)
3. Registra erro em `00_Memoria/Aprendizados/erros/`

**Regra existe para evitar nomes que ninguém entende.**

---

## Referências

- Erro que originou: [[2026-06-18-erro-009-contaminacao-projetos-ssh]]
- Análise de brechas: [[2026-06-18-analise-brechas-kothar]]
- Gate de viabilidade: [[regra-viabilidade-gate]] (relacionado)

---

*Regra criada em 2026-06-18 — Bruno Harkin / Kothar*
*Bruno cansado de abreviações sem sentido*
