# Kothar v4.0 — Registro de Arquitetura: Integração LinkedIn OAuth2 & MCP
**Data:** 13 de outubro de 2026  
**Responsável:** Bruno Harkin | Ugarit Digital  
**Módulos:** LinkedIn REST API v2 / OpenID, FastAPI Backend, MCP Server, Health Check & Security

---

## 1. Contexto e Objetivo

Integração oficial da conta profissional do **LinkedIn** ao Kothar para:
1. Inspeção contínua da identidade e estado da conexão.
2. Consulta dos dados do perfil profissional do usuário (`/v2/userinfo`).
3. Suporte arquitetural para postagens de textos e artigos (`/v2/ugcPosts`) quando o produto *Share on LinkedIn* estiver concedido.
4. Exposição como ferramentas tipadas via protocolo MCP nativo.

---

## 2. Decisões Arquiteturais e Implementação

1. **Roteador Nativo FastAPI (`/auth/linkedin/callback`)**:
   - Criado em `backend/api/routers/autenticacao_linkedin.py` e registrado no `main.py`.
   - Gera a URL de consentimento com `response_type=code`, captura o código retornado pelo LinkedIn, troca pelo `access_token` e salva em `backend/.linkedin-tokens/sessao_linkedin.json` e no `.env`.
   - Retorna página HTML amigável no navegador confirmando a conexão.

2. **Segurança e Isolamento**:
   - `LINKEDIN_CLIENT_ID` e `LINKEDIN_CLIENT_SECRET` mantidos exclusivamente no `.env`.
   - Diretório `backend/.linkedin-tokens/` adicionado ao `.gitignore` para impedir qualquer comit de dados de sessão.
   - Scanner de credenciais (`kothar-health.sh` e hooks) aprovado em 100% (31/31).

3. **Camada de Serviço (`backend/servicos/comunicacao_linkedin/gerenciador_linkedin.py`)**:
   - `obter_access_token()`: leitura automática de sessão salva.
   - `obter_perfil_usuario()`: busca nome, email verificado, ID do membro (sub), foto e localidade via OpenID Connect.
   - `verificar_status_conexao()`: cálculo de validade restante em dias (~60 dias) e checagem de escopos ativos.
   - `publicar_post_texto(texto)`: verificação de presença do escopo `w_member_social` antes de disparar publicação, com mensagens de erro claras se o produto não estiver ativo.

4. **Ferramentas MCP (`backend/mcp_server/linkedin_tools.py`)**:
   - `linkedin_status_conexao`: status executivo da conexão, escopos e validade do token.
   - `linkedin_obter_perfil`: perfil formatado do membro (OpenID Connect).
   - `linkedin_publicar_post`: publicação de textos no feed pessoal.
   - `linkedin_publicar_post_link`: compartilhamento de links com cartões de pré-visualização.
   - `linkedin_listar_posts`: histórico e rastreamento das publicações gerenciadas pelo Kothar.
   - `linkedin_excluir_post`: exclusão de publicações pelo URN/ID oficial.
   - Registradas em `backend/mcp_server/main.py`.

5. **Skill Catalogada**:
   - Atualizada `.agents/skills/kothar-linkedin/SKILL.md` (81ª skill oficial do Kothar com protocolos de gate CP6 e gatilhos automatizados).

