"""
=============================================================
 KOTHAR v4.0 — Router de Autenticação OAuth2 Meta (Facebook & Instagram)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import os
import json
import urllib.parse
from pathlib import Path
import requests
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth/meta", tags=["Meta-Auth"])

DIRETORIO_BACKEND = Path(__file__).resolve().parent.parent.parent
CAMINHO_TOKENS = DIRETORIO_BACKEND / ".meta-tokens"
ARQUIVO_SESSAO = CAMINHO_TOKENS / "sessao_meta.json"
VERSAO_API_META = "v21.0"


def carregar_credenciais_env():
    caminhos = [
        DIRETORIO_BACKEND / ".env",
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


@router.get("/callback", response_class=HTMLResponse)
async def callback_oauth_meta(
    code: str = Query(None),
    error: str = Query(None),
    error_reason: str = Query(None),
    error_description: str = Query(None)
):
    env = carregar_credenciais_env()
    app_id = env.get("META_APP_ID", "2111706022717804")
    app_secret = env.get("META_APP_SECRET", "")
    redirect_uri = env.get("META_REDIRECT_URI", "http://localhost:8080/auth/meta/callback")

    # Escopos para Facebook Pages e Instagram Business/Content
    escopos = [
        "public_profile",
        "email",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_comments",
        "instagram_manage_insights"
    ]
    escopo_str = ",".join(escopos)

    params_novo = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": "kothar_meta_auth_state",
        "response_type": "code",
        "scope": escopo_str
    }
    url_reautorizar = f"https://www.facebook.com/{VERSAO_API_META}/dialog/oauth?" + urllib.parse.urlencode(params_novo)

    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Erro Meta</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #f87171; text-align: center; padding: 60px;">
            <h1 style="color: #ef4444;">❌ Erro na Autorização Meta (Facebook/Instagram)</h1>
            <p style="color: #cbd5e1; font-size: 16px;">Erro: <b>{error}</b> ({error_reason or ''})</p>
            <p style="color: #94a3b8; font-size: 14px;">{error_description or ''}</p>
            <br>
            <a href="{url_reautorizar}" style="background: #1877f2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Tentar Novamente</a>
        </body>
        </html>
        """

    if not code:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Conectar Meta & Instagram</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #e2e8f0; text-align: center; padding: 60px;">
            <div style="max-width: 650px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <h1 style="color: #1877f2; margin-bottom: 5px;">📸 KOTHAR v4.0 — Facebook & Instagram</h1>
                <h3 style="color: #cbd5e1; margin-top: 0;">Ugarit Digital — Integração Oficial</h3>
                <p style="color: #94a3b8; font-size: 15px; line-height: 1.6;">
                    Clique no botão abaixo para vincular sua conta do Facebook, suas Páginas comerciais e contas do Instagram Business ao Kothar:
                </p>
                <div style="background: #0f172a; padding: 15px; border-radius: 8px; margin: 25px 0; text-align: left; font-size: 13px; color: #94a3b8;">
                    • <b>App ID:</b> {app_id}<br>
                    • <b>Permissões:</b> Perfil, Páginas, Publicação no Feed e Instagram Graph API
                </div>
                <a href="{url_reautorizar}" style="background: linear-gradient(135deg, #1877f2 0%, #d62976 100%); color: #fff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                    👉 Conectar Facebook & Instagram
                </a>
            </div>
        </body>
        </html>
        """

    # 1. Trocar código por short-lived access token
    url_token_endpoint = f"https://graph.facebook.com/{VERSAO_API_META}/oauth/access_token"
    params_token = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }

    try:
        r = requests.get(url_token_endpoint, params=params_token, timeout=15)
        if r.status_code != 200:
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Kothar — Erro de Token</title></head>
            <body style="font-family: monospace; background: #0b0f19; color: #f87171; text-align: center; padding: 60px;">
                <h2>❌ Falha ao obter token de acesso da Meta:</h2>
                <p>{r.text}</p>
                <br>
                <a href="{url_reautorizar}" style="background: #1877f2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Tentar Novamente</a>
            </body>
            </html>
            """

        resp_token = r.json()
        short_token = resp_token.get("access_token")

        # 2. Trocar por Long-Lived Token (60 dias)
        params_long_lived = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token
        }
        r_long = requests.get(url_token_endpoint, params=params_long_lived, timeout=15)
        long_token = short_token
        expires_in = resp_token.get("expires_in", 5184000)
        if r_long.status_code == 200:
            resp_long = r_long.json()
            long_token = resp_long.get("access_token", short_token)
            expires_in = resp_long.get("expires_in", expires_in)

        # 3. Buscar dados do usuário
        r_me = requests.get(
            f"https://graph.facebook.com/{VERSAO_API_META}/me",
            params={"fields": "id,name,email", "access_token": long_token},
            timeout=10
        )
        dados_usuario = r_me.json() if r_me.status_code == 200 else {}
        nome_usuario = dados_usuario.get("name", "Usuário Meta")
        email_usuario = dados_usuario.get("email", "")

        # 4. Buscar páginas e contas do Instagram vinculadas
        r_accounts = requests.get(
            f"https://graph.facebook.com/{VERSAO_API_META}/me/accounts",
            params={
                "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}",
                "access_token": long_token
            },
            timeout=15
        )
        paginas = []
        page_token_principal = ""
        instagram_account_id = ""
        instagram_username = ""

        if r_accounts.status_code == 200:
            paginas = r_accounts.json().get("data", [])
            if paginas:
                # Usa a primeira página encontrada como padrão
                pri = paginas[0]
                page_token_principal = pri.get("access_token", "")
                ig = pri.get("instagram_business_account", {})
                if ig:
                    instagram_account_id = ig.get("id", "")
                    instagram_username = ig.get("username", "")

        # 5. Salvar payload completo em .meta-tokens/sessao_meta.json
        CAMINHO_TOKENS.mkdir(parents=True, exist_ok=True)
        dados_salvar = {
            "usuario": dados_usuario,
            "user_access_token": long_token,
            "expires_in": expires_in,
            "page_access_token_padrao": page_token_principal,
            "instagram_account_id": instagram_account_id,
            "instagram_username": instagram_username,
            "paginas": paginas
        }
        with open(ARQUIVO_SESSAO, "w", encoding="utf-8") as f:
            json.dump(dados_salvar, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(ARQUIVO_SESSAO, 0o644)
        except Exception:
            pass

        # 6. Atualizar .env no host
        caminho_env_host = DIRETORIO_BACKEND / ".env"
        if caminho_env_host.exists() and os.access(caminho_env_host, os.W_OK):
            try:
                linhas = []
                with open(caminho_env_host, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                novas = []
                for l in linhas:
                    if l.startswith("META_ACCESS_TOKEN=") and long_token:
                        novas.append(f"META_ACCESS_TOKEN={long_token}\n")
                    elif l.startswith("META_PAGE_ACCESS_TOKEN=") and page_token_principal:
                        novas.append(f"META_PAGE_ACCESS_TOKEN={page_token_principal}\n")
                    elif l.startswith("META_INSTAGRAM_ACCOUNT_ID=") and instagram_account_id:
                        novas.append(f"META_INSTAGRAM_ACCOUNT_ID={instagram_account_id}\n")
                    else:
                        novas.append(l)
                with open(caminho_env_host, "w", encoding="utf-8") as f:
                    f.writelines(novas)
            except Exception:
                pass

        total_paginas = len(paginas)
        tem_ig = bool(instagram_account_id)

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Meta Conectada</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #38bdf8; text-align: center; padding: 60px;">
            <div style="max-width: 650px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <h1 style="color: #1877f2; margin-bottom: 5px;">🚀 Meta & Instagram Conectados!</h1>
                <h3 style="color: #f8fafc; margin-top: 0;">Kothar v4.0 — Ugarit Digital</h3>
                <p style="color: #94a3b8; font-size: 15px; line-height: 1.6;">
                    Usuário autenticado: <b style="color: #38bdf8;">{nome_usuario}</b><br>
                    {f'E-mail: <b style="color: #cbd5e1;">{email_usuario}</b><br>' if email_usuario else ''}
                    Tokens de longa duração salvos com isolamento no Kothar.
                </p>
                <div style="background: #0f172a; padding: 18px; border-radius: 8px; margin: 25px 0; text-align: left; font-size: 14px; border: 1px solid #1e293b;">
                    <div style="color: #a7f3d0; margin-bottom: 8px;">🔒 Status da Conexão: <b>ATIVA</b></div>
                    <div style="color: #cbd5e1;">• Páginas do Facebook detectadas: <b>{total_paginas}</b></div>
                    <div style="color: #cbd5e1;">• Instagram Business conectado: <b>{'@' + instagram_username if tem_ig else 'Nenhum perfil comercial vinculado à página'}</b></div>
                    <div style="color: #64748b; font-size: 12px; margin-top: 6px;">Validade estimada do token: ~60 dias (renovável)</div>
                </div>
                <p style="color: #64748b; font-size: 14px;">Você já pode fechar esta aba e retornar ao chat.</p>
            </div>
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Erro Interno</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #f87171; text-align: center; padding: 60px;">
            <h2>❌ Erro interno ao processar autenticação Meta: {e}</h2>
            <br>
            <a href="{url_reautorizar}" style="background: #1877f2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Tentar Novamente</a>
        </body>
        </html>
        """

