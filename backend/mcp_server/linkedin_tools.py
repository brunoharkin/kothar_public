"""
=============================================================
 KOTHAR v4.0 — Ferramentas MCP para LinkedIn
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import json
from typing import Optional
from backend.servicos.comunicacao_linkedin.gerenciador_linkedin import (
    verificar_status_conexao,
    obter_perfil_usuario,
    publicar_post_texto,
    publicar_post_link,
    excluir_post,
    listar_historico_publicacoes
)


async def linkedin_status_conexao() -> str:
    """
    Retorna o status operacional da integração com o LinkedIn,
    indicando validade do token, escopos aprovados e se está pronto para operar.
    """
    try:
        resultado = verificar_status_conexao()
        if not resultado.get("conectado"):
            return (
                "❌ LinkedIn Desconectado ou Token Inválido.\n"
                f"Detalhe: {resultado.get('erro', 'Acesse http://localhost:8080/auth/linkedin/callback para autenticar.')}"
            )

        perfil = resultado.get("perfil", {})
        escopos = ", ".join(resultado.get("escopos_ativos", []))
        dias = resultado.get("validade_token_dias", "Desconhecido")
        pode_publicar = "Sim (w_member_social ativo)" if resultado.get("pode_publicar") else "Não (apenas leitura de perfil/OpenID)"

        linhas = [
            "💼 STATUS DA CONEXÃO LINKEDIN:",
            f"• Perfil Vinculado: {perfil.get('nome')} ({perfil.get('email')})",
            f"• ID Membro: {perfil.get('id_membro')}",
            f"• Status: {resultado.get('status')} ✅",
            f"• Validade Estimada do Token: ~{dias} dias",
            f"• Escopos Ativos: {escopos}",
            f"• Permissão de Postagem: {pode_publicar}"
        ]
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao verificar status do LinkedIn: {str(e)}"


async def linkedin_obter_perfil() -> str:
    """
    Consulta e formata os dados do perfil profissional do usuário autenticado no LinkedIn.
    Retorna Nome, E-mail, ID único, Localidade e URL da Foto.
    """
    try:
        p = obter_perfil_usuario()
        linhas = [
            f"👤 PERFIL LINKEDIN — {p.get('nome')}:",
            f"• ID Membro: {p.get('id_membro')}",
            f"• Primeiro Nome: {p.get('primeiro_nome')}",
            f"• Sobrenome: {p.get('sobrenome')}",
            f"• E-mail: {p.get('email')} {'(Verificado)' if p.get('email_verificado') else ''}",
            f"• Localidade: {p.get('pais', 'N/A')} ({p.get('idioma', 'N/A')})",
            f"• Foto de Perfil: {p.get('foto_url', 'Sem foto')}"
        ]
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar perfil no LinkedIn: {str(e)}"


async def linkedin_publicar_post(texto: str) -> str:
    """
    Publica uma mensagem de texto simples no feed pessoal do LinkedIn.
    Requer autorização prévia de Bruno.
    
    Args:
        texto: Conteúdo a ser publicado no feed.
    """
    if not texto or not texto.strip():
        return "❌ Erro: Texto da publicação não pode ser vazio."

    try:
        res = publicar_post_texto(texto.strip())
        if res.get("sucesso"):
            return (
                f"✅ Post publicado com sucesso no LinkedIn!\n"
                f"• ID do Post: {res.get('id_post')}\n"
                f"• Status: {res.get('status')}"
            )
        else:
            return f"⚠️ Falha ao publicar:\n{res.get('erro')}"
    except Exception as e:
        return f"❌ Erro ao disparar publicação no LinkedIn: {str(e)}"


async def linkedin_publicar_post_link(
    texto: str,
    url_link: str,
    titulo: Optional[str] = None,
    descricao: Optional[str] = None
) -> str:
    """
    Publica um post com pré-visualização de link (Artigo, site ou projeto) no LinkedIn.
    
    Args:
        texto: Texto do post / comentário.
        url_link: URL do link a ser compartilhado.
        titulo: Título da matéria/link (opcional).
        descricao: Descrição curta do link (opcional).
    """
    if not texto or not url_link:
        return "❌ Erro: Texto e URL do link são obrigatórios."

    try:
        res = publicar_post_link(
            texto=texto.strip(),
            url_link=url_link.strip(),
            titulo=titulo.strip() if titulo else None,
            descricao=descricao.strip() if descricao else None
        )
        if res.get("sucesso"):
            return (
                f"✅ Artigo/Link compartilhado com sucesso no LinkedIn!\n"
                f"• Link: {url_link}\n"
                f"• ID do Post: {res.get('id_post')}\n"
                f"• Status: {res.get('status')}"
            )
        else:
            return f"⚠️ Falha ao compartilhar link:\n{res.get('erro')}"
    except Exception as e:
        return f"❌ Erro ao disparar post com link: {str(e)}"


async def linkedin_listar_posts(limite: int = 10) -> str:
    """
    Lista o histórico das publicações gerenciadas pelo Kothar no LinkedIn.
    
    Args:
        limite: Quantidade máxima de publicações para exibir (padrão 10).
    """
    try:
        posts = listar_historico_publicacoes()
        if not posts:
            return "📋 Nenhuma publicação catalogada no histórico do Kothar até o momento."

        linhas = [f"📋 HISTÓRICO DE PUBLICAÇÕES LINKEDIN (Últimos {min(limite, len(posts))}):"]
        for idx, p in enumerate(posts[:limite], 1):
            status = p.get("status", "PUBLICADO")
            linhas.append(
                f"{idx}. [{status}] Data: {p.get('data')} | Tipo: {p.get('tipo')}\n"
                f"   Texto: \"{p.get('texto')[:100]}...\"\n"
                f"   ID: {p.get('id')}\n"
            )
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao listar posts: {str(e)}"


async def linkedin_excluir_post(post_urn: str) -> str:
    """
    Exclui uma publicação do LinkedIn pelo seu ID ou URN.
    
    Args:
        post_urn: URN ou identificador do post a ser excluído.
    """
    if not post_urn or not post_urn.strip():
        return "❌ Erro: URN do post é obrigatório."

    try:
        res = excluir_post(post_urn.strip())
        if res.get("sucesso"):
            return f"🗑️ Post {post_urn} removido com sucesso do LinkedIn."
        else:
            return f"⚠️ Falha ao remover post:\n{res.get('erro')}"
    except Exception as e:
        return f"❌ Erro ao excluir post: {str(e)}"
