import { FormEvent, ReactNode, useCallback, useEffect, useState } from 'react';
import { Activity, BookOpen, CheckCircle2, ClipboardCheck, ListChecks, RefreshCw, Search, SlidersHorizontal } from 'lucide-react';
import { Acao, evolucaoApi, EvolucaoApiError, Fato, linhas, Perfil, Registro, texto, urlPublica, VisaoEvolucao } from './evolucao.api';
import './evolucao.styles.css';

type Aba = 'tarefas' | 'memoria' | 'avaliacoes' | 'aprovacoes' | 'feedback' | 'prospeccao';
type Executar = <T>(label: string, action: () => Promise<T>, done?: (result: T) => void) => Promise<void>;
type PainelProps = { data: VisaoEvolucao; project: string; executar: Executar; busy: boolean };
const abas: { id: Aba; nome: string; icon: typeof Activity }[] = [
  { id: 'tarefas', nome: 'Tarefas e orçamento', icon: ListChecks },
  { id: 'memoria', nome: 'Memória', icon: BookOpen },
  { id: 'avaliacoes', nome: 'Avaliações e skills', icon: SlidersHorizontal },
  { id: 'aprovacoes', nome: 'Aprovações', icon: ClipboardCheck },
  { id: 'feedback', nome: 'Correções', icon: CheckCircle2 },
  { id: 'prospeccao', nome: 'Prospecção', icon: Search },
];
const estados: Record<string, string> = {
  queued: 'Na fila', blocked: 'Bloqueada', running: 'Em execução', completed: 'Concluída',
  failed: 'Falhou', retry_wait: 'Aguardando tentativa', uncertain: 'Resultado incerto', idle: 'Fila vazia',
  prepared: 'Para revisar', approved: 'Aprovado', rejected: 'Rejeitado', draft: 'Rascunho',
  passed: 'Aprovada', published_unverified: 'Publicado, sem verificação', provider_verified: 'Verificado pelo provedor',
  provider_rejected: 'Rejeitado pelo provedor', provider_unknown: 'Verificação inconclusiva',
};
const dataHora = (value: number | string) => new Date(typeof value === 'number' ? value * 1000 : value).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
const numero = (value: number) => value.toLocaleString('pt-BR');
const campo = (form: FormData, name: string) => String(form.get(name) || '').trim();
const inteiro = (form: FormData, name: string) => Number(campo(form, name));
const id = () => crypto.randomUUID();
const opcoesUF = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ');

function MensagemVazia({ children }: { children: ReactNode }) { return <p className="ev-vazio">{children}</p>; }
function Detalhes({ value, title = 'Ver registro completo' }: { value: unknown; title?: string }) {
  return <details className="ev-detalhes"><summary>{title}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}
function LinkFonte({ value, children = 'Abrir fonte' }: { value: string; children?: ReactNode }) {
  const url = urlPublica(value);
  return url ? <a href={url} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{value}</span>;
}
function Campo({ label, children }: { label: string; children: ReactNode }) {
  return <label className="ev-campo"><span>{label}</span>{children}</label>;
}
function Estado({ value }: { value: string }) { return <span className={`ev-estado ev-estado--${value}`}>{estados[value] || value}</span>; }
function Card({ title, children, description }: { title: string; children: ReactNode; description?: string }) {
  return <section className="ev-card"><h2>{title}</h2>{description && <p className="ev-ajuda">{description}</p>}{children}</section>;
}

export function EvolucaoPage() {
  const [project, setProject] = useState('kothar');
  const [aba, setAba] = useState<Aba>('tarefas');
  const [data, setData] = useState<VisaoEvolucao | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState('');
  const [notice, setNotice] = useState<{ error: boolean; text: string } | null>(null);
  const carregar = useCallback(async (signal?: AbortSignal) => {
    const result = await evolucaoApi<VisaoEvolucao>(project, '', 'GET', undefined, signal);
    setData(result);
  }, [project]);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setLoading(true); setNotice(null);
    carregar(controller.signal).catch(error => {
      if (!controller.signal.aborted) setNotice({ error: true, text: error instanceof Error ? error.message : 'Falha ao carregar o painel.' });
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [carregar]);

  const executar: Executar = async (label, action, done) => {
    if (pending) return;
    setPending(label); setNotice(null);
    try {
      const result = await action();
      done?.(result);
      await carregar();
      const record = result && typeof result === 'object' ? result as Record<string, unknown> : {};
      const failed = ['failed', 'blocked', 'uncertain'].includes(texto(record.status)) || record.all_passed === false;
      setNotice({ error: failed, text: failed ? `${label}: execução registrada com falha ou bloqueio. Confira os resultados.` : `${label}: operação concluída.` });
    } catch (error) {
      setNotice({ error: true, text: error instanceof Error ? error.message : 'Falha ao executar a operação.' });
    } finally { setPending(''); }
  };
  const busy = Boolean(pending) || loading;
  const props = data ? { data, project, executar, busy } : null;
  return <div className="ev-pagina">
    <header className="ev-cabecalho"><div><span className="ev-sobretitulo">OPERAÇÃO DO KOTHAR</span><h1>Evolução</h1><p>Execute, verifique e acompanhe melhorias com evidências.</p></div>
      <button type="button" className="ev-secundario" disabled={busy} onClick={() => executar('Atualizar dados', async () => undefined)}><RefreshCw size={16} />Atualizar</button>
    </header>
    <form className="ev-projeto" onSubmit={event => { event.preventDefault(); const next = campo(new FormData(event.currentTarget), 'project'); if (next !== project) setProject(next); }}>
      <Campo label="Projeto"><input name="project" defaultValue={project} required pattern="[A-Za-z0-9][A-Za-z0-9_.-]*" maxLength={100} title="Comece com letra ou número; use letras, números, ponto, hífen ou sublinhado." disabled={busy} /></Campo>
      <button className="ev-secundario" disabled={busy}>Abrir projeto</button><p className="ev-ajuda">Dados e operações separados por projeto e sessão.</p>
    </form>
    {notice && <p className={`ev-aviso ${notice.error ? 'ev-aviso--erro' : ''}`} role={notice.error ? 'alert' : 'status'}>{notice.text}</p>}
    {pending && <p role="status" className="ev-pendente">{pending}…</p>}
    {loading && <p role="status" className="ev-vazio">Carregando tarefas, evidências e limites…</p>}
    {!loading && !data && <MensagemVazia>O painel está indisponível. Use Atualizar para tentar novamente.</MensagemVazia>}
    {data && props && <>
      <div className="ev-resumo" aria-label="Resumo do projeto">
        {[['Tarefas ativas', data.tasks.filter(t => !['completed', 'failed'].includes(t.status)).length], ['Fatos válidos', data.facts.length], ['Rascunhos para revisar', data.actions.filter(a => a.status === 'prepared').length], ['Empresas encontradas', data.prospects.length]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </div>
      <nav className="ev-abas" aria-label="Áreas de evolução">{abas.map(item => <button type="button" key={item.id} aria-current={aba === item.id ? 'page' : undefined} onClick={() => setAba(item.id)}><item.icon size={16} />{item.nome}</button>)}</nav>
      <fieldset className="ev-conteudo" disabled={busy} key={project} aria-busy={busy}>
        <legend className="ev-sr">{abas.find(item => item.id === aba)?.nome}</legend>
        {aba === 'tarefas' && <Tarefas {...props} />}
        {aba === 'memoria' && <Memoria {...props} />}
        {aba === 'avaliacoes' && <Avaliacoes {...props} />}
        {aba === 'aprovacoes' && <Aprovacoes {...props} />}
        {aba === 'feedback' && <Feedback {...props} />}
        {aba === 'prospeccao' && <Prospeccao {...props} />}
      </fieldset>
    </>}
  </div>;
}

function BuscaCampos() {
  return <div className="ev-grade-campos">
    <Campo label="Segmento"><select name="category" defaultValue="clinica"><option value="clinica">Clínicas</option><option value="dentista">Dentistas</option><option value="restaurante">Restaurantes</option><option value="academia">Academias</option><option value="farmacia">Farmácias</option><option value="hotel">Hotéis</option><option value="agencia de marketing">Agências de marketing</option><option value="saas">SaaS / tecnologia</option></select></Campo>
    <Campo label="Município"><input name="city" required minLength={2} maxLength={100} /></Campo>
    <Campo label="UF"><select name="state" defaultValue="SP">{opcoesUF.map(uf => <option key={uf}>{uf}</option>)}</select></Campo>
    <Campo label="Raio em metros"><input name="radius_m" type="number" min={100} max={10000} step={100} defaultValue={3000} required /></Campo>
    <Campo label="Máximo de empresas"><input name="limit" type="number" min={1} max={25} defaultValue={10} required /></Campo>
  </div>;
}
function buscaPayload(form: FormData) { return { category: campo(form, 'category'), city: campo(form, 'city'), state: campo(form, 'state'), radius_m: inteiro(form, 'radius_m'), limit: inteiro(form, 'limit') }; }

function Tarefas({ data, project, executar }: PainelProps) {
  const [operation, setOperation] = useState('skills');
  const [resultado, setResultado] = useState<unknown>();
  const criar = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const payload = operation === 'skills' ? { operation, context: campo(form, 'context'), budget_tokens: 1500 }
      : operation === 'evaluation' ? { operation, use_canonical: true }
      : operation === 'discovery' ? { operation, request: buscaPayload(form) }
      : { operation, prospect_id: campo(form, 'prospect_id') };
    executar('Criar tarefa', () => evolucaoApi(project, '/tasks', 'POST', {
      title: campo(form, 'title'), dedupe_key: id(), category: campo(form, 'task_category'),
      priority: inteiro(form, 'priority'), max_attempts: inteiro(form, 'max_attempts'),
      retry_safe: form.get('retry_safe') === 'on', dependencies: form.getAll('dependencies'), payload,
    }));
  };
  return <div className="ev-grade">
    <Card title="Fila de execução" description="Correções e retomadas têm precedência. Dependências e resultados ficam persistidos.">
      <button type="button" onClick={() => executar('Executar próxima tarefa', () => evolucaoApi(project, '/tasks/run', 'POST'), setResultado)} disabled={!data.tasks.some(t => ['queued', 'retry_wait', 'blocked'].includes(t.status))}>Executar próxima tarefa</button>
      {resultado !== undefined && <Detalhes value={resultado} title="Resultado da execução — confira o estado" />}
      <div className="ev-lista">{data.tasks.length ? data.tasks.map(task => <article className="ev-item" key={task.id}><div className="ev-item-topo"><h3>{task.title}</h3><Estado value={task.status} /></div><p>Prioridade {task.priority} · Tentativas {task.attempts}/{task.max_attempts} · {task.dependencies.length} dependências</p><Detalhes value={task} /></article>) : <MensagemVazia>Nenhuma tarefa criada. Selecione uma operação no formulário.</MensagemVazia>}</div>
    </Card>
    <Card title="Criar tarefa"><form onSubmit={criar} className="ev-form">
      <Campo label="Título"><input name="title" required maxLength={300} /></Campo>
      <div className="ev-grade-campos"><Campo label="Categoria"><select name="task_category"><option value="repair">Correção</option><option value="resume">Retomada</option><option value="new">Nova tarefa</option></select></Campo><Campo label="Prioridade (0 a 100)"><input name="priority" type="number" required min={0} max={100} defaultValue={50} /></Campo></div>
      <Campo label="Operação"><select value={operation} onChange={event => setOperation(event.target.value)}><option value="skills">Selecionar skills</option><option value="evaluation" disabled={!data.capabilities.evaluations}>Avaliar conjunto canônico</option><option value="discovery" disabled={!data.capabilities.prospecting}>Descobrir empresas</option><option value="profile" disabled={!data.capabilities.prospecting || !data.prospects.length}>Investigar site de empresa</option></select></Campo>
      {operation === 'skills' && <Campo label="Contexto da tarefa"><textarea name="context" required maxLength={8000} rows={3} /></Campo>}
      {operation === 'discovery' && <BuscaCampos />}
      {operation === 'profile' && <Campo label="Empresa"><select name="prospect_id" required>{data.prospects.map(p => <option key={p.id} value={p.id}>{p.company}</option>)}</select></Campo>}
      <Campo label="Dependências (opcional; selecione com Ctrl ou Command)"><select name="dependencies" multiple size={3}>{data.tasks.map(task => <option key={task.id} value={task.id}>{task.title} — {estados[task.status] || task.status}</option>)}</select></Campo>
      <Campo label="Máximo de tentativas"><input name="max_attempts" type="number" min={1} max={5} defaultValue={1} required /></Campo>
      <label className="ev-check"><input name="retry_safe" type="checkbox" />Permitir retomada automática se a operação for segura para repetir</label>
      <button>Criar tarefa</button>
    </form></Card>
    <Card title="Orçamento do projeto" description="Tokens, chamadas e microunidades são limites independentes. O valor de custo usa a unidade configurada no servidor.">
      {!data.budget && <MensagemVazia>Configure os limites para liberar operações com consumo.</MensagemVazia>}
      {data.budget && <div className="ev-consumo">{(['tokens', 'calls', 'cost_microunits'] as const).map(metric => {
        const budget = data.budget!; const used = budget.spent[metric] + budget.reserved[metric];
        return <div key={metric}><span>{metric === 'tokens' ? 'Tokens' : metric === 'calls' ? 'Chamadas' : 'Custo (microunidades)'}</span><strong>{numero(used)} / {numero(budget.limits[metric])}</strong><progress max={budget.limits[metric] || 1} value={used} aria-label={`Consumo de ${metric}`} /><small>Consumido: {numero(budget.spent[metric])} · Reservado: {numero(budget.reserved[metric])}</small></div>;
      })}</div>}
      <form className="ev-form" key={data.budget?.revision ?? 'new'} onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); executar('Salvar orçamento', () => evolucaoApi(project, '/budget', 'PUT', { tokens: inteiro(form, 'tokens'), calls: inteiro(form, 'calls'), cost_microunits: inteiro(form, 'cost_microunits') })); }}>
        <div className="ev-grade-campos"><Campo label="Limite de tokens"><input name="tokens" type="number" min={0} max={1000000000} defaultValue={data.budget?.limits.tokens ?? 0} required /></Campo><Campo label="Limite de chamadas"><input name="calls" type="number" min={0} max={1000000} defaultValue={data.budget?.limits.calls ?? 0} required /></Campo><Campo label="Limite de custo em microunidades"><input name="cost_microunits" type="number" min={0} max={1000000000000} defaultValue={data.budget?.limits.cost_microunits ?? 0} required /></Campo></div><button>Salvar limites</button>
      </form>
    </Card>
  </div>;
}

function Memoria({ data, project, executar }: PainelProps) {
  const [editing, setEditing] = useState<Fato | null>(null);
  const salvar = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget); const expires = campo(form, 'expires_at');
    const payload = { content: campo(form, 'content'), source: campo(form, 'source'), category: campo(form, 'category'), confidence: inteiro(form, 'confidence') / 100, observed_at: Math.floor(new Date(campo(form, 'observed_at')).getTime() / 1000), expires_at: expires ? Math.floor(new Date(expires).getTime() / 1000) : null };
    executar(editing ? 'Corrigir informação' : 'Registrar informação', () => evolucaoApi(project, editing ? `/facts/${encodeURIComponent(editing.id)}?revision=${editing.revision}` : '/facts', editing ? 'PUT' : 'POST', payload), () => setEditing(null));
  };
  const localDate = (timestamp: number) => { const date = new Date(timestamp * 1000); date.setMinutes(date.getMinutes() - date.getTimezoneOffset()); return date.toISOString().slice(0, 16); };
  return <div className="ev-grade"><Card title="Memória com fonte" description="Somente informações ativas e válidas aparecem aqui. Correções preservam o vínculo com a versão anterior.">
    <div className="ev-lista">{data.facts.length ? data.facts.map(fact => <article key={fact.id} className="ev-item"><h3>{fact.category}</h3><p className="ev-texto">{fact.content}</p><p>Confiança: {Math.round(fact.confidence * 100)}% · Observado em {dataHora(fact.observed_at)}</p><p>Validade: {fact.expires_at ? dataHora(fact.expires_at) : 'Sem expiração definida'}</p><LinkFonte value={fact.source} /><div className="ev-acoes"><button type="button" className="ev-secundario" onClick={() => setEditing(fact)}>Corrigir</button><button type="button" className="ev-perigo" onClick={() => { if (window.confirm('Revogar esta informação e remover seu conteúdo da memória ativa?')) executar('Revogar informação', () => evolucaoApi(project, `/facts/${encodeURIComponent(fact.id)}?revision=${fact.revision}`, 'DELETE'), () => { if (editing?.id === fact.id) setEditing(null); }); }}>Revogar</button></div></article>) : <MensagemVazia>Nenhuma informação válida registrada neste projeto.</MensagemVazia>}</div>
  </Card><Card title={editing ? 'Corrigir informação' : 'Registrar informação'}><form className="ev-form" key={editing?.id ?? 'new'} onSubmit={salvar}>
    <Campo label="Informação ou decisão"><textarea name="content" defaultValue={editing?.content} rows={4} maxLength={8000} required /></Campo><Campo label="Fonte ou referência"><input name="source" defaultValue={editing?.source} maxLength={2048} required /></Campo>
    <Campo label="Categoria"><input name="category" defaultValue={editing?.category ?? 'decision'} maxLength={80} required /></Campo><Campo label="Confiança de 0 a 100%"><input name="confidence" type="number" min={0} max={100} defaultValue={editing ? Math.round(editing.confidence * 100) : 80} required /></Campo>
    <Campo label="Data de observação"><input name="observed_at" type="datetime-local" defaultValue={localDate(editing?.observed_at ?? Math.floor(Date.now() / 1000))} required /></Campo><Campo label="Expira em (opcional)"><input name="expires_at" type="datetime-local" defaultValue={editing?.expires_at ? localDate(editing.expires_at) : ''} /></Campo>
    <div className="ev-acoes"><button>{editing ? 'Salvar correção' : 'Registrar informação'}</button>{editing && <button type="button" className="ev-secundario" onClick={() => setEditing(null)}>Cancelar edição</button>}</div>
  </form></Card></div>;
}

function Avaliacoes({ data, project, executar }: PainelProps) {
  const [selection, setSelection] = useState<unknown>();
  const [lastReport, setLastReport] = useState<Registro | null>(null);
  return <div className="ev-grade"><Card title="Avaliações com execução" description="Executa o modelo configurado, verifica os critérios e registra consumo e rastros. Um resultado bloqueado não é aprovação.">
    {!data.capabilities.evaluations && <p className="ev-aviso">Avaliações indisponíveis: configure o modelo executor no servidor.</p>}
    <button type="button" disabled={!data.capabilities.evaluations || !data.budget} onClick={() => executar('Executar avaliação canônica', () => evolucaoApi<Registro>(project, '/evaluations', 'POST', { use_canonical: true }), setLastReport)}>Executar conjunto canônico</button>
    <form className="ev-form ev-separador" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); if (!linhas(campo(form, 'expected')).length && !linhas(campo(form, 'forbidden')).length) { const input = event.currentTarget.elements.namedItem('expected') as HTMLTextAreaElement; input.setCustomValidity('Informe pelo menos um trecho esperado ou proibido.'); input.reportValidity(); return; } executar('Executar caso de avaliação', () => evolucaoApi<Registro>(project, '/evaluations', 'POST', { cases: [{ id: id(), project_id: project, prompt: campo(form, 'prompt'), expected_contains: linhas(campo(form, 'expected')), forbidden_contains: linhas(campo(form, 'forbidden')) }] }), setLastReport); }}>
      <Campo label="Tarefa para o modelo"><textarea name="prompt" rows={3} required maxLength={32000} /></Campo><Campo label="Trechos esperados (um por linha)"><textarea name="expected" rows={2} maxLength={8000} onInput={event => event.currentTarget.setCustomValidity('')} /></Campo><Campo label="Trechos proibidos (um por linha)"><textarea name="forbidden" rows={2} maxLength={8000} onInput={event => { const expected = event.currentTarget.form?.elements.namedItem('expected') as HTMLTextAreaElement | null; expected?.setCustomValidity(''); }} /></Campo><p className="ev-ajuda">Informe pelo menos um trecho esperado ou proibido. Os critérios verificam a resposta da execução.</p><button disabled={!data.capabilities.evaluations || !data.budget}>Executar caso</button>
    </form>{lastReport && <Detalhes value={lastReport} title="Resultado da última avaliação" />}
    <div className="ev-lista">{data.evaluations.length ? data.evaluations.map(report => <article className="ev-item" key={report.id}><h3>Avaliação {report.id.slice(0, 12)}</h3><p>Aprovados: {String(report.passed ?? 0)} · Falhas: {String(report.failed ?? 0)} · Bloqueados: {String(report.blocked ?? 0)}</p><Detalhes value={report} title="Critérios, execução e consumo" /></article>) : <MensagemVazia>Nenhuma avaliação executada neste projeto.</MensagemVazia>}</div>
  </Card><Card title="Seleção de skills" description={`${data.skills_metadata.length} habilidades catalogadas. Selecionar não comprova aplicação nem aprovação dos controles.`}>
    <form className="ev-form" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); executar('Selecionar habilidades', () => evolucaoApi(project, '/skills/select', 'POST', { context: campo(form, 'context'), budget_tokens: inteiro(form, 'budget_tokens') }), setSelection); }}><Campo label="Contexto e objetivo"><textarea name="context" rows={4} maxLength={8000} required /></Campo><Campo label="Orçamento de contexto em tokens"><input type="number" name="budget_tokens" min={100} max={16000} defaultValue={1500} required /></Campo><button>Selecionar habilidades</button></form>
    {selection !== undefined && <Detalhes value={selection} title="Seleção, estimativa e auditoria" />}<details className="ev-detalhes"><summary>Consultar catálogo de habilidades</summary><ul className="ev-catalogo">{data.skills_metadata.map(skill => <li key={skill.name}><strong>{skill.name}</strong><p>{skill.description}</p><small>{numero(skill.estimated_tokens)} tokens estimados · {skill.version}</small></li>)}</ul></details>
  </Card></div>;
}

function Aprovacoes({ data, project, executar }: PainelProps) {
  const decidir = (action: Acao, decision: string) => executar(decision === 'approve' ? 'Aprovar rascunho' : 'Rejeitar rascunho', () => evolucaoApi(project, `/actions/${encodeURIComponent(action.id)}/decision`, 'POST', { payload_hash: action.payload_hash, scope: action.scope, expires_at: action.expires_at, decision }));
  return <Card title="Revisão de ações" description="A aprovação vale para o conteúdo exibido, seu escopo e sua validade. Aprovar um rascunho não envia a mensagem.">
    {!data.capabilities.external_dispatch && <p className="ev-aviso">Envio externo indisponível. As ações deste painel são rascunhos para revisão.</p>}
    <div className="ev-lista">{data.actions.length ? data.actions.map(action => { const expired = action.expires_at * 1000 <= Date.now(); return <article key={action.id} className="ev-item"><div className="ev-item-topo"><h3>{action.review}</h3><Estado value={action.status} /></div><p>Escopo: {action.scope} · {expired ? 'Expirou em' : 'Válido até'} {dataHora(action.expires_at)}</p>{typeof action.payload.subject === 'string' && <h4>{action.payload.subject}</h4>}{typeof action.payload.body === 'string' && <p className="ev-texto">{action.payload.body}</p>}<Detalhes value={action.payload} title="Revisar todo o conteúdo da ação" /><div className="ev-acoes"><button type="button" disabled={expired || !['prepared', 'approved'].includes(action.status)} onClick={() => decidir(action, 'approve')}>Aprovar rascunho</button><button type="button" className="ev-perigo" disabled={!['prepared', 'approved'].includes(action.status)} onClick={() => decidir(action, 'reject')}>Rejeitar</button></div></article>; }) : <MensagemVazia>Nenhuma ação preparada. Os rascunhos de prospecção aparecerão aqui para revisão.</MensagemVazia>}</div>
  </Card>;
}

function Feedback({ data, project, executar }: PainelProps) {
  return <div className="ev-grade"><Card title="Registrar uma correção" description="A correção gera uma proposta versionada e um caso de regressão. Instruções não são alteradas automaticamente."><form className="ev-form" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); executar('Registrar correção', () => evolucaoApi(project, '/feedback', 'POST', { id: id(), project_id: project, prompt: campo(form, 'prompt'), observed_response: campo(form, 'observed_response'), correction: campo(form, 'correction'), expected_contains: linhas(campo(form, 'expected')), forbidden_contains: linhas(campo(form, 'forbidden')) })); }}>
    <Campo label="Pedido original"><textarea name="prompt" required maxLength={32000} rows={3} /></Campo><Campo label="Resposta observada"><textarea name="observed_response" required maxLength={32000} rows={3} /></Campo><Campo label="Comportamento correto"><textarea name="correction" required maxLength={4000} rows={3} /></Campo><Campo label="Trechos esperados na regressão (um por linha)"><textarea name="expected" maxLength={8000} rows={2} /></Campo><Campo label="Trechos proibidos na regressão (um por linha)"><textarea name="forbidden" maxLength={8000} rows={2} /></Campo><button>Gerar proposta e caso de regressão</button>
  </form></Card><Card title="Propostas registradas"><div className="ev-lista">{data.feedback.length ? data.feedback.map(item => <article className="ev-item" key={item.id}><div className="ev-item-topo"><h3>Versão {String(item.version ?? 1)}</h3><Estado value={texto(item.status) || 'draft'} /></div><p className="ev-texto">{texto(item.proposed_instruction)}</p><Detalhes value={item} title="Proposta, origem e caso de regressão" />{data.capabilities.evaluations && <button type="button" className="ev-secundario" disabled={!data.budget} onClick={() => executar('Avaliar regressão da correção', () => evolucaoApi(project, `/feedback/${encodeURIComponent(item.id)}/evaluate`, 'POST'))}>Avaliar regressão</button>}</article>) : <MensagemVazia>Nenhuma proposta gerada neste projeto.</MensagemVazia>}</div></Card></div>;
}

function Prospeccao({ data, project, executar }: PainelProps) {
  const [perfil, setPerfil] = useState<{ id: string; value: Perfil } | null>(null);
  const [discovery, setDiscovery] = useState<unknown>();
  const [qualification, setQualification] = useState<unknown>();
  const [draft, setDraft] = useState<unknown>();
  const [bant, setBant] = useState<Record<string, string>>({ budget: 'unknown', authority: 'unknown', need: 'unknown', timing: 'unknown' });
  const abrir = (prospectId: string, collect: boolean) => executar(collect ? 'Investigar site' : 'Abrir perfil', async () => {
    try {
      const result = await evolucaoApi<Perfil | { profile: Perfil }>(project, `/prospects/${encodeURIComponent(prospectId)}/profile`, collect ? 'POST' : 'GET');
      return { id: prospectId, value: 'profile' in result ? result.profile : result };
    } catch (error) {
      if (error instanceof EvolucaoApiError && error.status === 404 && !collect) throw new Error('Este perfil ainda não foi coletado. Use Investigar site.');
      throw error;
    }
  }, result => { setPerfil(result); setQualification(undefined); setDraft(undefined); setBant({ budget: 'unknown', authority: 'unknown', need: 'unknown', timing: 'unknown' }); });
  return <div className="ev-grade"><Card title="Descobrir empresas no Brasil" description="Busca por segmento e localidade no OpenStreetMap. A cobertura é uma amostra e não comprova intenção de compra.">
    {!data.capabilities.prospecting && <p className="ev-aviso">Descoberta e investigação externas precisam ser habilitadas no servidor.</p>}
    {!data.budget && <p className="ev-ajuda">Configure primeiro o orçamento em Tarefas e orçamento.</p>}
    <form className="ev-form" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); executar('Descobrir empresas', () => evolucaoApi(project, '/prospects/discover', 'POST', buscaPayload(form)), setDiscovery); }}><BuscaCampos /><button disabled={!data.capabilities.prospecting || !data.budget}>Buscar empresas</button></form>{discovery !== undefined && <Detalhes value={discovery} title="Resultado, cobertura e atribuição da busca" />}<p className="ev-ajuda">© OpenStreetMap contributors — ODbL 1.0. Registros públicos não representam consentimento para contato.</p>
    <div className="ev-lista">{data.prospects.length ? data.prospects.map(prospect => <article key={prospect.id} className={`ev-item ${perfil?.id === prospect.id ? 'ev-item--selecionado' : ''}`}><h3>{prospect.company}</h3><p>{prospect.domain}</p><p>{prospect.signal}</p><p>Próximo passo: {prospect.next_step}</p><LinkFonte value={prospect.source} /><div className="ev-acoes"><button type="button" className="ev-secundario" onClick={() => abrir(prospect.id, false)}>Abrir perfil</button><button type="button" disabled={!data.capabilities.prospecting || !data.budget || prospect.domain.startsWith('no-site:')} onClick={() => abrir(prospect.id, true)}>Investigar site</button></div></article>) : <MensagemVazia>Nenhuma empresa descoberta neste projeto.</MensagemVazia>}</div>
  </Card><div className="ev-pilha">{perfil ? <>
    <Card title={perfil.value.business.name} description={perfil.value.coverage}><p className="ev-ajuda">Perfil válido até {dataHora(perfil.value.expires_at)}</p>
      <h3>Sinais observados</h3>{perfil.value.signals.length ? perfil.value.signals.map(signal => <article className="ev-item" key={signal.code}><h4>{signal.label}</h4><p>{signal.evidence.observation}</p><p className="ev-ajuda">{signal.limitation}</p><p>Observado em {dataHora(signal.evidence.observed_at)}</p><LinkFonte value={signal.evidence.source_url} /></article>) : <MensagemVazia>Nenhum sinal identificado nesta página.</MensagemVazia>}
      <h3>Contatos publicados</h3>{perfil.value.contacts.length ? perfil.value.contacts.map(contact => <article className="ev-item" key={contact.email}><p>{contact.email}</p><Estado value={contact.status} /><p><LinkFonte value={contact.source_url} /></p></article>) : <MensagemVazia>Nenhum contato público encontrado.</MensagemVazia>}
    </Card>
    <Card title="Qualificar oportunidade" description="Aderência ao público e BANT são avaliados separadamente. Confirmações exigem evidência informada."><form className="ev-form" key={perfil.id} onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); const answers = Object.fromEntries(Object.keys(bant).map(key => [key, { status: bant[key], evidence: campo(form, `${key}_evidence`) || null }])); executar('Qualificar oportunidade', () => evolucaoApi(project, `/prospects/${encodeURIComponent(perfil.id)}/qualify`, 'POST', { icp: { target_categories: linhas(campo(form, 'categories')), target_states: [campo(form, 'state')], desired_signals: form.getAll('signals') }, bant: answers }), setQualification); }}>
      <Campo label="Segmentos desejados (um por linha)"><textarea name="categories" rows={2} required defaultValue={perfil.value.business.category} maxLength={1200} /></Campo><Campo label="UF desejada"><select name="state" defaultValue={perfil.value.business.state}>{opcoesUF.map(uf => <option key={uf}>{uf}</option>)}</select></Campo>
      {perfil.value.signals.length > 0 && <Campo label="Sinais desejados (opcional; selecione com Ctrl ou Command)"><select name="signals" multiple size={Math.min(4, perfil.value.signals.length)}>{perfil.value.signals.map(signal => <option key={signal.code} value={signal.code}>{signal.label}</option>)}</select></Campo>}
      {Object.entries({ budget: 'Orçamento', authority: 'Autoridade para decidir', need: 'Necessidade', timing: 'Prazo' }).map(([key, label]) => <div className="ev-grade-campos" key={key}><Campo label={label}><select value={bant[key]} onChange={event => setBant(previous => ({ ...previous, [key]: event.target.value }))}><option value="unknown">Desconhecido</option><option value="confirmed">Confirmado</option><option value="negative">Negativo</option></select></Campo><Campo label={`Evidência — ${label.toLowerCase()}`}><input name={`${key}_evidence`} maxLength={500} required={bant[key] !== 'unknown'} /></Campo></div>)}<button>Calcular aderência e BANT</button>
    </form>{qualification !== undefined && <Detalhes value={qualification} title="Aderência, evidências e próximas perguntas" />}</Card>
    <Card title="Preparar abordagem" description="O rascunho usa observações do perfil e segue para a fila de revisão."><form className="ev-form" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); executar('Preparar rascunho', () => evolucaoApi(project, `/prospects/${encodeURIComponent(perfil.id)}/draft`, 'POST', { offer: campo(form, 'offer'), signal_code: campo(form, 'signal') || null, objection: campo(form, 'objection') || null }), setDraft); }}><Campo label="O que você oferece"><textarea name="offer" rows={3} required minLength={3} maxLength={240} /></Campo><Campo label="Sinal para a abertura"><select name="signal"><option value="">Selecionar automaticamente</option>{perfil.value.signals.map(signal => <option key={signal.code} value={signal.code}>{signal.label}</option>)}</select></Campo><Campo label="Objeção a trabalhar (opcional)"><select name="objection"><option value="">Nenhuma</option><option value="price">Preço</option><option value="timing">Momento</option><option value="existing_supplier">Já tem fornecedor</option><option value="not_interested">Sem interesse</option></select></Campo><button>Preparar rascunho para revisão</button></form>{draft !== undefined && <Detalhes value={draft} title="Rascunho e ação preparada — mensagem não enviada" />}</Card>
  </> : <Card title="Evidências da empresa"><MensagemVazia>Abra um perfil salvo ou investigue o site de uma empresa para ver sinais, contatos, qualificação e rascunhos.</MensagemVazia></Card>}</div></div>;
}
