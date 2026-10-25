"""
=============================================================
 KOTHAR v4.0 — Gerenciador de Integração com LinkedIn
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

DIRETORIO_BACKEND = Path(__file__).resolve().parent.parent.parent
ARQUIVO_ENV = DIRETORIO_BACKEND / ".env"
CAMINHO_TOKENS = DIRETORIO_BACKEND / ".linkedin-tokens"
ARQUIVO_SESSAO = CAMINHO_TOKENS / "sessao_linkedin.json"
ARQUIVO_HISTORICO_POSTS = CAMINHO_TOKENS / "historico_posts.json"


def obter_credenciais_env() -> Dict[str, str]:
    """Carrega credenciais do arquivo .env."""
    caminhos = [
        ARQUIVO_ENV,
        Path("/app/.env"),
        Path("/home/bruno-harkin/kothar/.env")
    ]
    vars_env = {}
    for p in caminhos:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for l in f:
                        l = l.strip()
                        if l and not l.startswith("#") and "=" in l:
                            k, v = l.split("=", 1)
                            vars_env[k.strip()] = v.strip()
                if vars_env.get("LINKEDIN_CLIENT_ID"):
                    break
            except Exception:
                pass
    return vars_env


def obter_access_token() -> str:
    """Recupera o access token do LinkedIn persistido."""
    caminhos_sessao = [
        ARQUIVO_SESSAO,
        Path("/app/backend/.linkedin-tokens/sessao_linkedin.json"),
        Path("/home/bruno-harkin/kothar/backend/.linkedin-tokens/sessao_linkedin.json")
    ]
    for cs in caminhos_sessao:
        if cs.exists():
            try:
                with open(cs, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    token = dados.get("access_token")
                    if token:
                        return token
            except Exception:
                pass

    env = obter_credenciais_env()
    token = env.get("LINKEDIN_ACCESS_TOKEN")
    if token:
        return token

    raise ValueError(
        "Token de acesso do LinkedIn não encontrado. "
        "Acesse http://localhost:8080/auth/linkedin/callback para autorizar a conta."
    )


def obter_dados_sessao() -> Dict[str, Any]:
    """Retorna o payload completo da sessão salva."""
    caminhos_sessao = [
        ARQUIVO_SESSAO,
        Path("/app/backend/.linkedin-tokens/sessao_linkedin.json"),
        Path("/home/bruno-harkin/kothar/backend/.linkedin-tokens/sessao_linkedin.json")
    ]
    for cs in caminhos_sessao:
        if cs.exists():
            try:
                with open(cs, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


def obter_perfil_usuario() -> Dict[str, Any]:
    """
    Consulta os dados de perfil da conta do LinkedIn conectada
    através do endpoint OpenID /userinfo.
    """
    token = obter_access_token()
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    resp = requests.get(url, headers=headers, timeout=12)
    if resp.status_code == 200:
        dados = resp.json()
        return {
            "sucesso": True,
            "id_membro": dados.get("sub"),
            "nome": dados.get("name"),
            "primeiro_nome": dados.get("given_name"),
            "sobrenome": dados.get("family_name"),
            "email": dados.get("email"),
            "email_verificado": dados.get("email_verified", False),
            "foto_url": dados.get("picture"),
            "pais": dados.get("locale", {}).get("country") if isinstance(dados.get("locale"), dict) else None,
            "idioma": dados.get("locale", {}).get("language") if isinstance(dados.get("locale"), dict) else None
        }
    elif resp.status_code == 401:
        raise PermissionError("Token do LinkedIn expirado ou revogado. Faça nova autorização.")
    else:
        raise RuntimeError(f"Falha ao consultar perfil no LinkedIn (HTTP {resp.status_code}): {resp.text}")


def verificar_status_conexao() -> Dict[str, Any]:
    """
    Testa e valida o status operacional da conexão com o LinkedIn.
    """
    try:
        sessao = obter_dados_sessao()
        perfil = obter_perfil_usuario()
        
        escopos_str = sessao.get("scope", "")
        expires_in = sessao.get("expires_in", 0)
        
        dias_validade = round(expires_in / 86400, 1) if expires_in else None
        escopos = [e.strip() for e in escopos_str.replace(",", " ").split() if e.strip()]

        return {
            "conectado": True,
            "status": "OPERACIONAL",
            "perfil": {
                "nome": perfil.get("nome"),
                "email": perfil.get("email"),
                "id_membro": perfil.get("id_membro")
            },
            "escopos_ativos": escopos,
            "validade_token_dias": dias_validade,
            "pode_publicar": "w_member_social" in escopos
        }
    except Exception as e:
        return {
            "conectado": False,
            "status": "DESCONECTADO",
            "erro": str(e)
        }


def _registrar_post_historico(dados_post: Dict[str, Any]) -> None:
    """Registra uma publicação no histórico local do Kothar."""
    try:
        CAMINHO_TOKENS.mkdir(parents=True, exist_ok=True)
        historico = []
        if ARQUIVO_HISTORICO_POSTS.exists():
            with open(ARQUIVO_HISTORICO_POSTS, "r", encoding="utf-8") as f:
                historico = json.load(f)
        historico.insert(0, dados_post)
        historico = historico[:50]  # Mantém os últimos 50
        with open(ARQUIVO_HISTORICO_POSTS, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def listar_historico_publicacoes() -> List[Dict[str, Any]]:
    """Retorna os posts gerenciados e publicados pelo Kothar."""
    if ARQUIVO_HISTORICO_POSTS.exists():
        try:
            with open(ARQUIVO_HISTORICO_POSTS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def publicar_post_texto(texto: str) -> Dict[str, Any]:
    """
    Publica um texto no perfil pessoal do LinkedIn do usuário autenticado.
    Requer o escopo w_member_social.
    """
    token = obter_access_token()
    sessao = obter_dados_sessao()
    escopos = sessao.get("scope", "")

    if "w_member_social" not in escopos:
        return {
            "sucesso": False,
            "erro": (
                "Permissão de publicação ('w_member_social') não está ativa neste token. "
                "Reautorize em http://localhost:8080/auth/linkedin/callback."
            )
        }

    perfil = obter_perfil_usuario()
    autor_urn = f"urn:li:person:{perfil['id_membro']}"

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": autor_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": texto
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code in (200, 201):
        dados = resp.json()
        id_post = dados.get("id")
        registro = {
            "id": id_post,
            "tipo": "TEXTO",
            "texto": texto,
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PUBLICADO",
            "autor": perfil.get("nome")
        }
        _registrar_post_historico(registro)
        return {
            "sucesso": True,
            "id_post": id_post,
            "status": "PUBLICADO"
        }
    else:
        return {
            "sucesso": False,
            "erro": f"Erro HTTP {resp.status_code}: {resp.text}"
        }


def publicar_post_link(texto: str, url_link: str, titulo: Optional[str] = None, descricao: Optional[str] = None) -> Dict[str, Any]:
    """
    Publica um post com link incorporado e pré-visualização (Article Share).
    Requer o escopo w_member_social.
    """
    token = obter_access_token()
    sessao = obter_dados_sessao()
    escopos = sessao.get("scope", "")

    if "w_member_social" not in escopos:
        return {
            "sucesso": False,
            "erro": "Permissão de publicação ('w_member_social') ausente."
        }

    perfil = obter_perfil_usuario()
    autor_urn = f"urn:li:person:{perfil['id_membro']}"

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    media_obj = {
        "status": "READY",
        "originalUrl": url_link
    }
    if titulo:
        media_obj["title"] = {"text": titulo}
    if descricao:
        media_obj["description"] = {"text": descricao}

    payload = {
        "author": autor_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": texto
                },
                "shareMediaCategory": "ARTICLE",
                "media": [media_obj]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code in (200, 201):
        dados = resp.json()
        id_post = dados.get("id")
        registro = {
            "id": id_post,
            "tipo": "ARTIGO_LINK",
            "texto": texto,
            "url_link": url_link,
            "titulo": titulo,
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PUBLICADO",
            "autor": perfil.get("nome")
        }
        _registrar_post_historico(registro)
        return {
            "sucesso": True,
            "id_post": id_post,
            "status": "PUBLICADO"
        }
    else:
        return {
            "sucesso": False,
            "erro": f"Erro HTTP {resp.status_code}: {resp.text}"
        }


def excluir_post(post_urn: str) -> Dict[str, Any]:
    """
    Exclui um post do LinkedIn pelo URN/ID.
    """
    token = obter_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    # Formata URL
    encoded_urn = requests.utils.quote(post_urn, safe="")
    url = f"https://api.linkedin.com/v2/ugcPosts/{encoded_urn}"

    resp = requests.delete(url, headers=headers, timeout=12)
    if resp.status_code in (200, 204):
        # Atualiza status no histórico local
        try:
            if ARQUIVO_HISTORICO_POSTS.exists():
                with open(ARQUIVO_HISTORICO_POSTS, "r", encoding="utf-8") as f:
                    historico = json.load(f)
                for h in historico:
                    if h.get("id") == post_urn:
                        h["status"] = "EXCLUÍDO"
                with open(ARQUIVO_HISTORICO_POSTS, "w", encoding="utf-8") as f:
                    json.dump(historico, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return {"sucesso": True, "status": "EXCLUÍDO"}
    else:
        return {"sucesso": False, "erro": f"Erro HTTP {resp.status_code}: {resp.text}"}
