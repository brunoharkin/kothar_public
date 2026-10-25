---
name: kothar-engenharia-reversa
description: >-
  Skill do Kothar: Engenharia Reversa e Desconstrução de Features (baseada na metodologia REA - Reverse Engineer Anything).
  Ativar quando for solicitado inspecionar, desconstruir ou auditar aplicações de terceiros (Electron/ASAR, pacotes Web/JS,
  capturas de tráfego de rede HAR/SAZ, APKs Android ou binários nativos) para reconstrução limpa e estruturada (Clean-Room Design)
  no ecossistema Ugarit Digital.
---

# Skill: Kothar Engenharia Reversa & Desconstrução de Software (REA)

> **"Decompile $\rightarrow$ Understand $\rightarrow$ Recreate."**
> A engenharia reversa no Kothar não é pirataria nem cópia cega: é a desconstrução metódica da mecânica de software para síntese arquitetural limpa (*Clean-Room*), documentada no Cofre e reconstruída nos padrões Ugarit em Português do Brasil.

---

## 🛑 REGRAS CRÍTICAS DE SEGURANÇA E COMPLIANCE

```
❌ NUNCA INJETAR CÓDIGO PROPRIETÁRIO DIRETAMENTE NO REPOSITÓRIO
❌ NUNCA REALIZAR ENGENHARIA REVERSA PARA CRACKING, PIRATARIA OU BYPASS DE DRM
❌ NUNCA COMMISSAIONAR BINÁRIOS DESCOMPILADOS BRUTOS SEM TRATAMENTO
❌ NUNCA EXPOR CREDENCIAIS OU TOKENS CAPTURADOS EM LOGS DE TRÁFEGO
✅ SEMPRE SEPARAR: Fato Observado vs Dedução Lógica vs Incerteza
✅ SEMPRE APLICAR PROTOCOLO CLEAN-ROOM: Arquitetura $\rightarrow$ Especificação $\rightarrow$ Nova Implementação
```

---

## 🧠 TAXONOMIA DE EVIDÊNCIAS (REA Protocol)

Ao relatar descobertas de engenharia reversa a Bruno, **NUNCA** misturar suposições com fatos comprovados. Use sempre a classificação quádrupla:

1. **Observação (Observation):** Fato verificado diretamente no artefato (ex: string literal encontrada no bundle, rota `/api/v1/checkout` mapeada, dependência do Zustand identificada).
2. **Derivação (Derivation):** Transformação direta e determinística de código (ex: AST desofuscada que mapeia um reducer de estado para um switch-case).
3. **Inferência (Inference):** Hipótese arquitetural formulada pela IA baseada em padrões de projeto (deve ser rotulada explicitamente como hipótese a ser validada).
4. **Incógnita (Unknown):** Comportamento que não pode ser determinado apenas pela análise estática (ex: validação realizada puramente no servidor remoto).

---

## 🎯 ROTEAMENTO DE ALVOS (Target Routing)

Identifique o tipo de alvo fornecido pelo usuário e aplique a ferramenta/estratégia correspondente:

| Tipo de Alvo | Extensão / Formato | Ferramenta REA Primária | Modo de Análise |
|--------------|-------------------|-------------------------|-----------------|
| **App Desktop Electron** | `.asar`, pasta desempacotada | `analyze_javascript_application` | Estático (AST + Grafos de Módulos) |
| **Frontend Web / SPA** | `.js` minificado, sourcemaps, HTML | `analyze_javascript_application` | Mapeamento de imports, stores e endpoints |
| **Tráfego de Rede HTTP/WS**| `.har`, `.saz`, `.mitm` | `inspect_web_network_capture` | Análise de payloads, headers e sequências |
| **Pacote Android** | `.apk` | `inspect_android_package` (JADX) | Manifest, classes, atividades e rede |
| **Binário Nativo** | ELF (Linux), PE (Windows), Mach-O | `open_binary` + `inspect_artifact` | Ghidra / Hopper / IDA (Símbolos e Callgraphs) |
| **Captura de Pacotes** | `.pcap`, `.pcapng` | `inspect_packet_capture` | TShark / Decodificação de frames |

---

## 🛠️ FLUXO OPERACIONAL EM 5 ETAPAS (Ugarit Clean-Room)

### Etapa 1: Triagem & Extração do Alvo
- **Se for Electron (.asar):**
  ```bash
  # Desempacotar ASAR se necessário
  npx asar extract app.asar ./app-descompactado
  # Analisar com REA
  npx -y rea-agents@latest analyze-javascript-application ./app-descompactado --json
  ```
- **Se for Captura de Tráfego (.har/.saz):**
  - Filtrar payloads com dados sensíveis (redação de tokens/senhas).
  - Identificar endpoints REST/GraphQL, parâmetros obrigatórios e formatos de payload.

### Etapa 2: Mapeamento da Mecânica (Evidence Gathering)
1. **Ponto de Entrada (Entry Point):** Onde o fluxo começa (ex: clique no botão, rota disparada).
2. **Transformação de Dados:** Como o payload de entrada é serializado e validado.
3. **Comunicação:** Qual URL, protocolo, método HTTP e cabeçalhos são exigidos.
4. **Gestão de Estado:** Como a resposta é persistida localmente (Cache, LocalStorage, Store).

### Etapa 3: Amarração Lógica Reversa
Mapear a arquitetura completa em formato tabular antes de propor qualquer código:
```
[Gatilho UI / Evento] 
       ↓
[Camada de Negócio / Store Local]
       ↓
[Payload / Endpoint de Integração]
       ↓
[Resposta Remota & Tratamento de Erros]
```

### Etapa 4: Especificação no Cofre (ADR / Documentação)
Registrar a desconstrução no Cofre canônico (`/home/bruno-harkin/Cofre/`):
- O que o sistema inspecionado faz.
- Quais foram as evidências técnicas encontradas.
- O que foi descartado (código legado, telemetria inútil, dependências proprietárias).
- Como será a implementação limpa nos padrões Ugarit.

### Etapa 5: Reconstrução Limpa (Clean-Room Implementation)
Implementar nos padrões canônicos da Ugarit Digital:
- Estrutura estrita: `frontend/paginas/{nome}/`, `backend/servicos/`.
- Nomes em Português do Brasil sugestivos.
- Zero código copiado ou compilado de terceiros.
- Validação total via DoD (Definition of Done).

---

## 📋 COMANDOS RÁPIDOS CLI (REA Runner)

Para rodar análises rápidas via terminal sem depender de sessão ativa:

```bash
# Análise completa de aplicação JS / Electron:
npx -y rea-agents@latest analyze-javascript-application /caminho/do/alvo --json

# Diagnóstico de prontidão do REA na máquina:
npx -y rea-agents@latest doctor --json

# Ajuda e listagem de subcomandos do REA:
npx -y rea-agents@latest --help
```

---

## 🎯 DEFINITION OF DONE DA ENGENHARIA REVERSA

Uma tarefa de engenharia reversa só é declarada "✅ Pronta" quando:
1. Todas as conclusões possuem fonte ou evidência explícita (sem "acho que funciona assim").
2. Nenhuma credencial, cookie de sessão ou dado pessoal de terceiros foi persistido.
3. A amarração lógica completa (UI $\leftrightarrow$ Backend $\leftrightarrow$ API) está desenhada.
4. A especificação Clean-Room foi salva no Cofre canônico.
5. O escopo da nova feature está delimitado sem inchar o projeto com dependências desnecessárias.

