# Kothar v4.0 — Registro de Arquitetura e Aprendizado
**Data:** 13 de outubro de 2026  
**Responsável:** Bruno Harkin | Ugarit Digital  
**Módulos:** Google Workspace (Gmail & Calendar), FastAPI Backend, MCP Server, Health Check & Security Hooks

---

## 1. Contexto e Decisão de Arquitetura

O sistema necessitava de uma conexão direta, autônoma e segura com o **Gmail** e **Google Calendar** para:
1. Visualização e sumarização de mensagens recentes.
2. Manutenção contínua de **Inbox Zero** (higienização contra spams e cold mails).
3. Visualização de compromissos no Google Calendar.

### Decisão Técnica: Protocolo MCP sobre Serviço Nativo
Em vez de depender de scripts soltos no terminal ou de chamadas manuais, a interface foi exposta através de **ferramentas MCP tipadas** com schemas rígidos (`backend/mcp_server/google_tools.py`), apoiadas por uma camada de serviço robusta (`backend/servicos/comunicacao_google/gerenciador_email.py`).

---

## 2. Princípios de Segurança Estabelecidos

1. **Soft Delete Mandatório**:
   - Proibição absoluta de `messages.delete` atômico/irreversível.
   - Todo descarte utiliza `messages.trash`, garantindo que mensagens fiquem na Lixeira oficial por 30 dias com possibilidade de restauração.
2. **Defesa contra Injeção Indireta de Prompt**:
   - Corpos de e-mails são sanitizados, desprovidos de tags e truncados antes de chegarem à janela de contexto do LLM.
3. **Persistência de Sessão sem Reautenticação Manual**:
   - Captura forçada de `refresh_token` (`access_type=offline` e `prompt=consent`) armazenado em `.env` e protegido no `.gitignore`.

---

## 3. Calibrações e Correções Definitivas Realizadas

### A. Resolução de Concorrência de Portas
- **Problema:** O contêiner permanente da API FastAPI (`kothar_api`) já ocupava a porta `8080`, fazendo com que scripts efêmeros de callback retornassem `{"detail": "Not Found"}`.
- **Solução:** O endpoint `/auth/google/callback` foi incorporado nativamente ao FastAPI em `backend/api/routers/autenticacao_google.py` com retorno em tela HTML interativa para autorização em 1 clique.

### B. Calibração do Scanner de Credenciais (Eliminação de Falsos Positivos)
- **Problema:** Variáveis de URL como `url_token = "https://oauth2.googleapis.com/token"` disparavam o alerta de "Credencial hardcoded" devido ao casamento com o termo `token`.
- **Solução:** `scripts/kothar-health.sh` e `hooks/credential-scanner.sh` foram calibrados para ignorar strings que iniciem com `http://` ou `https://` e chamadas dinâmicas (`os.getenv`), preservando a detecção estrita de chaves e senhas reais sem falsos positivos.

### C. Formatação RFC3339 no Google Calendar
- **Problema:** A Google Calendar API rejeitava requisições com status 400 Bad Request devido à presença do caractere `+` no timezone ISO (`+00:00`).
- **Solução:** O parâmetro de tempo foi padronizado para UTC estrito com terminação `Z` (`%Y-%m-%dT%H:%M:%SZ`).

### D. Auditoria Estrutural Resiliente a CWD
- **Problema:** O hook `kothar-structure-audit.sh` dependia do `pwd` da ferramenta chamadora, podendo escanear o diretório home inteiro caso invocado fora da raiz do repositório.
- **Solução:** A raiz do projeto agora é calculada dinamicamente com base na localização canônica do próprio script (`BASH_SOURCE[0]`).

---

## 4. Estado da Caixa Postal Pós-Operação
- **Inbox Inicial:** 1.021 mensagens (946 não lidas).
- **Spam Inicial:** 74 mensagens.
- **Inbox Final:** **0 mensagens (Inbox Zero absoluto)**.
- **Spam Final:** **0 mensagens**.
- **Lixeira:** 1.094 mensagens transferidas com segurança de retenção.

