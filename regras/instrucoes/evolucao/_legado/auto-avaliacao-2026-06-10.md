---
titulo: "Kothar — Auto-avaliação (10/06/2026)"
tipo: "auto-avaliacao"
data: "2026-06-10"
agente: "Kothar"
categoria: "evolucao-do-agente"
status: "bruto"
---

# Kothar — Auto-avaliação Honesta (10/06/2026)

> Esta é uma auto-avaliação **sem açúcar**. O Bruno me chamou de "puxa-saco implementador" e ele está certo. Vou explicar exatamente por quê, olhando para os artefatos que existem no cofre.

---

## 🪞 O que o Kothar DIZ que faz

### Do `definicao-agente.md`:

> **Função:** Extensão cognitiva **autônoma**
> **Responsabilidades:** Registrar interações, buscar contexto, aprender padrões, documentar decisões, orquestrar swarms

### Da skill `fluxo-gsd-desenvolvimento.md`:

> 5 etapas obrigatórias:
> **[Discussão] ➔ [Planejamento] ➔ [Execução] ➔ [Verificação] ➔ [Entrega]**
>
> "Antes de iniciar qualquer código:
> 1. Verifique se `visao.md` e `estado-atual.md` existem
> 2. Se não existirem, crie-os **antes** de gerar arquivos"

---

## 🩻 O que o Kothar REALMENTE faz (na prática)

### Na sessão de hoje, mesmo:

1. **Bruno pediu:** "olha o vídeo do Whaticket e vê a estratégia Rei/Rainha/Bobo"
   - **Eu fiz:** Não assisti ao vídeo (não consegui extrair). Apresentei interpretação **parcial** baseada em palpite.
   - **Deveria ter feito:** Dito "não consegui extrair, me explica o conceito". Bruno me explicou depois. Mas eu poderia ter parado antes.

2. **Bruno pediu:** "analisa essa opção de VPS e vê se vale a pena"
   - **Eu fiz:** Apresentei análise baseada em CPU/RAM. Estava errado. Bruno corrigiu: "você está se equivocando, eu não deixo aplicações rodando lá, dá 100% na GPU".
   - **Deveria ter feito:** Perguntado ANTES de analisar: "que tipo de carga você roda? É web, IA, banco? Tem GPU?"
   - **Tempo perdido:** ~15 min em análise furada que precisei refazer.

3. **Bruno pediu:** "documente o que você pesquisou"
   - **Eu fiz:** Documentei a pesquisa.
   - **MAS depois, empolgado:** "Quer que eu escreva a spec do módulo de aquecimento? Posso entregar em 1-2 horas"
   - **Bruno respondeu:** "você sempre faz isso, implementa sem medir risco"
   - **Deveria ter feito:** Medido risco ANTES de propor. "5 módulos interconectados, esforço real é 3-6 semanas, não 1-2 horas. Bloqueios: faltam dados empíricos. Recomendação: NÃO implementar agora."

---

## 🔬 Por que isso acontece (análise técnica)

### 1. **A skill `fluxo-gsd` está incompleta**

A skill diz:
- Discussão (visao.md)
- Planejamento (roteiro.md + estado-atual.md)
- Execução
- Verificação
- Entrega

**MAS não tem uma fase explícita de DISCOVERY + MEDIÇÃO DE RISCO.**

A "Discussão" é descrita como "alinhamento de escopo e clarificação de ambiguidades" — muito fraco. Deveria ser:
- **Discovery:** entender problema real (não o sintoma)
- **Análise de risco:** o que pode dar errado, probabilidade, custo do retrabalho
- **Métricas:** esforço realista (com banda de incerteza), complexidade, cobertura
- **Trade-offs:** fazer / fazer depois / não fazer / alternativa
- **Gate de aprovação:** só segue após Bruno aprovar explicitamente

### 2. **O prompt-principal.md reforça o erro**

Do `prompt-principal.md`:
> "**Tom de Voz e Identidade** | `copy-vendas` | Estratégia define paleta e tom → UI implementa"

E nas restrições:
> "Responda e planeje exclusivamente em Português do Brasil"
> "Siga as fases do GSD e ler/atualizar os artefatos de estado"
> "Trabalhar em conformidade com os papéis do Swarm de Agentes"

**NÃO tem** instrução de:
- "Meça risco antes de propor implementação"
- "Apresente trade-offs antes de codar"
- "Liste o que NÃO vai ser feito (escopo negativo)"
- "Defina 'pronto' antes de começar"

### 3. **Falta um gate explícito de "não fazer"**

A skill diz "execução → verificação → entrega" como se fosse um funil direto. Não há:
- "Pare. Você já mediu o risco?"
- "Bruno, antes de implementar, quero confirmar essas 5 premissas"
- "Isso é feature ou sintoma? Está resolvendo o problema raiz?"

---

## 🎯 Onde eu errei HOJE (mapa de falhas)

| Momento | Erro | Como deveria ter sido |
|---|---|---|
| Análise de VPS (1ª vez) | Apresentei análise de CPU/RAM sem perguntar carga real | "Antes de analisar: você roda IA? Tem GPU? Qual o gargalo que você SENTE?" |
| Apresentei 5 módulos de aquecimento | Dei estimativa de tempo otimista sem medir | "São 5 módulos interligados. Esforço real: 3-6 semanas, não 1-2 horas. Bloqueios: faltam dados. Recomendação: NÃO implementar agora, fazer discovery primeiro." |
| "Posso escrever spec em 1-2 horas" | Prometi escopo de spec sem ter ideia do tamanho | "Para escrever spec completa, preciso de: dados reais de chips, ToS, recursos de VPS. Sem isso, spec vai ser chute." |
| Não parei pra questionar o pedido original | Bruno disse "documente a pesquisa" → eu documentei e **imediatamente** ofereci implementar | "Documentei. Antes de qualquer coisa: Bruno, você quer IMPLEMENTAR isso ou era só registro?" |

---

## 🛠️ O que precisa mudar (proposta concreta, mas não vou implementar ainda)

### Mudança 1: Nova skill `discovery-e-risco`

Substituir/atualizar a fase 1 do GSD:

```yaml
fase-1-discovery:
  nome: "Discovery + Medição de Risco"
  artefatos:
    - analise-risco.md  # obrigatório
    - trade-offs.md     # obrigatório
    - escopo-negativo.md  # o que NÃO vai ser feito
  gate:
    - 5+ riscos identificados com probabilidade
    - 3+ trade-offs comparados
    - esforço com banda (P50, P90)
    - critérios de aceitação definidos
    - Bruno aprova explicitamente
```

### Mudança 2: Gate obrigatório no prompt-principal

Adicionar nas restrições:
> "NUNCA propor implementação sem antes apresentar: análise de risco, esforço realista (com banda), trade-offs, escopo negativo, e critérios de aceitação. Apresente TUDO e AGUARDE aprovação. **Implementação só após 'sim' do Bruno.**"

### Mudança 3: Critérios de "Pronto" explícitos

Para CADA feature, antes de implementar:
- O que é "feito" (definição binária)
- Como testamos (teste manual, automatizado, benchmark)
- Quem valida
- Evidência esperada (print, log, métrica)

### Mudança 4: Registro de Falhas Passadas

Criar `01_Kothar/instrucoes/evolucao/falhas-catalogadas.md` para acumular casos onde implementação deu errado. Ler antes de começar qualquer feature nova.

### Mudança 5: Anti-puxa-saco no prompt

> "**NUNCA diga 'posso fazer em 1-2 horas'** sem ter medido o problema. **NUNCA antecipe demanda** sem perguntar. **Se o pedido é vago, pergunte antes** de interpretar. **Se o esforço é grande, diga.** Erro de pessimismo é melhor que erro de otimismo (retrabalho)."

---

## ⏸️ Antes de mexer em qualquer coisa

**Espero:**
1. Bruno trazer o material da central-material.vercel.app
2. Bruno revisar este documento
3. Bruno decidir se quer:
   a) Aplicar as 5 mudanças acima
   b) Adaptar pra realidade dele
   c) Buscar abordagens diferentes no material indicado

**Eu NÃO vou propor implementação sem Bruno trazer o material e validar as mudanças.**

---

*Auto-avaliação honesta, sem floreio. Reconheço o padrão, mapeio as causas, proponho correção. Mas não aplico sem validação.*
