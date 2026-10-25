"""
=============================================================
 KOTHAR v4.0 — Gerenciador de Integração com Meta (Facebook & Instagram)
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
CAMINHO_TOKENS = DIRETORIO_BACKEND / ".meta-tokens"
ARQUIVO_SESSAO = CAMINHO_TOKENS / "sessao_meta.json"
ARQUIVO_HISTORICO = CAMINHO_TOKENS / "historico_publicacoes.json"
VERSAO_API_META = "v21.0"


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
                if vars_env.get("META_APP_ID"):
                    break
            except Exception:
                pass
    return vars_env


def obter_dados_sessao() -> Dict[str, Any]:
    """Retorna o payload completo da sessão salva."""
    caminhos_sessao = [
        ARQUIVO_SESSAO,
        Path("/app/backend/.meta-tokens/sessao_meta.json"),
        Path("/home/bruno-harkin/kothar/backend/.meta-tokens/sessao_meta.json")
    ]
    for cs in caminhos_sessao:
        if cs.exists():
            try:
                with open(cs, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


def obter_user_access_token() -> str:
    """Recupera o token de acesso do usuário."""
    sessao = obter_dados_sessao()
    token = sessao.get("user_access_token")
    if token:
        return token

    env = obter_credenciais_env()
    token_env = env.get("META_ACCESS_TOKEN")
    if token_env:
        return token_env

    raise ValueError(
        "Token de acesso da Meta não encontrado. "
        "Acesse http://localhost:8080/auth/meta/callback para autorizar sua conta."
    )


def obter_page_access_token() -> str:
    """Recupera o token de página para postagens no Facebook/Instagram."""
    sessao = obter_dados_sessao()
    token = sessao.get("page_access_token_padrao")
    if token:
        return token

    env = obter_credenciais_env()
    token_env = env.get("META_PAGE_ACCESS_TOKEN")
    if token_env:
        return token_env

    # Se não houver page token específico, tenta o user token
    return obter_user_access_token()


def obter_instagram_account_id() -> Optional[str]:
    """Retorna o ID da conta do Instagram Business vinculada."""
    sessao = obter_dados_sessao()
    ig_id = sessao.get("instagram_account_id")
    if ig_id:
        return ig_id

    env = obter_credenciais_env()
    return env.get("META_INSTAGRAM_ACCOUNT_ID") or None


def verificar_status_conexao() -> Dict[str, Any]:
    """
    Testa e valida o status operacional da conexão com o Facebook e Instagram.
    """
    try:
        token = obter_user_access_token()
        sessao = obter_dados_sessao()

        # Testa chamada à Graph API
        url = f"https://graph.facebook.com/{VERSAO_API_META}/me"
        resp = requests.get(url, params={"fields": "id,name", "access_token": token}, timeout=10)

        if resp.status_code == 200:
            dados_me = resp.json()
            paginas = sessao.get("paginas", [])
            ig_id = sessao.get("instagram_account_id")
            ig_user = sessao.get("instagram_username")

            expires_in = sessao.get("expires_in", 0)
            dias_validade = round(expires_in / 86400, 1) if expires_in else None

            return {
                "conectado": True,
                "status": "OPERACIONAL",
                "usuario": {
                    "nome": dados_me.get("name"),
                    "id": dados_me.get("id")
                },
                "total_paginas_facebook": len(paginas),
                "instagram_conectado": bool(ig_id),
                "instagram_username": ig_user if ig_id else None,
                "validade_token_dias": dias_validade
            }
        else:
            return {
                "conectado": False,
                "status": "TOKEN_INVALIDO",
                "erro": resp.text
            }
    except Exception as e:
        return {
            "conectado": False,
            "status": "DESCONECTADO",
            "erro": str(e)
        }


def obter_perfil_instagram() -> Dict[str, Any]:
    """
    Obtém informações do perfil do Instagram Business/Creator conectado.
    """
    ig_id = obter_instagram_account_id()
    if not ig_id:
        raise ValueError(
            "Nenhuma conta de Instagram Business conectada. "
            "Certifique-se de que sua conta do Instagram é Comercial/Criador e está vinculada a uma Página do Facebook."
        )

    token = obter_page_access_token()
    url = f"https://graph.facebook.com/{VERSAO_API_META}/{ig_id}"
    params = {
        "fields": "id,username,name,biography,profile_picture_url,followers_count,follows_count,media_count,website",
        "access_token": token
    }

    resp = requests.get(url, params=params, timeout=12)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(f"Erro ao consultar perfil do Instagram (HTTP {resp.status_code}): {resp.text}")


def listar_paginas_facebook() -> List[Dict[str, Any]]:
    """Lista as páginas do Facebook gerenciadas pela conta autenticada."""
    sessao = obter_dados_sessao()
    return sessao.get("paginas", [])


def _registrar_publicacao_historico(dados: Dict[str, Any]) -> None:
    """Registra uma publicação no histórico local do Kothar."""
    try:
        CAMINHO_TOKENS.mkdir(parents=True, exist_ok=True)
        historico = []
        if ARQUIVO_HISTORICO.exists():
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        historico.insert(0, dados)
        historico = historico[:50]
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def listar_historico_publicacoes() -> List[Dict[str, Any]]:
    """Retorna o histórico de publicações feitas via Kothar no Facebook/Instagram."""
    if ARQUIVO_HISTORICO.exists():
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def publicar_facebook_post(mensagem: str, link: Optional[str] = None) -> Dict[str, Any]:
    """
    Publica uma mensagem ou link na Página do Facebook padrão.
    """
    sessao = obter_dados_sessao()
    paginas = sessao.get("paginas", [])
    if not paginas:
        raise ValueError("Nenhuma Página do Facebook encontrada para realizar a postagem.")

    pagina_padrao = paginas[0]
    page_id = pagina_padrao.get("id")
    page_token = pagina_padrao.get("access_token")

    url = f"https://graph.facebook.com/{VERSAO_API_META}/{page_id}/feed"
    payload = {
        "message": mensagem,
        "access_token": page_token
    }
    if link:
        payload["link"] = link

    resp = requests.post(url, data=payload, timeout=15)
    if resp.status_code == 200:
        dados = resp.json()
        id_post = dados.get("id")
        registro = {
            "plataforma": "FACEBOOK",
            "id": id_post,
            "pagina": pagina_padrao.get("name"),
            "mensagem": mensagem,
            "link": link,
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PUBLICADO"
        }
        _registrar_publicacao_historico(registro)
        return {"sucesso": True, "id_post": id_post, "pagina": pagina_padrao.get("name")}
    else:
        return {"sucesso": False, "erro": f"HTTP {resp.status_code}: {resp.text}"}


def publicar_instagram_foto(imagem_url: str, legenda: str) -> Dict[str, Any]:
    """
    Publica uma foto com legenda no Instagram Business/Creator via Content Publishing API.
    Fluxo de 2 passos da Meta:
    1. Criar container de mídia (/media)
    2. Publicar container (/media_publish)
    """
    ig_id = obter_instagram_account_id()
    if not ig_id:
        return {
            "sucesso": False,
            "erro": "Nenhuma conta comercial de Instagram vinculada à Página do Facebook."
        }

    token = obter_page_access_token()

    # Passo 1: Criar container
    url_container = f"https://graph.facebook.com/{VERSAO_API_META}/{ig_id}/media"
    payload_container = {
        "image_url": imagem_url,
        "caption": legenda,
        "access_token": token
    }
    r_container = requests.post(url_container, data=payload_container, timeout=20)
    if r_container.status_code != 200:
        return {"sucesso": False, "erro": f"Falha ao criar container no Instagram: {r_container.text}"}

    creation_id = r_container.json().get("id")
    if not creation_id:
        return {"sucesso": False, "erro": "ID do container não retornado pelo Instagram."}

    # Passo 2: Publicar
    url_publish = f"https://graph.facebook.com/{VERSAO_API_META}/{ig_id}/media_publish"
    payload_publish = {
        "creation_id": creation_id,
        "access_token": token
    }
    r_publish = requests.post(url_publish, data=payload_publish, timeout=20)
    if r_publish.status_code == 200:
        dados_pub = r_publish.json()
        post_id = dados_pub.get("id")
        registro = {
            "plataforma": "INSTAGRAM",
            "id": post_id,
            "legenda": legenda,
            "imagem_url": imagem_url,
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PUBLICADO"
        }
        _registrar_publicacao_historico(registro)
        return {"sucesso": True, "id_post": post_id}
    else:
        return {"sucesso": False, "erro": f"Falha ao publicar container no Instagram: {r_publish.text}"}


def obter_detalhes_pagina_facebook(page_id: Optional[str] = None) -> Dict[str, Any]:
    """Obtém detalhes da Página do Facebook (seguidores, fãs, categoria, sobre)."""
    sessao = obter_dados_sessao()
    paginas = sessao.get("paginas", [])
    if not paginas:
        return {}

    alvo = paginas[0]
    if page_id:
        for p in paginas:
            if p.get("id") == page_id:
                alvo = p
                break

    token = alvo.get("access_token") or obter_page_access_token()
    pid = alvo.get("id")

    url = f"https://graph.facebook.com/{VERSAO_API_META}/{pid}"
    params = {
        "fields": "id,name,about,description,fan_count,followers_count,category",
        "access_token": token
    }
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return {}


def listar_contas_anuncio() -> List[Dict[str, Any]]:
    """Consulta as contas de anúncios da Meta associadas ao usuário."""
    token = obter_user_access_token()
    url = f"https://graph.facebook.com/{VERSAO_API_META}/me/adaccounts"
    params = {
        "fields": "id,name,account_id,account_status,currency,amount_spent",
        "access_token": token
    }
    resp = requests.get(url, params=params, timeout=12)
    if resp.status_code == 200:
        return resp.json().get("data", [])
    return []

