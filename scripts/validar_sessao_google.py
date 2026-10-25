#!/usr/bin/env python3
"""
Validador de Sessão e Persistência Google (OAuth2) - Kothar v4.0
Ugarit Digital — Bruno Harkin

Garante a autorização inicial, captura do Refresh Token perpétuo
e validação de renovação autônoma de sessão para Gmail e Google Calendar.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

try:
    import requests
except ImportError:
    print("❌ Pacote 'requests' não encontrado. Execute: pip install requests")
    sys.exit(1)

DIRETORIO_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMINHO_ENV = os.path.join(DIRETORIO_RAIZ, ".env")
DIRETORIO_TOKENS = os.path.join(DIRETORIO_RAIZ, ".google-tokens")
ARQUIVO_SESSAO = os.path.join(DIRETORIO_TOKENS, "sessao_google.json")

ESCOPOS = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

def carregar_env():
    valores = {}
    if os.path.exists(CAMINHO_ENV):
        with open(CAMINHO_ENV, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#") and "=" in linha:
                    chave, valor = linha.split("=", 1)
                    valores[chave.strip()] = valor.strip()
    return valores

def atualizar_env(chave, novo_valor):
    if not os.path.exists(CAMINHO_ENV):
        return
    linhas = []
    encontrado = False
    with open(CAMINHO_ENV, "r", encoding="utf-8") as f:
        linhas = f.readlines()
    
    novas_linhas = []
    for linha in linhas:
        if linha.strip().startswith(f"{chave}="):
            novas_linhas.append(f"{chave}={novo_valor}\n")
            encontrado = True
        else:
            novas_linhas.append(linha)
            
    if not encontrado:
        novas_linhas.append(f"{chave}={novo_valor}\n")
        
    with open(CAMINHO_ENV, "w", encoding="utf-8") as f:
        f.writelines(novas_linhas)

codigo_autorizacao = None
servidor_http = None

class ManipuladorCallbackOAuth(BaseHTTPRequestHandler):
    def do_GET(self):
        global codigo_autorizacao
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        if "code" in params:
            codigo_autorizacao = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: monospace; background: #0f172a; color: #38bdf8; text-align: center; padding: 50px;">
                <h2>✅ Kothar — Autorização Concluída com Sucesso!</h2>
                <p style="color: #94a3b8;">O código OAuth2 foi capturado e o Refresh Token está sendo persistido.</p>
                <p>Você pode fechar esta aba e retornar ao terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            erro = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h3>❌ Erro na autorização: {erro}</h3>".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def testar_renovacao_e_acesso(client_id, client_secret, refresh_token):
    print("\n🔍 Testando recuperação autônoma de sessão com Refresh Token...")
    endpoint_oauth = "https://oauth2.googleapis.com/token"
    dados = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    resp = requests.post(endpoint_oauth, data=dados, timeout=10)
    if resp.status_code != 200:
        print(f"❌ Falha ao renovar access token: {resp.status_code} — {resp.text}")
        return False
        
    token_info = resp.json()
    access_token = token_info.get("access_token")
    print("✅ Renovação autônoma de sessão validada! Access Token gerado com sucesso.")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Testar Perfil Gmail
    resp_gmail = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/profile", headers=headers, timeout=10)
    if resp_gmail.status_code == 200:
        perfil = resp_gmail.json()
        email_usuario = perfil.get("emailAddress", "desconhecido")
        total_mensagens = perfil.get("messagesTotal", 0)
        print(f"✅ Gmail API conectada! Conta: {email_usuario} ({total_mensagens} mensagens no total)")
        atualizar_env("GOOGLE_ACCOUNT_EMAIL", email_usuario)
    else:
        print(f"⚠️ Aviso no Gmail API: {resp_gmail.status_code} — {resp_gmail.text}")

    # 2. Testar Google Calendar
    resp_cal = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList", headers=headers, timeout=10)
    if resp_cal.status_code == 200:
        calendarios = resp_cal.json().get("items", [])
        print(f"✅ Google Calendar API conectada! ({len(calendarios)} calendário(s) localizados)")
    else:
        print(f"⚠️ Aviso no Calendar API: {resp_cal.status_code} — {resp_cal.text}")

    return True

def principal():
    global codigo_autorizacao, servidor_http
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🔐 KOTHAR v4.0 — VALIDAÇÃO E PERSISTÊNCIA DE SESSÃO GOOGLE")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    env_vars = carregar_env()
    client_id = env_vars.get("GOOGLE_CLIENT_ID")
    client_secret = env_vars.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = env_vars.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback")
    refresh_token = env_vars.get("GOOGLE_REFRESH_TOKEN")
    
    if not client_id or not client_secret:
        print("❌ Erro: GOOGLE_CLIENT_ID ou GOOGLE_CLIENT_SECRET não configurados no .env")
        sys.exit(1)
        
    os.makedirs(DIRETORIO_TOKENS, exist_ok=True)
    
    # Se já existir refresh token, testa a renovação imediatamente
    if refresh_token:
        print(f"📌 Refresh Token existente localizado no .env.")
        if testar_renovacao_e_acesso(client_id, client_secret, refresh_token):
            print("\n🎉 SESSÃO PERSISTENTE 100% FUNCIONAL! O Kothar pode operar sem reautenticação contínua.")
            return

    # Iniciar fluxo OAuth2
    params_oauth = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(ESCOPOS),
        "access_type": "offline",
        "prompt": "consent"
    }
    url_autorizacao = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params_oauth)
    
    print("👉 Passo 1: Abra a URL abaixo no seu navegador para autorizar o acesso:")
    print("─────────────────────────────────────────────────────────────")
    print(url_autorizacao)
    print("─────────────────────────────────────────────────────────────\n")
    
    parsed_redirect = urllib.parse.urlparse(redirect_uri)
    porta = parsed_redirect.port or 8080
    
    try:
        servidor_http = HTTPServer(("0.0.0.0", porta), ManipuladorCallbackOAuth)
    except Exception as e:
        print(f"⚠️ Não foi possível abrir servidor na porta {porta}: {e}")
        servidor_http = None

    if servidor_http:
        print(f"⏳ Aguardando callback automático em {redirect_uri} (limite de 120s)...")
        thread = threading.Thread(target=servidor_http.handle_request)
        thread.daemon = True
        thread.start()
        thread.join(timeout=120)
        servidor_http.server_close()

    # Verificar se foi passado via argumento de linha de comando
    if len(sys.argv) > 1 and sys.argv[1].strip():
        entrada_cli = sys.argv[1].strip()
        if "code=" in entrada_cli:
            parsed = urllib.parse.urlparse(entrada_cli)
            params = urllib.parse.parse_qs(parsed.query)
            codigo_autorizacao = params.get("code", [""])[0]
        else:
            codigo_autorizacao = entrada_cli
        print(f"📌 Código detectado via argumento.")

    if not codigo_autorizacao:
        print("\nComo o container da API Kothar já escuta na porta 8080, o navegador exibe `{'detail': 'Not Found'}`.")
        print("Basta copiar a URL completa da barra de endereços do navegador (ou o valor de 'code=') e colar abaixo:")
        try:
            entrada_usuario = input("\nCole aqui a URL completa ou o código: ").strip()
            if "code=" in entrada_usuario:
                parsed = urllib.parse.urlparse(entrada_usuario)
                params = urllib.parse.parse_qs(parsed.query)
                codigo_autorizacao = params.get("code", [""])[0]
            else:
                codigo_autorizacao = entrada_usuario
        except EOFError:
            codigo_autorizacao = ""

    if not codigo_autorizacao:
        print("\n❌ Nenhum código recebido. Fluxo cancelado.")
        sys.exit(1)

    print("\n🔄 Trocando código por tokens permanentes...")
    endpoint_oauth = "https://oauth2.googleapis.com/token"
    dados_troca = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": codigo_autorizacao,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    resp_troca = requests.post(endpoint_oauth, data=dados_troca, timeout=15)
    if resp_troca.status_code != 200:
        print(f"❌ Falha na troca do código: {resp_troca.status_code} — {resp_troca.text}")
        sys.exit(1)
        
    dados_sessao = resp_troca.json()
    refresh_token = dados_sessao.get("refresh_token")
    
    if not refresh_token:
        print("⚠️ Aviso: O Google não retornou um refresh_token (geralmente ocorre se a autorização já foi feita antes sem revogar).")
        print("Dica: Adicione prompt=consent ou revogue o app nas permissões da conta Google para gerar novo refresh_token.")
    else:
        atualizar_env("GOOGLE_REFRESH_TOKEN", refresh_token)
        print("💾 GOOGLE_REFRESH_TOKEN salvo no .env!")

    with open(ARQUIVO_SESSAO, "w", encoding="utf-8") as f:
        json.dump(dados_sessao, f, indent=2)
    os.chmod(ARQUIVO_SESSAO, 0o600)
    print(f"💾 Sessão salva com permissão 600 em: {ARQUIVO_SESSAO}")

    if refresh_token:
        testar_renovacao_e_acesso(client_id, client_secret, refresh_token)
        print("\n🎉 PERSISTÊNCIA COMPLETA! O Kothar agora recupera a sessão autonomamente em qualquer execução futura.")

if __name__ == "__main__":
    principal()
