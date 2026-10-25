"""
=============================================================
 KOTHAR v4.0 — Router de Autenticação OAuth2 Google
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

router = APIRouter(prefix="/auth/google", tags=["Google-Auth"])

DIRETORIO_BACKEND = Path(__file__).resolve().parent.parent.parent
CAMINHO_TOKENS = DIRETORIO_BACKEND / ".google-tokens"
ARQUIVO_SESSAO = CAMINHO_TOKENS / "sessao_google.json"

def carregar_credenciais_env():
    # Tenta ler do .env na raiz
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
                if vars_env.get("GOOGLE_CLIENT_ID"):
                    break
            except Exception:
                pass
    return vars_env

@router.get("/callback", response_class=HTMLResponse)
async def callback_oauth_google(
    code: str = Query(None),
    error: str = Query(None)
):
    env = carregar_credenciais_env()
    client_id = env.get("GOOGLE_CLIENT_ID", "")
    client_secret = env.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = env.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback")
    
    # URL para reautenticar caso o código tenha expirado
    escopos = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ]
    params_novo = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(escopos),
        "access_type": "offline",
        "prompt": "consent"
    }
    url_reautorizar = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params_novo)

    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Erro de Autenticação</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #f87171; text-align: center; padding: 60px;">
            <h1 style="color: #ef4444;">❌ Erro na Autorização Google</h1>
            <p style="color: #cbd5e1; font-size: 16px;">O Google retornou o erro: <b>{error}</b></p>
            <br>
            <a href="{url_reautorizar}" style="background: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Tentar Novamente</a>
        </body>
        </html>
        """

    if not code:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Kothar — Código Ausente</title></head>
        <body style="font-family: monospace; background: #0b0f19; color: #e2e8f0; text-align: center; padding: 60px;">
            <h1 style="color: #38bdf8;">🎵 KOTHAR v4.0 — Autenticação Google</h1>
            <p style="color: #94a3b8; font-size: 16px;">Nenhum código foi enviado na URL.</p>
            <br>
            <a href="{url_reautorizar}" style="background: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Fazer Login com Google</a>
        </body>
        </html>
        """

    # Trocar código por token
    url_oauth_endpoint = "https://oauth2.googleapis.com/token"
    dados = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        r = requests.post(url_oauth_endpoint, data=dados, timeout=15)
        if r.status_code == 200:
            resp_json = r.json()
            refresh_token = resp_json.get("refresh_token")
            access_token = resp_json.get("access_token")
            
            # Buscar e-mail da conta
            email_conta = "Conta Conectada"
            if access_token:
                try:
                    r_perfil = requests.get(
                        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10
                    )
                    if r_perfil.status_code == 200:
                        email_conta = r_perfil.json().get("emailAddress", email_conta)
                except Exception:
                    pass

            # Salvar em .google-tokens
            CAMINHO_TOKENS.mkdir(parents=True, exist_ok=True)
            with open(ARQUIVO_SESSAO, "w", encoding="utf-8") as f:
                json.dump(resp_json, f, indent=2)
            try:
                os.chmod(ARQUIVO_SESSAO, 0o600)
            except Exception:
                pass
                
            # Salvar no .env do projeto no host se acessível
            caminho_env_host = DIRETORIO_BACKEND / ".env"
            if caminho_env_host.exists() and os.access(caminho_env_host, os.W_OK):
                try:
                    linhas = []
                    with open(caminho_env_host, "r", encoding="utf-8") as f:
                        linhas = f.readlines()
                    novas = []
                    rt_ok = False
                    email_ok = False
                    for l in linhas:
                        if l.startswith("GOOGLE_REFRESH_TOKEN=") and refresh_token:
                            novas.append(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")
                            rt_ok = True
                        elif l.startswith("GOOGLE_ACCOUNT_EMAIL=") and email_conta:
                            novas.append(f"GOOGLE_ACCOUNT_EMAIL={email_conta}\n")
                            email_ok = True
                        else:
                            novas.append(l)
                    if not rt_ok and refresh_token:
                        novas.append(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")
                    if not email_ok and email_conta:
                        novas.append(f"GOOGLE_ACCOUNT_EMAIL={email_conta}\n")
                    with open(caminho_env_host, "w", encoding="utf-8") as f:
                        f.writelines(novas)
                except Exception:
                    pass

            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Kothar — Sessão Google Conectada</title></head>
            <body style="font-family: monospace; background: #0b0f19; color: #38bdf8; text-align: center; padding: 60px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <h1 style="color: #4ade80; margin-bottom: 10px;">✅ Sessão Conectada com Sucesso!</h1>
                    <h3 style="color: #f8fafc; margin-top: 0;">Kothar v4.0 — Ugarit Digital</h3>
                    <p style="color: #94a3b8; font-size: 15px; line-height: 1.6;">
                        Conta vinculada: <b style="color: #38bdf8;">{email_conta}</b><br>
                        O <b>Refresh Token</b> perpétuo foi capturado e persistido com segurança.
                    </p>
                    <div style="background: #0f172a; padding: 15px; border-radius: 8px; margin: 25px 0; border: 1px solid #1e293b;">
                        <span style="color: #a7f3d0; font-size: 14px;">🔒 Status da Sessão: <b>ATIVA E PERSISTENTE</b></span><br>
                        <span style="color: #64748b; font-size: 12px;">Permissões: Gmail (Leitura/Modificação) + Google Calendar</span>
                    </div>
                    <p style="color: #64748b; font-size: 14px;">Você já pode fechar esta aba e retornar ao chat.</p>
                </div>
            </body>
            </html>
            """
        else:
            erro_detalhe = r.text
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Kothar — Código Expirado</title></head>
            <body style="font-family: monospace; background: #0b0f19; color: #f8fafc; text-align: center; padding: 60px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: #fbbf24;">⚠️ O código de autorização expirou ou já foi utilizado</h2>
                    <p style="color: #94a3b8; font-size: 14px;">Os códigos do Google são de uso único e duram menos de 2 minutos. Basta gerar um novo código com um clique abaixo:</p>
                    <br>
                    <a href="{url_reautorizar}" style="background: #2563eb; color: #fff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block;">
                        👉 Gerar Nova Autorização (1 Clique)
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
            <h2>❌ Falha na conexão: {e}</h2>
            <br>
            <a href="{url_reautorizar}" style="background: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Tentar Novamente</a>
        </body>
        </html>
        """
