# Kothar v4.0 — Registro de Arquitetura: Integração Meta (Facebook & Instagram)
**Data:** 13 de outubro de 2026  
**Responsável:** Bruno Harkin | Ugarit Digital  
**Módulos:** Meta Graph API v21.0, Facebook Login, Instagram Business API, FastAPI Backend, MCP Server

---

## 1. Contexto e Objetivo

Integração oficial das contas de **Facebook Pages** e **Instagram Business** (`Crm-sophia`) ao Kothar para:
1. Inspeção de páginas e perfis de Instagram conectados.
2. Consulta de métricas (seguidores, publicações, bio) no Instagram Business.
3. Publicação assistida de posts e links no Facebook e fotos no Instagram.
4. Exposição através de 6 ferramentas MCP tipadas.

---

## 2. Decisões Arquiteturais e Implementação

1. **Roteador Nativo FastAPI (`/auth/meta/callback`)**:
   - Criado em `backend/api/routers/autenticacao_meta.py` e registrado em `main.py`.
   - Gerencia a autorização OAuth2 com Graph API v21.0, troca de token temporário por `long_lived_access_token` (60 dias), extração de `me/accounts` e descoberta automática de `instagram_business_account`.
   - Salva a sessão em `backend/.meta-tokens/sessao_meta.json` e no `.env`.

2. **Segurança e Isolamento**:
   - `META_APP_ID` e `META_APP_SECRET` mantidos exclusivamente no `.env`.
   - Diretório `backend/.meta-tokens/` adicionado ao `.gitignore`.
   - Scanner de credenciais verificado em 100%.

3. **Camada de Serviço (`backend/servicos/comunicacao_meta/gerenciador_meta.py`)**:
   - Métodos estruturados para Facebook Feed e fluxo em 2 etapas para Instagram Content Publishing API (`/media` + `/media_publish`).

4. **Ferramentas MCP (`backend/mcp_server/meta_tools.py`)**:
   - `meta_status_conexao`
   - `meta_listar_paginas`
   - `instagram_obter_perfil`
   - `facebook_publicar_post`
   - `instagram_publicar_foto`
   - `meta_listar_historico_posts`

5. **Skill Catalogada**:
   - Criada `.agents/skills/kothar-meta-instagram/SKILL.md` (82ª skill do Kothar).

---

## 3. Estado Atual da Conexão

- **Usuário Conectado**: Bruno Harkin (ID: 959318120456147)
- **Página do Facebook Vinculada**: Ugarit digitall (ID: 1093379693867864)
- **Instagram Business Vinculado**: @ugarit_digitall (ID: 17841423361765032)
- **Status da Conexão**: OPERACIONAL ✅ (Token de Longa Duração ~60 dias)
- **Health Check**: 31/31 Aprovadas (100% funcional)

