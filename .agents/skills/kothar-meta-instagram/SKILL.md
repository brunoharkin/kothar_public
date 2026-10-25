---
name: kothar-meta-instagram
description: >-
  Skill do Kothar v4.0 para gestão e presença profissional em Facebook e Instagram
  através da Meta Graph API e ferramentas MCP tipadas. Permite inspeção de páginas,
  métricas de perfis do Instagram Business, consulta de contas de anúncios da Meta
  e disparo de postagens no Facebook e Instagram.
---

# Skill: Kothar Meta (Facebook & Instagram MCP)

> **Ugarit Digital — Bruno Harkin**  
> Canal de conexão e automação para Páginas do Facebook, Perfis Comerciais do Instagram e Contas de Anúncio da Meta.

---

## 🎯 Gatilhos de Ativação Automática

Ativar esta skill IMEDIATAMENTE sempre que Bruno solicitar:
- *"verifica o instagram"* / *"como está o instagram?"* / *"quem está conectado no instagram?"*
- *"como está o facebook?"* / *"quais páginas temos no facebook?"* / *"detalhes da página do facebook"*
- *"quais contas de anúncio temos?"* / *"como estão meus anúncios na meta?"*
- *"postar no instagram"* / *"publicar foto no instagram"*
- *"postar no facebook"* / *"publicar na página do facebook"*
- *"quais foram os últimos posts na meta?"*

---

## 🛠️ Ferramentas MCP Disponíveis

| Ferramenta MCP | Função | Parâmetros |
| :--- | :--- | :--- |
| `meta_status_conexao` | Retorna status da conexão, páginas ativas, conta do Instagram e validade do token | Nenhum |
| `meta_listar_paginas` | Lista todas as Páginas do Facebook administradas e seus vínculos de Instagram | Nenhum |
| `meta_detalhes_pagina_facebook` | Consulta métricas da página (seguidores, fãs, categoria, descrição) | `page_id` (str opcional) |
| `instagram_obter_perfil` | Consulta seguidores, mídias, bio e dados do Instagram Business (@username) | Nenhum |
| `meta_listar_contas_anuncio` | Lista contas de anúncios da Meta, status (ativa/restrita), moeda e gastos | Nenhum |
| `facebook_publicar_post` | Publica texto ou link na Página do Facebook padrão (requer autorização de Bruno) | `mensagem` (str), `link` (str opcional) |
| `instagram_publicar_foto` | Publica foto com legenda no feed do Instagram Business | `imagem_url` (str pública HTTPS), `legenda` (str) |
| `meta_listar_historico_posts` | Lista o histórico das publicações gerenciadas pelo Kothar no Facebook/Instagram | `limite` (int, default 10) |

---

## 📋 Regras de Operação e Segurança

1. **Gate Obrigatório de Publicação (CP6)**: O Kothar nunca publica nada no Facebook ou Instagram sem aprovação explícita do rascunho por Bruno.
2. **Requisitos do Instagram**: A conta do Instagram deve ser do tipo **Comercial (Business) ou Criador de Conteúdo**, vinculada a uma Página do Facebook.
3. **Mídias para Instagram**: A API da Meta exige que a imagem seja uma URL pública segura (`https://`) em formato JPG/PNG para download pelos servidores da Meta no momento do agendamento/publicação.
4. **Isolamento de Credenciais**: `META_APP_ID`, `META_APP_SECRET` e tokens persistidos exclusivamente em `.env` e `.meta-tokens/`, com proteção no `.gitignore`.
