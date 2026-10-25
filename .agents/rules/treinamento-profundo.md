# PADRÃO DE TREINAMENTO PROFUNDO (DEEP TRAINING)

Sempre que o agente (Kothar ou sub-agente) for instruído a "ler uma sessão e aprender/treinar", ele está ESTRITAMENTE PROIBIDO de realizar "leitura rasa" (apenas resumir ou aceitar no contexto temporário).

**O agente deve OBRIGATORIAMENTE executar este protocolo de 4 etapas:**

1. **Mapear o Loop de Falha:** Identificar exatamente onde o agente da sessão anterior falhou, tentou repetidas vezes (alucinação) e qual foi a causa raiz de sua "cegueira" (falta de leitura de docs, porta errada, etc).
2. **Extrair o Ponto de Ruptura (Solução):** Isolar o exato comando, linha de código ou premissa arquitetural que resolveu a falha na sessão bem-sucedida.
3. **Sintetizar o Mandamento (Regra de Ouro):** Criar uma diretriz absoluta em formato "SEMPRE faça X" ou "NUNCA faça Y porque causará Z".
4. **Injeção Persistente (A Ação Final):** O agente DEVE escrever/sobrescrever um arquivo permanente. O conhecimento extraído DEVE ser salvo como uma nova regra em `~/.agents/rules/` ou como uma Skill na pasta correspondente. O treinamento só é validado quando a modificação no sistema de arquivos local é concluída.
