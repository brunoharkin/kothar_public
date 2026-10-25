"""
=============================================================
 KOTHAR v4.0 — Ferramentas MCP para Meta (Facebook & Instagram)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import json
from typing import Optional
from backend.servicos.comunicacao_meta.gerenciador_meta import (
    verificar_status_conexao,
    obter_perfil_instagram,
    listar_paginas_facebook,
    obter_detalhes_pagina_facebook,
    listar_contas_anuncio,
    publicar_facebook_post,
    publicar_instagram_foto,
    listar_historico_publicacoes
)


async def meta_status_conexao() -> str:
    """
    Retorna o status operacional da integração com Facebook e Instagram,
    incluindo páginas associadas e conta do Instagram Business ativa.
    """
    try:
        res = verificar_status_conexao()
        if not res.get("conectado"):
            return (
                "❌ Meta (Facebook/Instagram) Desconectada.\n"
                f"Detalhe: {res.get('erro', 'Acesse http://localhost:8080/auth/meta/callback para autorizar a conta.')}"
            )

        usuario = res.get("usuario", {})
        dias = res.get("validade_token_dias", "N/A")
        ig_status = f"@{res.get('instagram_username')}" if res.get("instagram_conectado") else "Não conectado"

        linhas = [
            "📸 STATUS DA CONEXÃO META (FACEBOOK & INSTAGRAM):",
            f"• Usuário: {usuario.get('nome')} (ID: {usuario.get('id')})",
            f"• Status: {res.get('status')} ✅",
            f"• Páginas do Facebook Gerenciadas: {res.get('total_paginas_facebook')}",
            f"• Instagram Business: {ig_status}",
            f"• Validade Estimada do Token: ~{dias} dias"
        ]
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao verificar status da Meta: {str(e)}"


async def meta_listar_paginas() -> str:
    """
    Lista todas as Páginas do Facebook administradas pela conta conectada.
    """
    try:
        paginas = listar_paginas_facebook()
        if not paginas:
            return "📋 Nenhuma Página do Facebook vinculada a esta conta."

        linhas = [f"📋 PÁGINAS DO FACEBOOK ({len(paginas)} encontradas):"]
        for idx, p in enumerate(paginas, 1):
            ig = p.get("instagram_business_account", {})
            ig_txt = f"Instagram: @{ig.get('username')}" if ig else "Sem Instagram vinculado"
            linhas.append(f"{idx}. {p.get('name')} (ID: {p.get('id')}) — {ig_txt}")
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao listar páginas: {str(e)}"


async def instagram_obter_perfil() -> str:
    """
    Consulta métricas e detalhes do perfil do Instagram Business/Creator conectado
    (seguidores, seguindo, total de mídias, bio e website).
    """
    try:
        p = obter_perfil_instagram()
        linhas = [
            f"📷 PERFIL DO INSTAGRAM — @{p.get('username')}:",
            f"• Nome: {p.get('name')}",
            f"• Seguidores: {p.get('followers_count'):,} | Seguindo: {p.get('follows_count'):,}",
            f"• Publicações: {p.get('media_count')}",
            f"• Bio: \"{p.get('biography', '')}\"",
            f"• Website: {p.get('website', 'Nenhum')}",
            f"• Foto: {p.get('profile_picture_url', 'Sem foto')}"
        ]
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar perfil do Instagram: {str(e)}"


async def facebook_publicar_post(mensagem: str, link: Optional[str] = None) -> str:
    """
    Publica uma mensagem ou link na Página padrão do Facebook.
    Requer aprovação prévia de Bruno.
    
    Args:
        mensagem: Texto da publicação.
        link: URL externa opcional para anexar ao post.
    """
    if not mensagem or not mensagem.strip():
        return "❌ Erro: Mensagem não pode ser vazia."

    try:
        res = publicar_facebook_post(mensagem.strip(), link.strip() if link else None)
        if res.get("sucesso"):
            return (
                f"✅ Publicado com sucesso no Facebook!\n"
                f"• Página: {res.get('pagina')}\n"
                f"• ID do Post: {res.get('id_post')}"
            )
        else:
            return f"⚠️ Falha ao publicar no Facebook: {res.get('erro')}"
    except Exception as e:
        return f"❌ Erro ao disparar post no Facebook: {str(e)}"


async def instagram_publicar_foto(imagem_url: str, legenda: str) -> str:
    """
    Publica uma foto com legenda no feed do Instagram Business.
    Requer uma URL pública acessível da imagem (HTTPS) e aprovação de Bruno.
    
    Args:
        imagem_url: URL pública da imagem (JPG ou PNG).
        legenda: Texto/legenda da postagem.
    """
    if not imagem_url or not legenda:
        return "❌ Erro: Imagem URL e legenda são obrigatórias."

    try:
        res = publicar_instagram_foto(imagem_url.strip(), legenda.strip())
        if res.get("sucesso"):
            return (
                f"✅ Publicado com sucesso no Instagram!\n"
                f"• ID da Mídia: {res.get('id_post')}"
            )
        else:
            return f"⚠️ Falha ao publicar no Instagram: {res.get('erro')}"
    except Exception as e:
        return f"❌ Erro ao disparar foto no Instagram: {str(e)}"


async def meta_listar_historico_posts(limite: int = 10) -> str:
    """
    Lista o histórico de posts gerenciados e disparados pelo Kothar no Facebook e Instagram.
    """
    try:
        posts = listar_historico_publicacoes()
        if not posts:
            return "📋 Nenhuma publicação catalogada no histórico da Meta."

        linhas = [f"📋 HISTÓRICO DE PUBLICAÇÕES META (Últimos {min(limite, len(posts))}):"]
        for idx, p in enumerate(posts[:limite], 1):
            plat = p.get("plataforma", "META")
            txt = p.get("mensagem") or p.get("legenda", "")
            linhas.append(
                f"{idx}. [{plat}] Data: {p.get('data')} | ID: {p.get('id')}\n"
                f"   Texto: \"{txt[:100]}...\"\n"
            )
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao listar posts da Meta: {str(e)}"


async def meta_detalhes_pagina_facebook(page_id: Optional[str] = None) -> str:
    """
    Retorna métricas da Página do Facebook (seguidores, fãs, categoria e descrição).
    """
    try:
        dados = obter_detalhes_pagina_facebook(page_id)
        if not dados:
            return "📋 Nenhuma informação retornada para a Página do Facebook."

        linhas = [
            f"📄 PÁGINA DO FACEBOOK — {dados.get('name')}:",
            f"• ID da Página: {dados.get('id')}",
            f"• Categoria: {dados.get('category', 'N/A')}",
            f"• Fãs / Curtidas: {dados.get('fan_count', 0):,}",
            f"• Seguidores: {dados.get('followers_count', 0):,}",
            f"• Sobre / Descrição: \"{dados.get('about') or dados.get('description') or 'Sem descrição'}\""
        ]
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar detalhes da página: {str(e)}"


async def meta_listar_contas_anuncio() -> str:
    """
    Lista todas as contas de anúncios da Meta (Facebook/Instagram Ads),
    informando nome, ID da conta, status (ativa/restrita), moeda e total gasto.
    """
    try:
        contas = listar_contas_anuncio()
        if not contas:
            return "📋 Nenhuma conta de anúncios encontrada vinculada a este usuário."

        status_map = {1: "🟢 Ativa", 2: "🔴 Desativada", 3: "⚠️ Restrita/Pendente", 7: "Pendente"}
        linhas = [f"📢 CONTAS DE ANÚNCIOS META ({len(contas)} encontradas):"]
        for idx, c in enumerate(contas, 1):
            st = status_map.get(c.get("account_status"), f"Status {c.get('account_status')}")
            gasto_centavos = int(c.get("amount_spent", 0))
            gasto_fmt = f"R$ {gasto_centavos / 100:.2f}" if c.get("currency") == "BRL" else f"{c.get('currency')} {gasto_centavos / 100:.2f}"
            linhas.append(
                f"{idx}. {c.get('name')} (ID: {c.get('account_id')})\n"
                f"   • Status: {st} | Moeda: {c.get('currency')} | Total Gasto: {gasto_fmt}"
            )
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar contas de anúncios: {str(e)}"

