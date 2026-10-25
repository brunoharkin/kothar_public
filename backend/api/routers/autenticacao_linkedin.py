"""
=============================================================
 KOTHAR v4.0 — Router de Autenticação OAuth2 LinkedIn
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

router = APIRouter(prefix="/auth/linkedin", tags=["LinkedIn-Auth"])

DIRETORIO_BACKEND = Path(__file__).resolve().parent.parent.parent
CAMINHO_TOKENS = DIRETORIO_BACKEND / ".linkedin-tokens"
ARQUIVO_SESSAO = CAMINHO_TOKENS / "sessao_linkedin.json"

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
                if vars_env.get("LINKEDIN_CLIENT_ID"):
                    break
            except Exception:
                pass
    return vars_env

@router.get("/callback", response_class=HTMLResponse)
async def callback_oauth_linkedin(
    code: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None)
):
    env = carregar_credenciais_env()
    client_id = env.get("LINKEDIN_CLIENT_ID", "")
    client_secret = env.get("LINKEDIN_CLIENT_SECRET", "")
    redirect_uri = env.get("LINKEDIN_REDIRECT_URI", "http://localhost:8080/auth/linkedin/callback")
    
    # URL para reautenticar
    params_novo = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": "kothar_auth_state",
        "scope": "openid profile email w_member_social"
    }
    url_reautorizar = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params_novo)

    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Erro LinkedIn</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #f87171; text-align: center; padding: 60px;">
            <h1 style="color: #ef4444;">❌ Erro na Autorização do LinkedIn</h1>
            <p style="color: #cbd5e1; font-size: 16px;">Erro: <b>{error}</b></p>
            <p style="color: #94a3b8; font-size: 14px;">{error_description or ''}</p>
            <br>
            <a href="{url_reautorizar}" style="background: #0a66c2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Tentar Novamente</a>
        </body>
        </html>
        """

    if not code:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Conectar LinkedIn</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #e2e8f0; text-align: center; padding: 60px;">
            <h1 style="color: #0a66c2;">💼 KOTHAR v4.0 — Autenticação LinkedIn</h1>
            <p style="color: #94a3b8; font-size: 16px;">Clique abaixo para vincular sua conta do LinkedIn ao Kothar:</p>
            <br>
            <a href="{url_reautorizar}" style="background: #0a66c2; color: #fff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 15px; display: inline-block;">
                Fazer Login com LinkedIn
            </a>
        </body>
        </html>
        """

    # Trocar código por access token
    url_token_endpoint = "https://www.linkedin.com/oauth/v2/accessToken"
    dados_token = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers_req = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        r = requests.post(url_token_endpoint, data=dados_token, headers=headers_req, timeout=15)
        if r.status_code == 200:
            resp_json = r.json()
            access_token = resp_json.get("access_token")
            refresh_token = resp_json.get("refresh_token")
            
            nome_usuario = "Perfil LinkedIn"
            email_usuario = ""
            
            # Buscar dados do perfil via OpenID userinfo
            if access_token:
                try:
                    r_perfil = requests.get(
                        "https://api.linkedin.com/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10
                    )
                    if r_perfil.status_code == 200:
                        perfil_data = r_perfil.json()
                        nome_usuario = perfil_data.get("name", nome_usuario)
                        email_usuario = perfil_data.get("email", "")
                except Exception:
                    pass

            # Salvar em .linkedin-tokens
            CAMINHO_TOKENS.mkdir(parents=True, exist_ok=True)
            with open(ARQUIVO_SESSAO, "w", encoding="utf-8") as f:
                json.dump(resp_json, f, indent=2)
            try:
                os.chmod(ARQUIVO_SESSAO, 0o600)
            except Exception:
                pass
                
            # Atualizar .env no host se acessível
            caminho_env_host = DIRETORIO_BACKEND / ".env"
            if caminho_env_host.exists() and os.access(caminho_env_host, os.W_OK):
                try:
                    linhas = []
                    with open(caminho_env_host, "r", encoding="utf-8") as f:
                        linhas = f.readlines()
                    novas = []
                    for l in linhas:
                        if l.startswith("LINKEDIN_ACCESS_TOKEN=") and access_token:
                            novas.append(f"LINKEDIN_ACCESS_TOKEN={access_token}\n")
                        elif l.startswith("LINKEDIN_REFRESH_TOKEN=") and refresh_token:
                            novas.append(f"LINKEDIN_REFRESH_TOKEN={refresh_token}\n")
                        else:
                            novas.append(l)
                    with open(caminho_env_host, "w", encoding="utf-8") as f:
                        f.writelines(novas)
                except Exception:
                    pass

            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Kothar — LinkedIn Conectado</title></head>
            <body style="font-family: monospace; background: #0b0f19; color: #38bdf8; text-align: center; padding: 60px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <h1 style="color: #0a66c2; margin-bottom: 10px;">💼 LinkedIn Conectado com Sucesso!</h1>
                    <h3 style="color: #f8fafc; margin-top: 0;">Kothar v4.0 — Ugarit Digital</h3>
                    <p style="color: #94a3b8; font-size: 15px; line-height: 1.6;">
                        Perfil vinculado: <b style="color: #38bdf8;">{nome_usuario}</b><br>
                        {f'E-mail: <b style="color: #cbd5e1;">{email_usuario}</b><br>' if email_usuario else ''}
                        Token de API persistido com segurança no Kothar.
                    </p>
                    <div style="background: #0f172a; padding: 15px; border-radius: 8px; margin: 25px 0; border: 1px solid #1e293b;">
                        <span style="color: #a7f3d0; font-size: 14px;">🔒 Status da Conexão: <b>ATIVA</b></span><br>
                        <span style="color: #64748b; font-size: 12px;">Permissões: Perfil, Email e OpenID</span>
                    </div>
                    <p style="color: #64748b; font-size: 14px;">Você já pode fechar esta aba e retornar ao chat.</p>
                </div>
            </body>
            </html>
            """
        else:
            erro_txt = r.text
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Kothar — Falha no Token</title></head>
            <body style="font-family: monospace; background: #0b0f19; color: #f8fafc; text-align: center; padding: 60px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: #fbbf24;">⚠️ O código de autorização expirou ou é inválido</h2>
                    <p style="color: #94a3b8; font-size: 14px;">Resposta do LinkedIn: {erro_txt}</p>
                    <br>
                    <a href="{url_reautorizar}" style="background: #0a66c2; color: #fff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block;">
                        👉 Gerar Nova Autorização no LinkedIn
                    </a>
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
            <h2>❌ Falha na conexão com LinkedIn: {e}</h2>
            <br>
            <a href="{url_reautorizar}" style="background: #0a66c2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Tentar Novamente</a>
        </body>
        </html>
        """

