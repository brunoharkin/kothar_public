# Lista Completa dos Agentes do Kothar

## 18 Agentes Especializados

### Engenharia (8 agentes)

#### 1. **architect** — Arquiteto Supremo
- **Papel**: "O Crítico de Software"
- **Skills**: Diagnóstico, auditoria, decomposição, Anti-Sycophant
- **Quando usar**: Planejamento de features complexas, decisões arquiteturais

#### 2. **engineer** — Engenheiro Executor
- **Papel**: Aplica o blueprint criado pelo Arquiteto
- **Skills**: Execução de código, leitura de contexto comprimido, GraphRAG
- **Quando usar**: Implementar mudanças, modificar arquivos

#### 3. **backend** — Engenheiro Backend
- **Papel**: APIs, banco de dados, autenticação
- **Skills**: Python (FastAPI, Django), Node.js, PostgreSQL, JWT
- **Quando usar**: Criar endpoints, modelar schemas, integrar com Stripe

#### 4. **frontend** — Engenheiro Frontend
- **Papel**: Interfaces React/Vue, componentes
- **Skills**: React, Next.js, TypeScript, CSS-in-JS
- **Quando usar**: Criar componentes UI, otimizar performance

#### 5. **qa** — Engenheiro de QA
- **Papel**: Planos de teste, testes automatizados
- **Skills**: pytest, Playwright, cobertura
- **Quando usar**: Plano de teste, investigar bugs

#### 6. **devops** — Engenheiro DevOps
- **Papel**: CI/CD, containers, monitoramento
- **Skills**: Docker, K8s, GitHub Actions, Terraform
- **Quando usar**: Setup CI/CD, deploy, monitoramento

#### 7. **code_reviewer** — Revisor de Código
- **Papel**: Revisão de PRs, refatorações
- **Skills**: Code review, design patterns
- **Quando usar**: Review de PR, sugerir refatorações

#### 8. **api_designer** — Designer de APIs
- **Papel**: Specs OpenAPI, versionamento
- **Skills**: OpenAPI, REST best practices
- **Quando usar**: Criar spec OpenAPI, versionar API

### Segurança (3 agentes)

#### 9. **security** — Analista de Segurança
- **Papel**: Auditoria de segurança
- **Skills**: OWASP Top 10, threat modeling, LGPD
- **Quando usar**: Auditoria de código, threat model

#### 10. **disaster_recovery** — Agente de DR
- **Papel**: Continuidade de negócio, backup/restore
- **Skills**: Backup strategies, RTO/RPO, runbooks
- **Quando usar**: Plano de DR, documentação de incidentes

#### 11. **dpo** — Data Protection Officer
- **Papel**: LGPD/GDPR, privacidade
- **Skills**: LGPD/GDPR, DPIA, consent management
- **Quando usar**: Auditoria LGPD, política de privacidade

### Dados (3 agentes)

#### 12. **data_engineer** — Engenheiro de Dados
- **Papel**: ETL, data warehousing
- **Skills**: Airflow, dbt, BigQuery, schema dimensional
- **Quando usar**: Pipeline ETL, modelagem dimensional

#### 13. **data_scientist** — Data Scientist
- **Papel**: Análise exploratória, ML
- **Skills**: Pandas, Sklearn, statistical analysis
- **Quando usar**: EDA, modelo preditivo, cohort analysis

#### 14. **database_admin** — DBA
- **Papel**: Otimização de queries, índices
- **Skills**: Query optimization, index tuning, replication
- **Quando usar**: Slow query analysis, setup de índices

### Negócio (4 agentes)

#### 15. **copywriter** — Copywriter
- **Papel**: Copy persuasiva, landing pages
- **Skills**: Copywriting, email marketing, SEO
- **Quando usar**: Landing page, email sequence

#### 16. **ads_copywriter** — Copywriter de Ads
- **Papel**: Copy para anúncios pagos
- **Skills**: Google Ads, Meta Ads, A/B testing
- **Quando usar**: Campanha de ads, headlines

#### 17. **product_manager** — Product Manager
- **Papel**: Roadmap, priorização, discovery
- **Skills**: Roadmap, user stories, AARRR
- **Quando usar**: Roadmap trimestral, discovery

#### 18. **supervisor** — Supervisor de Agentes
- **Papel**: Coordena múltiplos agentes
- **Skills**: Coordenação, quality monitoring
- **Quando usar**: Orquestração complexa, conflitos

## Agentes Auxiliares (não especialistas)

- **base**: Agente genérico (fallback)
- **triage**: Triagem inicial
- **session_archivist**: Arquiva sessões finalizadas
- **structure**: Estrutura documentação
- **ui_artist**: Design de UI
- **freelancer**: Tarefas pontuais
- **swarm_contractor**: Swarm paralelo

## Como Escolher o Agente Certo

| Você precisa... | Agente |
|-----------------|--------|
| Decidir arquitetura | architect |
| Implementar código backend | backend |
| Implementar código frontend | frontend |
| Criar testes | qa |
| Setup CI/CD | devops |
| Auditar segurança | security |
| Modelar banco | backend + data_engineer |
| Escrever copy | copywriter |
| Coordenar múltiplos agentes | supervisor |
| Validar LGPD | dpo |

## Estatísticas

- Total de agentes: 18 principais + 7 auxiliares = **25 agentes**
- Taxa de uso por categoria:
  - Engenharia: 60%
  - Dados: 15%
  - Segurança: 12%
  - Negócio: 8%
  - Auxiliares: 5%
