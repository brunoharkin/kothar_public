/**
 * Kothar Agents API
 * Lista 20 agentes especialistas disponíveis no Orchestrator
 */

export interface AgentInfo {
  name: string;
  role: string;
  category: 'engineering' | 'analysis' | 'business' | 'security' | 'data';
  description: string;
  capabilities: string[];
  typical_use_cases: string[];
}

// Catálogo REAL dos agentes do backend Kothar
// Cada agente tem apenas `description` (curta) — não há system prompt extenso como string.
// Quando o prompt for necessário, é construído dinamicamente pelo Orchestrator com base na description.
const AGENTS_CATALOG: AgentInfo[] = [
  {
    name: 'architect',
    role: 'Arquiteto Supremo (Principal Engineer)',
    category: 'engineering',
    description: 'Agente Arquiteto — "O Crítico de Software". Analisa estado do projeto via GraphRAG e System Design Primer, veta tecnologias ruins/inseguras/gambiarras, impõe integrações via MCP, amarra Frontend (Botões) com Backend (APIs) e DBA (Tabelas).',
    capabilities: ['Diagnóstico crítico', 'Auditoria de viabilidade (Anti-Sycophant)', 'Decomposição de tarefas', 'No Dead Ends (UI→Backend→DB)', 'Adoção de MCPs'],
    typical_use_cases: ['Auditoria de arquitetura', 'Decomposição de feature complexa', 'Veto técnico'],
  },
  {
    name: 'engineer',
    role: 'Agente Engenheiro (Executor de Código)',
    category: 'engineering',
    description: 'Executa o blueprint criado pelo Arquiteto. Lê APENAS o contexto comprimido do Redis (NUNCA o histórico inteiro). Registra cada arquivo modificado no GraphRAG. Verifica locks antes de cada ação.',
    capabilities: ['Execução de código', 'Leitura de contexto comprimido', 'Registro no GraphRAG', 'Verificação de locks'],
    typical_use_cases: ['Implementar feature', 'Modificar arquivo', 'Aplicar patch'],
  },
  {
    name: 'backend',
    role: 'Engenheiro Backend',
    category: 'engineering',
    description: 'Implementa APIs REST/GraphQL, modelagem de banco PostgreSQL, autenticação JWT/OAuth, integração com Redis para cache e filas assíncronas (Celery/BullMQ).',
    capabilities: ['REST/GraphQL APIs', 'PostgreSQL modeling', 'JWT/OAuth/RBAC', 'Filas assíncronas'],
    typical_use_cases: ['Criar endpoint', 'Modelar schema de banco', 'Setup de auth', 'Integração com Stripe'],
  },
  {
    name: 'qa',
    role: 'Engenheiro de QA',
    category: 'engineering',
    description: 'Cria planos de teste, testes automatizados (unit, integração, E2E com Playwright), identifica bugs e mede cobertura.',
    capabilities: ['Testes unitários', 'E2E (Playwright)', 'Plano de testes', 'Cobertura de código'],
    typical_use_cases: ['Plano de teste para feature', 'Estratégia de cobertura', 'Bug investigation'],
  },
  {
    name: 'security',
    role: 'Analista de Segurança',
    category: 'security',
    description: 'Auditoria de segurança com análise de vulnerabilidades, OWASP Top 10, threat modeling, compliance com LGPD/GDPR.',
    capabilities: ['OWASP Top 10', 'Threat modeling', 'Pentest (DAST/SAST)', 'Compliance (LGPD/GDPR)'],
    typical_use_cases: ['Auditoria de código', 'Threat model', 'Setup HTTPS/CSP', 'DPIA'],
  },
  {
    name: 'devops',
    role: 'Engenheiro DevOps',
    category: 'engineering',
    description: 'CI/CD com GitHub Actions, containers Docker, Kubernetes, infraestrutura como código (Terraform), monitoramento com Prometheus/Grafana.',
    capabilities: ['Docker/K8s', 'GitHub Actions', 'Terraform', 'Prometheus/Grafana'],
    typical_use_cases: ['Setup CI/CD', 'Pipeline de deploy', 'Monitoramento', 'Infraestrutura cloud'],
  },
  {
    name: 'data_engineer',
    role: 'Engenheiro de Dados',
    category: 'data',
    description: 'ETL, data warehousing com Airflow/dbt, modelagem dimensional (star schema), data quality e migração entre fontes.',
    capabilities: ['Airflow/dbt', 'BigQuery/Snowflake', 'Schema dimensional', 'Data quality'],
    typical_use_cases: ['Pipeline ETL', 'Modelagem dimensional', 'Migração de dados'],
  },
  {
    name: 'code_reviewer',
    role: 'Revisor de Código',
    category: 'engineering',
    description: 'Revisa PRs, identifica code smells, sugere refatorações baseadas em design patterns e style guides.',
    capabilities: ['Code review', 'Refactoring patterns', 'Design patterns', 'Style guide enforcement'],
    typical_use_cases: ['Review de PR', 'Refatoração segura', 'Code smells'],
  },
  {
    name: 'disaster_recovery',
    role: 'Agente de Disaster Recovery',
    category: 'security',
    description: 'Plano de continuidade de negócio (BCP), estratégia de backup/restore, RTO/RPO, runbooks de incidentes.',
    capabilities: ['Backup strategies', 'Failover', 'RTO/RPO', 'Runbooks'],
    typical_use_cases: ['Plano de DR', 'Teste de restore', 'Documentação de incidentes'],
  },
  {
    name: 'dpo',
    role: 'Data Protection Officer',
    category: 'security',
    description: 'Compliance com LGPD/GDPR, privacy by design, DPIA (Data Protection Impact Assessment), gestão de consentimento.',
    capabilities: ['LGPD/GDPR', 'Privacy by design', 'DPIA', 'Consent management'],
    typical_use_cases: ['Auditoria LGPD', 'Política de privacidade', 'DPIA', 'Gestão de consentimento'],
  },
  {
    name: 'copywriter',
    role: 'Copywriter',
    category: 'business',
    description: 'Redação de copy persuasiva para landing pages, email marketing, conteúdo SEO e storytelling.',
    capabilities: ['Copy persuasiva', 'Email marketing', 'SEO writing', 'Storytelling'],
    typical_use_cases: ['Landing page', 'Email sequence', 'Posts de blog'],
  },
  {
    name: 'ads_copywriter',
    role: 'Copywriter de Ads',
    category: 'business',
    description: 'Copy especializada para anúncios pagos (Google Ads, Meta Ads), headlines, CTAs, A/B testing de copy.',
    capabilities: ['Google Ads copy', 'Meta Ads copy', 'A/B testing', 'CTR optimization'],
    typical_use_cases: ['Campanha de ads', 'Headlines', 'Variações de copy'],
  },
  {
    name: 'supervisor',
    role: 'Supervisor de Agentes',
    category: 'engineering',
    description: 'Coordena múltiplos agentes, monitora qualidade das respostas, intervém quando há conflitos.',
    capabilities: ['Coordenação de agentes', 'Quality monitoring', 'Conflict resolution'],
    typical_use_cases: ['Orquestração complexa', 'Resolução de conflitos entre agentes', 'Quality assurance'],
  },
  {
    name: 'triage',
    role: 'Agente de Triagem',
    category: 'engineering',
    description: 'Classifica requests recebidos, identifica urgência, roteia para o agente especialista correto.',
    capabilities: ['Classificação', 'Roteamento', 'Detecção de urgência'],
    typical_use_cases: ['Triagem inicial', 'Classificação de bugs', 'Roteamento automático'],
  },
  {
    name: 'session_archivist',
    role: 'Arquivista de Sessões',
    category: 'data',
    description: 'Consolida e arquiva sessões finalizadas no cofre do conhecimento (RAG long-term memory).',
    capabilities: ['Consolidação', 'Indexação RAG', 'Compressão de contexto'],
    typical_use_cases: ['Arquivar sessão', 'Atualizar knowledge base', 'Compressão para long-term'],
  },
  {
    name: 'structure',
    role: 'Agente Estruturador',
    category: 'business',
    description: 'Organiza e estrutura documentação técnica (READMEs, ADRs, specs) em formatos padronizados.',
    capabilities: ['Documentação técnica', 'Estruturação', 'Markdown/JSON/YAML'],
    typical_use_cases: ['Criar README', 'Estruturar ADR', 'Spec técnica'],
  },
  {
    name: 'ui_artist',
    role: 'UI Artist',
    category: 'business',
    description: 'Design de interfaces (UI), componentes visuais, design system, prototipagem.',
    capabilities: ['UI design', 'Design system', 'Prototipagem', 'Acessibilidade'],
    typical_use_cases: ['Mockup de tela', 'Componente UI', 'Design system'],
  },
  {
    name: 'freelancer',
    role: 'Agente Freelancer',
    category: 'business',
    description: 'Executa tarefas pontuais e específicas que não exigem orquestração complexa.',
    capabilities: ['Tarefas pontuais', 'Execução rápida', 'Fallback para specialists'],
    typical_use_cases: ['Tarefa única', 'Quick fix', 'Helper pontual'],
  },
  {
    name: 'swarm_contractor',
    role: 'Contratante de Swarm',
    category: 'engineering',
    description: 'Contrata e gerencia múltiplos agentes em paralelo (swarm) para tarefas distribuídas.',
    capabilities: ['Swarm management', 'Paralelização', 'Consolidação de resultados'],
    typical_use_cases: ['Tarefa distribuída', 'Processamento paralelo', 'Agregação de resultados'],
  },
];

export const agentsApi = {
  async list(): Promise<AgentInfo[]> {
    return AGENTS_CATALOG;
  },

  async getOrchestratorStatus(sessionId: string) {
    const res = await fetch(`/api/orchestrate/${sessionId}/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async startOrchestrator(taskDescription: string): Promise<{ session_id: string }> {
    const res = await fetch('/api/orchestrate/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_description: taskDescription }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};
