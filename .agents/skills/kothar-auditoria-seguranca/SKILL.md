---
name: kothar-auditoria-seguranca
description: >-
  Skill do Kothar: Auditoria de Segurança Multi-Fase, Validação Adversarial e Caça a Vulnerabilidades
  (baseada no framework de referência Cloudflare security-audit-skill). Transforma os agentes do Kothar em
  auditores de segurança de alta precisão através de reconhecimento arquitetural, ledger de cobertura,
  verificação adversarial independente (o agente que valida tenta ativamente refutar o achado) e vereditos tipados
  (confirmed, needs_validation, rejected).
---

# Skill: Kothar Auditoria Avançada de Segurança & Red Teaming Defensivo

> **Inspirado no Harness de Auditoria da Cloudflare (`cloudflare/security-audit-skill`).**
> Encontrar vulnerabilidades reais que violam fronteiras de confiança, comprovadas com evidência de código, reprodução segura e mitigação de menor escopo. Segurança sem falsos positivos e sem alucinação.

---

## 🛑 OS 5 PRINCÍPIOS FUNDAMENTAIS (Anti-Alucinação)

1. **Severidade Exige Impacto Real:**
   - Vulnerabilidade = $\text{Probabilidade} \times \text{Impacto Concreto}$.
   - O simples desvio de uma boa prática ou checklist não é uma vulnerabilidade se não houver um ator malicioso capaz de causar dano a um recurso ou identidade protegida.
2. **Validação Adversarial Obrigatória:**
   - **O agente que valida um achado NUNCA é o agente que o encontrou.**
   - O agente validador recebe a hipótese com uma instrução explícita: *\"Tente provar que este achado é FALSO e que o código já está protegido por outras barreiras.\"*
3. **Lacunas de Defesa em Profundidade não são Vulnerabilidades:**
   - Se a Camada A (ex: validação de schema / token JWT verificado) impede o ataque de forma determinística, a ausência da Camada B é uma nota de **Hardening (Endurecimento)**, nunca uma falha `confirmed`.
4. **Guardrails de Prompt NÃO são Fronteiras de Segurança:**
   - Em sistemas de IA e agentes, instruções em linguagem natural no prompt ("por favor, não responda senhas") não constituem barreira de segurança. Apenas código determinístico (schemas tipados, validação de parâmetros, ACLs e isolamento de processo) são barreiras válidas.
5. **Prompt Injection só é Vulnerabilidade se Romper Código:**
   - Prompt injection isolado não é finding. Ele só se torna vulnerabilidade quando o texto não confiável atinge o contexto de outro usuário, executa uma ferramenta sem autorização ou alimenta um sink perigoso (banco, shell, memória durável).

---

## 📋 OS 3 VEREDITOS ESTRITOS (Machine-Readable Findings)

Toda análise de vulnerabilidade deve terminar estritamente em um dos 3 vereditos:

| Veredito | Critério Obrigatório | Ação do Auditor |
|---|---|---|
| `confirmed` | Trace completo (Entrada $\rightarrow$ Fluxo $\rightarrow$ Sink) + Impacto real comprovado + Ator e recurso identificados. | Registrar no relatório com severidade e menor código de correção. |
| `needs_validation` | Ponto cego estático que depende de variável de ambiente, configuração de infraestrutura ou runtime ausente. | **PROIBIDO chutar severidade.** Registrar o fato exato que falta validar e o plano de teste. |
| `rejected` | Hipótese descartada (ex: caminho inatingível, dados previamente sanitizados, falso positivo de linter). | Registrar o motivo da refutação para histórico e evitar re-trabalho. |

---

## 🔄 O FLUXO DE AUDITORIA EM 6 FASES (Cloudflare Harness)

```
[FASE 1: Reconhecimento]      → Mapear fronteiras, atores, entradas e gerar coverage-ledger.json
           ↓
[FASE 2: Caça Especializada]  → Hunters isolados caçam por classes específicas de ataque
           ↓
[FASE 3: Validação Adversária]→ Verificador independente tenta DERRUBAR a vulnerabilidade
           ↓
[FASE 4: Estruturação]        → Gravar findings.json (validado por schema restrito)
           ↓
[FASE 5: Revisão Independente]→ Agente fresco valida a correção de menor escopo
           ↓
[FASE 6: Relatório Neutro]    → Gerar REPORT.md, FINDINGS-DETAIL.md e NEEDS-VALIDATION.md
```

### Fase 1: Reconhecimento & Ledger de Cobertura
- Criar mapa arquitetural de fronteiras de confiança (`architecture.md`).
- Criar a lista determinística de unidades a auditar (`coverage-ledger.json`).
- Mapear: Quem é o atacante? Quem é a vítima? Onde entram dados externos?

### Fase 2: Caça por Classes de Ataque Especializadas
Distribuir tarefas para subagentes focados em vetores específicos:
1. **Injeção de Código & Queries:** SQL com interpolação, comando shell, deserialização insegura, SSRF via requests.
2. **Controle de Acesso & Broken Auth:** Bypasses de middleware, inconsistência entre autenticação vs autorização, vazamento de IDs (IDOR/BOLA).
3. **Agentes de IA, RAG & MCP:**
   - Injeção indireta de prompt via documentos do RAG.
   - Contaminação de memória persistente (Memory Poisoning).
   - Confusão de papéis (Role Confusion em prompts interpolados).
   - Injeção de argumentos em ferramentas de IA (Tool Dispatch).
4. **Isolamento de Dados & Multi-Tenant:**
   - Vazamento de contexto entre tenants em queries sem cláusula de isolamento estrito.
   - Cache compartilhado sem chave de tenant.
5. **Exaustão de Recursos & Custos:**
   - Regex catastrófico (ReDoS), loops infinitos com payloads grandes, estouro de cotas de APIs pagas (OpenAI/Meta).

### Fase 3: Validação Adversarial de Candidatos
Para cada candidato encontrado na Fase 2:
- Spawnar um **Verificador Adversarial**.
- O validador deve ler o contexto em volta, checar middleware anterior, tipagens do Pydantic/Zod e configurações de banco.
- Se o validador encontrar uma barreira que impede a exploração $\rightarrow$ Marcar como `rejected` ou `hardening`.

### Fase 4 e 5: Estruturação e Correção de Menor Escopo
- Gerar o registro JSON estruturado com o fingerprint único da falha.
- Desenvolver a **Mínima Correção Eficaz** (princípio do menor escopo do Kothar): corrigir a causa raiz na borda de entrada sem refatorações amplas desnecessárias.

### Fase 6: Relatórios Oficiais
Salvar os relatórios de auditoria no Cofre oficial (`/home/bruno-harkin/Cofre/auditorias/{projeto}/`):
- `REPORT.md`: Sumário executivo, estatísticas de cobertura e matriz de risco.
- `FINDINGS-DETAIL.md`: Código vulnerável, passo a passo de reprodução segura e diff de correção.
- `NEEDS-VALIDATION.md`: Lista de incógnitas de infraestrutura a serem validadas em produção.

---

## 🔐 REGRAS DE EXECUÇÃO EM SANDBOX

- Todo teste de código deve rodar na sandbox padrão (`BypassSandbox: false`).
- Nunca disparar payloads contra endpoints remotos de produção ou serviços de terceiros.
- Usar dados sintéticos (fixtures) e segredos fictícios (`dummy_secret_xxx`).
- Nunca usar `/tmp` desprotegido; usar `scratch/` do workspace.

