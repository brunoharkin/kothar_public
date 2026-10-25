import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings, Save, BrainCircuit, User, Archive,
  Wifi, WifiOff, X, Plus, Trash2, Zap,
  FileDown, AlertTriangle, FolderOpen, Calendar, Copy, ZoomIn,
  FileText, ChevronRight
} from 'lucide-react';
import { ollamaAPI, OllamaMessage, OllamaModel } from './ollama.api';
import { marked } from 'marked';
import { AIChatInput } from '../../componentes/ui/ai-chat-input';
import './ollama.styles.css';

interface ChatColumn {
  id: string;
  selectedModel: string;
  messages: OllamaMessage[];
  input: string;
  isLoading: boolean;
  sessionId: string | null;
}

const generateId = () => typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : '00000000-0000-0000-0000-000000000000'.replace(/0/g, () => (~~(Math.random() * 16)).toString(16));

export function OllamaChatPage() {
  const [columns, setColumns] = useState<ChatColumn[]>(() => {
    const saved = localStorage.getItem('kothar-chat-columns');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Se a coluna estiver carregando, manteremos ela como true para poder reconectar!
        return parsed.map((col: any) => ({ ...col }));
      } catch (e) {}
    }
    return [{
      id: generateId(),
      selectedModel: '',
      messages: [],
      input: '',
      isLoading: false,
      sessionId: null
    }];
  });

  useEffect(() => {
    localStorage.setItem('kothar-chat-columns', JSON.stringify(columns));
  }, [columns]);
  
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [baseUrl, setBaseUrl] = useState('http://kothar_ollama:11434');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [ollamaConnected, setOllamaConnected] = useState(false);
  const [ollamaError, setOllamaError] = useState<string | null>(null);
  
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [historySessions, setHistorySessions] = useState<any[]>([]);

  // Estado do modal de visualização de código (Artifact Canvas)
  const [codeModal, setCodeModal] = useState<{ content: string; language: string; filename: string } | null>(null);
  const [artifactTab, setArtifactTab] = useState<'preview' | 'code'>('preview');
  const [artifactSaveDialog, setArtifactSaveDialog] = useState(false);
  const [artifactSaveFolder, setArtifactSaveFolder] = useState('planos');

  const saveArtifactToCofre = async () => {
    if (!codeModal) return;
    const name = codeModal.filename || 'artefato';
    try {
      const response = await fetch('/api/cofre/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder: artifactSaveFolder,
          filename: name,
          content: codeModal.content,
        }),
      });
      if (response.ok) {
        alert(`✅ Artefato salvo em ~/cofre/${artifactSaveFolder}/${name}`);
        setArtifactSaveDialog(false);
      } else {
        alert('❌ Erro ao salvar artefato no backend.');
      }
    } catch(e) {
      alert('❌ Erro de conexão ao salvar artefato.');
    }
  };

  // Acumulador de tokens da sessão
  const [sessionStats, setSessionStats] = useState<{ tokensInput: number; tokensOutput: number; totalCost: number }>({
    tokensInput: 0, tokensOutput: 0, totalCost: 0,
  });

  // === KOTHAR v6.0 SUPREMO: Configurações avançadas ===
  const [debugMode, setDebugMode] = useState(false);
  const [memoryDialog, setMemoryDialog] = useState<{ colId: string; memory: string; stats: any } | null>(null);
  const [advancedParams, setAdvancedParams] = useState({
    temperature: 0.7,
    num_ctx: 12288,
    num_predict: -1,
    top_p: 0.9,
    top_k: 40,
  });

  useEffect(() => {
    fetchModels();
  }, [baseUrl]);

  const fetchModels = async () => {
    ollamaAPI.setBaseUrl(baseUrl);
    const m = await ollamaAPI.getModels();
    setModels(m);
    setOllamaConnected(ollamaAPI.isConnected());
    setOllamaError(ollamaAPI.getLastError());
    
    if (m.length > 0) {
      const installed = m.filter(model => model.installed);
      const recommended = m.filter(model => model.recommended);
      const defaultName = installed[0]?.name || recommended[0]?.name || m[0].name;
      
      setColumns(prev => prev.map(col => {
        if (!col.selectedModel) return { ...col, selectedModel: defaultName };
        return col;
      }));
    }
  };

  // Reconectar sessões que estavam carregando (Background Worker)
  useEffect(() => {
    columns.forEach(col => {
      if (col.isLoading && col.sessionId) {
        resumeStream(col.id, col.sessionId);
      }
    });
    // Roda só 1x no mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resumeStream = async (colId: string, sessionId: string) => {
    try {
      // O backend cria a sessão no worker usando request.session_id (que passamos como colId no chat)
      const res = await ollamaAPI.connectStream(colId, (chunk) => {
        setColumns(prev => prev.map(c => {
          if (c.id === colId) {
            const updatedMessages = [...c.messages];
            if (updatedMessages.length > 0 && updatedMessages[updatedMessages.length - 1].role === 'assistant') {
              updatedMessages[updatedMessages.length - 1].content = chunk;
            } else {
              updatedMessages.push({ role: 'assistant', content: chunk });
            }
            return { ...c, messages: updatedMessages };
          }
          return c;
        }));
      });

      setColumns(prev => prev.map(c => {
        if (c.id === colId) {
          const updatedMessages = [...c.messages];
          if (updatedMessages.length > 0) {
            updatedMessages[updatedMessages.length - 1].metrics = res.metrics;
          }
          return { ...c, messages: updatedMessages, isLoading: false };
        }
        return c;
      }));
    } catch (e) {
      console.error("Erro ao reconectar no stream:", e);
      setColumns(prev => prev.map(c => {
        if (c.id === colId) {
          const updatedMessages = [...c.messages];
          if (updatedMessages.length > 0 && updatedMessages[updatedMessages.length - 1].role === 'assistant') {
            updatedMessages[updatedMessages.length - 1].content += `\n❌ Sessão perdida ou interrompida.`;
          }
          return { ...c, messages: updatedMessages, isLoading: false };
        }
        return c;
      }));
    }
  };

  const loadHistory = async () => {
    try {
      const res = await fetch('/api/sessions/');
      if (res.ok) {
        const data = await res.json();
        const items = Array.isArray(data) ? data : (data.items || []);
        const chatSessions = items.filter((s: any) => s.agent_name === 'kothar-local-ai').sort((a: any, b: any) =>
          new Date(b.created_at || b.started_at).getTime() - new Date(a.created_at || a.started_at).getTime()
        );
        setHistorySessions(chatSessions);
      }
    } catch (e) {
      console.error("Erro ao carregar histórico", e);
    }
  };

  const openSessionInNewColumn = async (id: string, modelName: string) => {
    try {
      const res = await fetch(`/api/traces/?session_id=${id}&limit=200`);
      if (res.ok) {
        const data = await res.json();
        const traces = Array.isArray(data) ? data : (data.items || []);
        const reconstructed: OllamaMessage[] = [];
        traces.forEach((t: any) => {
          const userInput = t.tool_input || t.input;
          const asstOutput = t.tool_output || t.output;
          if (userInput) reconstructed.push({ role: 'user', content: userInput });
          if (asstOutput) reconstructed.push({
            role: 'assistant',
            content: asstOutput,
            metrics: {
              prompt_eval_count: t.tokens_input,
              eval_count: t.tokens_output,
              total_duration: t.duration_ms ? t.duration_ms * 1e6 : undefined
            }
          });
        });

        const newCol: ChatColumn = {
          id: generateId(),
          selectedModel: modelName,
          messages: reconstructed,
          input: '',
          isLoading: false,
          sessionId: id
        };

        setColumns(prev => [...prev, newCol].slice(0, 3));
      }
    } catch (e) {
      console.error("Erro ao carregar traces da sessão", e);
    } finally {
      setIsHistoryOpen(false);
    }
  };

  const addColumn = () => {
    if (columns.length >= 3) return;
    const installed = models.filter(m => m.installed);
    const defaultName = installed[columns.length]?.name || installed[0]?.name || models[0]?.name || '';
    
    setColumns(prev => [...prev, {
      id: generateId(),
      selectedModel: defaultName,
      messages: [],
      input: '',
      isLoading: false,
      sessionId: null
    }]);
  };

  const removeColumn = (id: string) => {
    if (columns.length <= 1) return;
    setColumns(prev => prev.filter(col => col.id !== id));
  };

  const updateColumn = (id: string, updates: Partial<ChatColumn>) => {
    setColumns(prev => prev.map(col => col.id === id ? { ...col, ...updates } : col));
  };

  // Enviar apenas em uma coluna específica
  const handleSendColumn = async (colId: string, customInput?: string) => {
    const col = columns.find(c => c.id === colId);
    if (!col) return;
    
    const textToSend = customInput || col.input;
    if (!textToSend.trim() || !col.selectedModel || col.isLoading) return;

    if (!ollamaConnected) {
      updateColumn(colId, { 
        messages: [...col.messages, { role: 'user', content: textToSend }, { role: 'assistant', content: `❌ Ollama offline.` }],
        input: ''
      });
      return;
    }

    const userMessage: OllamaMessage = { role: 'user', content: textToSend };
    const newMessages = [...col.messages, userMessage];
    
    updateColumn(colId, {
      input: '',
      isLoading: true,
      messages: [...newMessages, { role: 'assistant', content: '' }]
    });

    let currentSession = col.sessionId;
    if (!currentSession) {
      const title = `Chat: ${textToSend.substring(0, 30)}...`;
      currentSession = await ollamaAPI.createTraceSession(title, col.selectedModel);
      updateColumn(colId, { sessionId: currentSession });
    }

    try {
      const res = await ollamaAPI.chat(
        {
          model: col.selectedModel,
          messages: newMessages,
          session_id: colId,
          options: {
            temperature: advancedParams.temperature,
            num_ctx: advancedParams.num_ctx,
            num_predict: advancedParams.num_predict,
            top_p: advancedParams.top_p,
            top_k: advancedParams.top_k,
          },
        },
        (chunk) => {
          setColumns(prev => prev.map(c => {
            if (c.id === colId) {
              const updatedMessages = [...c.messages];
              updatedMessages[updatedMessages.length - 1].content = chunk;
              return { ...c, messages: updatedMessages };
            }
            return c;
          }));
        }
      );
      
      // Update with final metrics
      setColumns(prev => prev.map(c => {
        if (c.id === colId) {
          const updatedMessages = [...c.messages];
          updatedMessages[updatedMessages.length - 1].metrics = res.metrics;
          return { ...c, messages: updatedMessages, isLoading: false };
        }
        return c;
      }));

      // No need to logTraceMessage manually, the background worker saves it!
      // But we can update stats:
      if (res.metrics) {
        setSessionStats(prev => ({
          tokensInput: prev.tokensInput + (res.metrics.prompt_eval_count || 0),
          tokensOutput: prev.tokensOutput + (res.metrics.eval_count || 0),
          totalCost: prev.totalCost,
        }));
      }
    } catch (error) {
      console.error(error);
      setColumns(prev => prev.map(c => {
        if (c.id === colId) {
          const updatedMessages = [...c.messages];
          updatedMessages[updatedMessages.length - 1].content = `❌ Erro de conexão ou fila.`;
          return { ...c, messages: updatedMessages, isLoading: false };
        }
        return c;
      }));
    }
  };

  // Botão "Sincronizar": Pega o input da coluna 0 e dispara pra todos
  const sendToAll = async () => {
    const textToSend = columns[0].input;
    if (!textToSend.trim()) return;
    
    // Zera os inputs de todas as colunas
    setColumns(prev => prev.map(c => ({ ...c, input: '' })));

    // Dispara requests concorrentes (sem travar a UI se um demorar mais que o outro)
    columns.forEach(col => {
      handleSendColumn(col.id, textToSend);
    });
  };

  // Confirmação explícita antes de limpar sessão (evita perda acidental)
  const confirmClearSession = (colId: string) => {
    const col = columns.find(c => c.id === colId);
    if (!col) return;

    const msgCount = col.messages.length;
    const confirmMsg = msgCount === 0
      ? 'Limpar esta sessão?'
      : `Limpar esta sessão? ${msgCount} mensagem(ns) serão perdidas (você pode salvar antes no cofre).`;

    if (window.confirm(confirmMsg)) {
      updateColumn(colId, { messages: [], input: '', sessionId: null });
    }
  };

  // Estado do modal de salvar no cofre
  const [saveDialog, setSaveDialog] = useState<{ colId: string; folder: string; name: string } | null>(null);

  const openSaveDialog = (colId: string) => {
    const col = columns.find(c => c.id === colId);
    if (!col || col.messages.length === 0) return;

    const defaultName = `conversa-${col.selectedModel.replace(/[^a-z0-9]/gi, '-')}-${new Date().toISOString().slice(0, 10)}`;

    setSaveDialog({
      colId,
      folder: 'kothar_local_chats',
      name: defaultName,
    });
  };

  const saveConversationToCofre = async () => {
    if (!saveDialog) return;
    const { colId, folder, name } = saveDialog;
    const col = columns.find(c => c.id === colId);
    if (!col) return;

    // Gera markdown da conversa (declarado fora do try para catch usar)
    const date = new Date().toISOString();
    let md = `# ${name}\n\n`;
    md += `**Data:** ${date}\n`;
    md += `**Modelo:** ${col.selectedModel}\n`;
    md += `**Mensagens:** ${col.messages.length}\n\n`;
    md += `---\n\n`;

    for (const msg of col.messages) {
      const role = msg.role === 'user' ? '🧑 **Você**' : '🤖 **Kothar**';
      md += `## ${role}\n\n${msg.content}\n\n`;
    }

    try {
      // Envia para backend salvar no cofre
      const response = await fetch('/api/cofre/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder,
          filename: `${name}.md`,
          content: md,
        }),
      });

      if (response.ok) {
        alert(`✅ Conversa salva em ~/cofre/${folder}/${name}.md`);
      } else {
        // Fallback: download como arquivo
        const blob = new Blob([md], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${name}.md`;
        a.click();
        URL.revokeObjectURL(url);
        alert(`📥 Backend não disponível. Arquivo baixado: ${name}.md\nMova para ~/cofre/${folder}/`);
      }
    } catch (e: any) {
      // Fallback: download local
      const blob = new Blob([md], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}.md`;
      a.click();
      URL.revokeObjectURL(url);
      alert(`📥 Arquivo baixado: ${name}.md`);
    }

    setSaveDialog(null);
  };

  // Detecta linguagem do bloco de código baseado no conteúdo
  const detectLanguage = (code: string): { lang: string; filename: string } => {
    const trimmed = code.trim();
    if (trimmed.includes('import React') || trimmed.includes('jsx') || trimmed.includes('tsx')) return { lang: 'tsx', filename: 'component.tsx' };
    if (trimmed.includes('def ') || trimmed.includes('import ') && !trimmed.includes('{')) return { lang: 'python', filename: 'script.py' };
    if (trimmed.includes('function ') || trimmed.includes('const ') && trimmed.includes('=>')) return { lang: 'javascript', filename: 'script.js' };
    if (trimmed.includes('CREATE TABLE') || trimmed.includes('SELECT ')) return { lang: 'sql', filename: 'schema.sql' };
    if (trimmed.includes('<!DOCTYPE') || trimmed.includes('<html')) return { lang: 'html', filename: 'page.html' };
    if (trimmed.includes('FROM ') && /\\b(gemma|llama|kothar)/.test(trimmed)) return { lang: 'dockerfile', filename: 'Modelfile' };
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) return { lang: 'json', filename: 'data.json' };
    if (trimmed.startsWith('# ')) return { lang: 'markdown', filename: 'doc.md' };
    return { lang: 'text', filename: 'snippet.txt' };
  };

  // Componente de bloco de código com botão de maximizar
  const CodeBlock = ({ code, language }: { code: string; language: string }) => {
    const meta = detectLanguage(code);
    const finalLang = language || meta.lang;

    const openModal = () => {
      setCodeModal({ content: code, language: finalLang, filename: meta.filename });
    };

    const copyCode = (e: React.MouseEvent) => {
      e.stopPropagation();
      navigator.clipboard.writeText(code);
    };

    return (
      <div className="ollama-code-block" onClick={openModal}>
        <div className="ollama-code-header">
          <span className="ollama-code-lang">{finalLang}</span>
          <div className="ollama-code-actions">
            <button onClick={copyCode} title="Copiar código">
              <Copy className="h-3 w-3" />
            </button>
            <button onClick={openModal} title="Expandir">
              <ZoomIn className="h-3 w-3" />
            </button>
          </div>
        </div>
        <pre className="ollama-code-content"><code>{code}</code></pre>
      </div>
    );
  };

  // Avatar animado "K" para o Kothar - várias animações sutis
  const KotharAvatar = ({ animated = false }: { animated?: boolean }) => {
    // Array de animações que rotacionam
    const animations = ['spin-slow', 'pulse-glow', 'float-up', 'float-down', 'wiggle', 'breathe'];
    const animClass = animated ? animations[Math.floor(Date.now() / 1000) % animations.length] : 'k-static';

    return (
      <div className={`ollama-avatar ollama-avatar-bot ${animClass}`}>
        <span className="ollama-avatar-k">K</span>
      </div>
    );
  };

  // Indicador de digitação animado (substitui typing-dots)
  const TypingIndicator = () => {
    return (
      <div className="ollama-typing-indicator">
        <div className={`ollama-avatar ollama-avatar-bot k-pulse-glow`}>
          <span className="ollama-avatar-k">K</span>
        </div>
        <div className="ollama-message-content">
          <div className="ollama-typing-bubble">
            <span className="ollama-typing-dot" style={{ animationDelay: '0ms' }}></span>
            <span className="ollama-typing-dot" style={{ animationDelay: '150ms' }}></span>
            <span className="ollama-typing-dot" style={{ animationDelay: '300ms' }}></span>
            <span className="ollama-typing-text">Kothar está pensando...</span>
          </div>
        </div>
      </div>
    );
  };

  const renderMessageContent = (content: string) => {
    if (!content) return null;

    // Parse markdown básico: detecta blocos de código
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match;
    let keyCounter = 0;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Texto antes do bloco
      if (match.index > lastIndex) {
        const textBefore = content.slice(lastIndex, match.index);
        parts.push(
          <div key={`text-${keyCounter++}`} className="ollama-text-block marked-content" dangerouslySetInnerHTML={{ __html: marked.parse(textBefore) as string }} />
        );
      }

      // Bloco de código
      const lang = match[1] || '';
      const code = match[2];
      parts.push(<CodeBlock key={`code-${keyCounter++}`} code={code} language={lang} />);

      lastIndex = match.index + match[0].length;
    }

    // Texto restante
    if (lastIndex < content.length) {
      const textAfter = content.slice(lastIndex);
      parts.push(
        <div key={`text-${keyCounter++}`} className="ollama-text-block marked-content" dangerouslySetInnerHTML={{ __html: marked.parse(textAfter) as string }} />
      );
    }

    // Pensamento do DeepSeek
    const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/);
    if (thinkMatch) {
      const reasoning = thinkMatch[1];
      const answer = content.replace(/<think>[\s\S]*?<\/think>/, '').trim();
      return (
        <>
          <details className="think-box">
            <summary>🧠 Raciocínio</summary>
            <div className="think-content">{reasoning}</div>
          </details>
          {answer && <div style={{ marginTop: '8px' }}>{renderMessageContent(answer)}</div>}
        </>
      );
    }

    return parts.length > 0 ? <>{parts}</> : <div className="ollama-text-block marked-content" dangerouslySetInnerHTML={{ __html: marked.parse(content) as string }} />;
  };

  // Regenerar resposta (re-executa última mensagem)
  const regenerateLastResponse = (colId: string) => {
    const col = columns.find(c => c.id === colId);
    if (!col) return;
    // Pega a penúltima mensagem (user antes da resposta do assistant)
    const msgs = col.messages;
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') {
        const userMsg = msgs[i].content;
        // Remove a última resposta do assistant
        const newMessages = msgs.slice(0, i + 1);
        updateColumn(colId, { messages: newMessages });
        // Re-envia
        setTimeout(() => handleSendColumn(colId, userMsg), 100);
        return;
      }
    }
  };

  // Copiar texto da resposta
  const copyResponse = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const renderMessageBubble = (msg: OllamaMessage, idx: number, isLoading: boolean, isLast: boolean, colId?: string, totalMessages: number = 0) => {
    // Pula a renderização da mensagem vazia se estiver carregando, pois o TypingIndicator já faz isso.
    if (msg.role === 'assistant' && msg.content === '' && isLoading && isLast) {
      return null;
    }

    return (
      <div key={idx} className={`ollama-message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}>
        {msg.role === 'user' ? (
          <div className="ollama-avatar ollama-avatar-user">
            <User className="h-3 w-3" />
          </div>
        ) : (
          <KotharAvatar animated={isLoading && isLast} />
        )}
      <div className="ollama-message-content">
        {/* SEM fundo para assistant, com fundo para user */}
        <div className={`ollama-message-bubble ${msg.role === 'assistant' ? 'ollama-message-bubble--clean' : ''}`}>
          {msg.content === '' && isLoading && isLast ? (
            <div className="ollama-typing-dots-inline">
              <span/><span/><span/>
            </div>
          ) : msg.content === '' ? (
            <div className="ollama-empty-response">⚠️ Modelo retornou resposta vazia.</div>
          ) : (
            renderMessageContent(msg.content)
          )}
        </div>
        {/* Footer de métricas discreto — só texto, sem ícones grandes */}
        {msg.metrics && (msg.metrics.total_duration || msg.metrics.eval_count || msg.metrics.prompt_eval_count) && (
          <div className="ollama-message-footer">
            <span className="ollama-metric-text">
              ↓ {msg.metrics.prompt_eval_count || 0} input
            </span>
            <span className="ollama-metric-divider">·</span>
            <span className="ollama-metric-text">
              ↑ {msg.metrics.eval_count || 0} output
            </span>
            <span className="ollama-metric-divider">·</span>
            <span className="ollama-metric-text">
              {(msg.metrics.total_duration / 1e9).toFixed(1)}s
            </span>
            {debugMode && msg.metrics.prompt_eval_count && msg.metrics.prompt_eval_count > 500 && (
              <>
                <span className="ollama-metric-divider">·</span>
                <span className="ollama-metric-text" style={{ color: '#10b981' }} title="RAG Supremo injetou contexto rico">
                  🧠 RAG ativo (~{Math.round(msg.metrics.prompt_eval_count / 1000)}k ctx)
                </span>
              </>
            )}
            {/* Ações: regenerar e copiar (só em respostas do assistant) */}
            {msg.role === 'assistant' && colId && isLast && !isLoading && (
              <>
                <span className="ollama-metric-divider">·</span>
                <button
                  className="ollama-action-link"
                  onClick={() => regenerateLastResponse(colId)}
                  title="Gerar outra resposta para a última pergunta"
                >
                  ↻ outra resposta
                </button>
                <span className="ollama-metric-divider">·</span>
                <button
                  className="ollama-action-link"
                  onClick={() => copyResponse(msg.content)}
                  title="Copiar texto"
                >
                  copiar
                </button>
              </>
            )}
          </div>
        )}
        {/* Badge de memória: aparece se a conversa está longa */}
        {debugMode && msg.role === 'assistant' && totalMessages > 10 && (
          <div className="ollama-memory-badge" style={{ fontSize: '10px', opacity: 0.6, marginTop: '4px' }}>
            💾 {totalMessages} msgs nesta sessão (auto-compressão em 20)
          </div>
        )}
      </div>
    </div>
    );
  };

  const uniqueModels = models.reduce<OllamaModel[]>((acc, model) => {
    if (!acc.find(m => m.name === model.name)) acc.push(model);
    return acc;
  }, []);
  const installedModels = uniqueModels.filter(m => m.installed);
  const availableModels = uniqueModels.filter(m => !m.installed);

  const ModelSelector = ({ value, onChange }: { value: string, onChange: (v: string) => void }) => (
    <select className="ollama-select" value={value} onChange={(e) => onChange(e.target.value)} style={{ flex: 1 }}>
      {uniqueModels.length === 0 ? <option value="">⏳ Carregando...</option> : (
        <>
          {installedModels.length > 0 && (
            <optgroup label="✅ Instalados">
              {installedModels.map(m => <option key={m.name} value={m.name}>{m.name} {m.recommended ? '⭐' : ''}</option>)}
            </optgroup>
          )}
          {availableModels.length > 0 && (
            <optgroup label="📦 Populares">
              {availableModels.map(m => <option key={m.name} value={m.name}>{m.name} ({m.vram_required || '?'})</option>)}
            </optgroup>
          )}
        </>
      )}
    </select>
  );

  return (
    <div className="ollama-container">
      {/* Header */}
      <div className="ollama-header">
        <div className="ollama-title">
          <BrainCircuit className="h-5 w-5 text-emerald-400" />
          <h2 style={{ fontSize: '15px' }}>Kothar Local AI</h2>
          {/* Status pill menor e mais discreto */}
          <span
            className={`ollama-status-dot ${ollamaConnected ? 'connected' : 'disconnected'}`}
            title={ollamaConnected ? 'Online' : 'Offline'}
          >
            {ollamaConnected ? <Wifi className="h-2.5 w-2.5" /> : <WifiOff className="h-2.5 w-2.5" />}
          </span>
          {ollamaError && !ollamaConnected && (
            <span className="ollama-error-hint" title={ollamaError}>
              {ollamaError.substring(0, 30)}
            </span>
          )}
          {/* Tokens acumulados da sessão (discreto) */}
          {(sessionStats.tokensInput > 0 || sessionStats.tokensOutput > 0) && (
            <span className="ollama-session-stats" title="Tokens acumulados nesta sessão">
              sessão: {((sessionStats.tokensInput + sessionStats.tokensOutput) / 1000).toFixed(1)}k tokens
            </span>
          )}
        </div>

        {/* Controls movidos para o painel de cada coluna */}
      </div>

      <AnimatePresence>
        {isConfigOpen && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="ollama-config-panel">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div>
                <label>API Endpoint:</label>
                <input type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} className="ollama-input-config" style={{ width: '100%' }} />
              </div>
              <div>
                <label>🌡️ Temperature: <strong>{advancedParams.temperature.toFixed(2)}</strong></label>
                <input type="range" min="0" max="1.5" step="0.05" value={advancedParams.temperature}
                  onChange={(e) => setAdvancedParams(p => ({ ...p, temperature: parseFloat(e.target.value) }))}
                  style={{ width: '100%' }} />
              </div>
              <div>
                <label>📏 num_ctx: <strong>{advancedParams.num_ctx}</strong></label>
                <input type="range" min="2048" max="32768" step="1024" value={advancedParams.num_ctx}
                  onChange={(e) => setAdvancedParams(p => ({ ...p, num_ctx: parseInt(e.target.value) }))}
                  style={{ width: '100%' }} />
              </div>
              <div>
                <label>📝 num_predict: <strong>{advancedParams.num_predict === -1 ? '∞' : advancedParams.num_predict}</strong></label>
                <input type="range" min="-1" max="4096" step="100" value={advancedParams.num_predict}
                  onChange={(e) => setAdvancedParams(p => ({ ...p, num_predict: parseInt(e.target.value) }))}
                  style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
              <button onClick={fetchModels} className="ollama-btn-refresh">Atualizar Conexão</button>
              <button
                onClick={() => setAdvancedParams({ temperature: 0.7, num_ctx: 12288, num_predict: -1, top_p: 0.9, top_k: 40 })}
                className="ollama-btn-refresh"
                title="Restaurar valores padrão"
              >
                ↺ Resetar
              </button>
            </div>
            <p style={{ fontSize: '11px', opacity: 0.6, marginTop: '8px' }}>
              ⚡ RAG Supremo ativo: 30 chunks, query expansion, re-ranking. Memória de conversa com sumarização automática.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="ollama-content-wrapper">
        {/* Dynamic Grid Columns */}
        {columns.map((col, index) => (
          <div key={col.id} className="ollama-chat-column">
            {/* Menu Interativo da Coluna (Unified) */}
            <div className="ollama-split-header" style={{ justifyContent: 'flex-end', borderBottom: 'none', padding: '12px 24px 0 24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <button className="ollama-menu-btn" onClick={addColumn} disabled={columns.length >= 3}>
                  <Plus className="h-3.5 w-3.5" /> Novo Painel
                </button>
                <button className="ollama-menu-btn" onClick={() => { setIsHistoryOpen(!isHistoryOpen); loadHistory(); }}>
                  <Archive className="h-3.5 w-3.5" /> Histórico
                </button>
                <button
                  className={`ollama-menu-btn ${debugMode ? 'active' : ''}`}
                  onClick={() => setDebugMode(!debugMode)}
                  title="Mostrar chunks RAG e memória injetada"
                >
                  <BrainCircuit className="h-3.5 w-3.5" /> Debug RAG
                </button>
                <button
                  className="ollama-menu-btn"
                  onClick={() => setIsConfigOpen(!isConfigOpen)}
                  title="Configurações avançadas (temperature, num_ctx)"
                >
                  <Settings className="h-3.5 w-3.5" /> Config
                </button>
                <button
                  className="ollama-menu-btn"
                  onClick={() => openSaveDialog(col.id)}
                  disabled={col.messages.length === 0}
                >
                  <FileDown className="h-3.5 w-3.5" /> Salvar no Cofre
                </button>
                <button
                  className="ollama-menu-btn danger"
                  onClick={() => confirmClearSession(col.id)}
                >
                  <AlertTriangle className="h-3.5 w-3.5" /> Limpar Sessão
                </button>
                {columns.length > 1 && (
                  <button className="ollama-menu-btn danger" onClick={() => removeColumn(col.id)}>
                    <Trash2 className="h-3.5 w-3.5" /> Fechar
                  </button>
                )}
              </div>
            </div>

            {/* Column Chat Area */}
            <div className="ollama-chat-area">
              {col.messages.length === 0 && !col.isLoading ? (
                <div className="ollama-empty-state">
                  <KotharAvatar />
                  <p style={{ fontSize: '13px', textAlign: 'center', marginTop: '12px' }}>
                    Olá! Sou Kothar, seu arquiteto de produto.
                  </p>
                </div>
              ) : (
                <>
                  {col.messages.map((msg, i) => renderMessageBubble(msg, i, col.isLoading, i === col.messages.length - 1, col.id, col.messages.length))}
                  {/* Indicador de digitação quando loading e última msg é user vazia */}
                  {col.isLoading && col.messages[col.messages.length - 1]?.content === '' && (
                    <TypingIndicator />
                  )}
                </>
              )}
              {/* Dummy div to scroll to bottom, we use a simple ref approach for each list */}
              <AutoScroller messages={col.messages} isLoading={col.isLoading} />
            </div>

            {/* Advanced Input Component */}
            <AIChatInput
              value={col.input}
              onChange={(val: string) => updateColumn(col.id, { input: val })}
              onSubmit={() => handleSendColumn(col.id)}
              isLoading={col.isLoading}
              disabled={col.isLoading || !col.selectedModel || !ollamaConnected}
              modelName={col.selectedModel}
            />
          </div>
        ))}

        {/* History Sidebar */}
        <AnimatePresence>
          {isHistoryOpen && (
            <motion.div initial={{ width: 0 }} animate={{ width: 300 }} exit={{ width: 0 }} className="ollama-history-sidebar" style={{ flexShrink: 0 }}>
              <h3><Archive className="h-4 w-4" /> Histórico <X className="h-4 w-4 ml-auto cursor-pointer" onClick={() => setIsHistoryOpen(false)}/></h3>
              {historySessions.map(sess => (
                <div key={sess.id} className="ollama-history-item" onClick={() => openSessionInNewColumn(sess.id, sess.llm_model || '')}>
                  <div className="ollama-history-item-title">{sess.task_summary || sess.name || 'Chat sem título'}</div>
                  <div className="ollama-history-item-meta">
                    <span>{sess.llm_model || sess.agent_name}</span>
                    <span>{new Date(sess.created_at || sess.started_at).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>
              ))}
              {historySessions.length === 0 && (
                <div className="p-4 text-sm text-slate-500">Nenhum chat gravado ainda.</div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Modal de Salvar no Cofre */}
        {saveDialog && (
          <div className="ollama-modal-backdrop" onClick={() => setSaveDialog(null)}>
            <div className="ollama-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="ollama-modal-header">
                <h3><FolderOpen className="h-4 w-4 inline mr-2" />Salvar conversa no cofre</h3>
                <button onClick={() => setSaveDialog(null)}>
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="ollama-modal-body">
                <label>Nome da conversa</label>
                <input
                  type="text"
                  value={saveDialog.name}
                  onChange={(e) => setSaveDialog({ ...saveDialog, name: e.target.value })}
                  placeholder="conversa-nome-data"
                />

                <label>Pasta no cofre</label>
                <select
                  value={saveDialog.folder}
                  onChange={(e) => setSaveDialog({ ...saveDialog, folder: e.target.value })}
                >
                  <option value="kothar_local_chats">~/cofre/kothar_local_chats/</option>
                  <option value="kothar_manuais">~/cofre/kothar_manuais/</option>
                  <option value="kothar_core">~/cofre/kothar_core/</option>
                  <option value="sessao">~/cofre/sessao/</option>
                  <option value="planos">~/cofre/planos/</option>
                  <option value="planejamento">~/cofre/planejamento/</option>
                </select>

                <div className="ollama-modal-info">
                  <Calendar className="h-3 w-3" />
                  <span>{new Date().toLocaleString('pt-BR')}</span>
                </div>
              </div>

              <div className="ollama-modal-actions">
                <button onClick={() => setSaveDialog(null)}>Cancelar</button>
                <button className="ollama-btn-primary" onClick={saveConversationToCofre}>
                  <Save className="h-4 w-4" /> Salvar no cofre
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Visualização de Código (Artifact Canvas) */}
        {codeModal && (
          <div className="ollama-modal-backdrop" onClick={() => { setCodeModal(null); setArtifactSaveDialog(false); }}>
            <div className={`ollama-code-modal ${artifactTab === 'preview' ? 'canvas-mode' : ''}`} onClick={(e) => e.stopPropagation()}>
              <div className="ollama-modal-header">
                <div className="artifact-tabs">
                  <button 
                    className={`artifact-tab ${artifactTab === 'preview' ? 'active' : ''}`}
                    onClick={() => setArtifactTab('preview')}
                  >
                    👁️ Preview
                  </button>
                  <button 
                    className={`artifact-tab ${artifactTab === 'code' ? 'active' : ''}`}
                    onClick={() => setArtifactTab('code')}
                  >
                    <FileText className="h-4 w-4 inline mr-1" /> Código Fonte
                  </button>
                </div>
                <button onClick={() => { setCodeModal(null); setArtifactSaveDialog(false); }}>
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="ollama-code-modal-toolbar">
                <span className="artifact-filename">{codeModal.filename} <span className="ollama-code-modal-lang">{codeModal.language}</span></span>
                
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                  <button className="ollama-modal-action" onClick={() => setArtifactSaveDialog(true)}>
                    <Save className="h-3 w-3" /> Salvar no Cofre
                  </button>
                  <button
                    className="ollama-modal-action"
                    onClick={() => {
                      navigator.clipboard.writeText(codeModal.content);
                      alert('✅ Código copiado!');
                    }}
                  >
                    <Copy className="h-3 w-3" /> Copiar
                  </button>
                  <button
                    className="ollama-modal-action"
                    onClick={() => {
                      const blob = new Blob([codeModal.content], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = codeModal.filename;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    <FileDown className="h-3 w-3" /> Baixar
                  </button>
                </div>
              </div>

              {artifactSaveDialog && (
                <div className="artifact-save-panel">
                  <span>Pasta destino:</span>
                  <select value={artifactSaveFolder} onChange={(e) => setArtifactSaveFolder(e.target.value)}>
                    <option value="planos">~/cofre/planos/</option>
                    <option value="planejamento">~/cofre/planejamento/</option>
                    <option value="produtos">~/cofre/produtos/</option>
                    <option value="kothar_local_chats">~/cofre/kothar_local_chats/</option>
                  </select>
                  <button className="ollama-btn-primary" onClick={saveArtifactToCofre} style={{ padding: '4px 12px', fontSize: '12px', height: 'auto' }}>Salvar</button>
                  <button onClick={() => setArtifactSaveDialog(false)} style={{ padding: '4px', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X className="h-4 w-4" /></button>
                </div>
              )}

              <div className="artifact-content-area">
                {artifactTab === 'preview' ? (
                  <div className="artifact-preview">
                    {['html', 'svg', 'xml'].includes(codeModal.language.toLowerCase()) ? (
                      <iframe 
                        title="Artifact Preview" 
                        srcDoc={codeModal.content} 
                        className="artifact-iframe"
                        sandbox="allow-scripts allow-same-origin"
                      />
                    ) : (
                      <div className="marked-content artifact-markdown" dangerouslySetInnerHTML={{ __html: marked.parse(codeModal.content) as string }} />
                    )}
                  </div>
                ) : (
                  <pre className="ollama-code-modal-content"><code>{codeModal.content}</code></pre>
                )}
              </div>

              <div className="ollama-code-modal-footer">
                <span>{codeModal.content.split('\n').length} linhas</span>
                <span className="ollama-metric-divider">·</span>
                <span>{codeModal.content.length} caracteres</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Auto-scroll inteligente: só segue o fim se o usuário já estava perto do fim.
// Se o usuário scrollou para cima (lendo respostas anteriores), respeita a posição dele.
// Quando ele rola de volta para perto do fim, volta a seguir automaticamente.
// Mostra badge "↓ seguir" quando há conteúdo novo e o usuário está scrollado para cima.
function AutoScroller({ messages, isLoading }: { messages: any[], isLoading: boolean }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const userScrolledUpRef = useRef(false);
  const [showJumpButton, setShowJumpButton] = useState(false);
  const [unseenCount, setUnseenCount] = useState(0);
  const lastMessageLengthRef = useRef(0);

  // Detecta scroll do usuário e conta mensagens não vistas
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const scrollable = container.closest('.ollama-chat-area') as HTMLElement | null;
    if (!scrollable) return;

    const handleScroll = () => {
      const distanceFromBottom = scrollable.scrollHeight - scrollable.scrollTop - scrollable.clientHeight;
      const isNearBottom = distanceFromBottom <= 80;
      userScrolledUpRef.current = !isNearBottom;
      setShowJumpButton(!isNearBottom && (isLoading || unseenCount > 0));
      if (isNearBottom) setUnseenCount(0);
    };

    scrollable.addEventListener('scroll', handleScroll, { passive: true });
    return () => scrollable.removeEventListener('scroll', handleScroll);
  }, [isLoading, unseenCount]);

  // Auto-scroll só se o usuário não scrollou para cima
  useEffect(() => {
    // Detecta se a última mensagem cresceu (streaming chunk)
    const lastMsg = messages[messages.length - 1];
    const currentLength = lastMsg?.content?.length || 0;
    if (currentLength > lastMessageLengthRef.current) {
      if (userScrolledUpRef.current) {
        // Conteúdo novo chegou enquanto o usuário lê algo acima
        setUnseenCount(c => c + 1);
      }
    }
    lastMessageLengthRef.current = currentLength;

    if (!userScrolledUpRef.current) {
      sentinelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      setUnseenCount(0);
    }
  }, [messages, isLoading]);

  const jumpToBottom = () => {
    userScrolledUpRef.current = false;
    setUnseenCount(0);
    setShowJumpButton(false);
    sentinelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  };

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      {showJumpButton && (
        <button
          onClick={jumpToBottom}
          title="Seguir resposta"
          style={{
            position: 'sticky',
            bottom: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(52, 211, 153, 0.95)',
            color: '#0a0a0a',
            border: 'none',
            borderRadius: 20,
            padding: '6px 14px',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            zIndex: 10,
            margin: '0 auto',
            width: 'fit-content'
          }}
        >
          ↓ {unseenCount > 0 ? `${unseenCount} nova${unseenCount > 1 ? 's' : ''} • ` : ''}Seguir resposta
        </button>
      )}
      <div ref={sentinelRef} style={{ height: 1 }} />
    </div>
  );
}
