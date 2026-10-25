---
name: kothar-linkedin
description: >-
  Skill do Kothar v4.0 para integração oficial com a API do LinkedIn através de OAuth2
  e ferramentas MCP tipadas. Permite inspeção de status da conexão, leitura de perfil,
  validação de escopos, gerenciamento de histórico e publicação de conteúdos e links.
---

# Skill: Kothar LinkedIn (API & MCP)

> **Ugarit Digital — Bruno Harkin**  
> Canal de conexão, gestão de identidade e presença profissional no LinkedIn via Kothar.

---

## 🎯 Gatilhos de Ativação Automática

Ativar esta skill IMEDIATAMENTE sempre que Bruno solicitar:
- *"verifica o linkedin"* / *"como está o status do linkedin?"*
- *"ver meu perfil no linkedin"* / *"quem está logado no linkedin?"*
- *"publicar no linkedin"* / *"postar no linkedin"* / *"compartilhar link no linkedin"*
- *"quais foram os últimos posts no linkedin?"* / *"listar publicações do linkedin"*
- *"remover post do linkedin"* / *"excluir publicação"*

---

## 🛠️ Ferramentas MCP Disponíveis

| Ferramenta MCP | Função | Parâmetros |
| :--- | :--- | :--- |
| `linkedin_status_conexao` | Retorna status da conexão, tempo de vida do token (~60 dias) e escopos ativos | Nenhum |
| `linkedin_obter_perfil` | Consulta detalhes estruturados do perfil (Nome, E-mail, ID único, Localidade, Foto) | Nenhum |
| `linkedin_publicar_post` | Publica texto no perfil pessoal do membro (requer confirmação explícita de Bruno) | `texto` (str) |
| `linkedin_publicar_post_link` | Compartilha link com card de pré-visualização no feed pessoal | `texto` (str), `url_link` (str), `titulo` (str opcional), `descricao` (str opcional) |
| `linkedin_listar_posts` | Lista o histórico das publicações gerenciadas pelo Kothar | `limite` (int, default 10) |
| `linkedin_excluir_post` | Exclui uma publicação pelo ID/URN oficial do LinkedIn | `post_urn` (str) |

---

## 📋 Protocolos de Execução

### Protocolo 1: Inspeção de Perfil e Estado
1. Invocar `linkedin_status_conexao` e `linkedin_obter_perfil`.
2. Apresentar dados executivos com status do token e permissões.

### Protocolo 2: Publicação com Gate de Aprovação (CP6)
1. Kothar **NUNCA** publica automaticamente sem aprovação do texto por Bruno.
2. Formatar o post com ganchos fortes, tom profissional e sem clichês vazios.
3. Apresentar o rascunho completo no chat e aguardar confirmação antes de invocar `linkedin_publicar_post` ou `linkedin_publicar_post_link`.
4. Após confirmação, disparar e catalogar no histórico local (`backend/.linkedin-tokens/historico_posts.json`).

### Protocolo 3: Gestão e Catálogo
1. Quando solicitado histórico ou exclusão, invocar `linkedin_listar_posts` ou `linkedin_excluir_post`.

---

## 🔒 Regras e Limitações Estruturais da API do LinkedIn

1. **Credenciais**: Tokens nunca expostos no chat ou versionados no Git. Armazenados em `backend/.linkedin-tokens/sessao_linkedin.json` e isolados no `.gitignore`.
2. **Edição de Perfil**: A API oficial do LinkedIn **não permite** que aplicativos editem campos biográficos (headline, resumo, histórico profissional) por APIs de nível padrão; essas alterações devem ser feitas diretamente no app/site do LinkedIn.
3. **Escopo de Escrita**: Requer o escopo `w_member_social` (fornecido pelo produto *Compartilhe no LinkedIn*).
