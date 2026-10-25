"""
=============================================================
 KOTHAR v4.0 — Gerenciador de E-mails (Gmail API)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import os
import json
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent.parent.parent
ARQUIVO_ENV = DIRETORIO_RAIZ / ".env"
ARQUIVO_REMETENTES_BLOQUEADOS = DIRETORIO_RAIZ / "backend" / ".google-tokens" / "remetentes_bloqueados.json"

def obter_credenciais():
    vars_env = {}
    if ARQUIVO_ENV.exists():
        with open(ARQUIVO_ENV, "r", encoding="utf-8") as f:
            for l in f:
                l = l.strip()
                if l and not l.startswith("#") and "=" in l:
                    k, v = l.split("=", 1)
                    vars_env[k.strip()] = v.strip()
    return vars_env

def obter_access_token():
    credenciais = obter_credenciais()
    client_id = credenciais.get("GOOGLE_CLIENT_ID")
    client_secret = credenciais.get("GOOGLE_CLIENT_SECRET")
    refresh_token = credenciais.get("GOOGLE_REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Credenciais Google incompletas no .env")

    url_oauth = "https://oauth2.googleapis.com/token"
    dados = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    resp = requests.post(url_oauth, data=dados, timeout=12)
    if resp.status_code != 200:
        raise RuntimeError(f"Falha ao renovar token Google: {resp.status_code} — {resp.text}")
        
    return resp.json().get("access_token")

def obter_estatisticas_caixa(access_token=None):
    token = access_token or obter_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    perfil = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/profile", headers=headers, timeout=10).json()
    inbox = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/labels/INBOX", headers=headers, timeout=10).json()
    spam = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/labels/SPAM", headers=headers, timeout=10).json()
    trash = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/labels/TRASH", headers=headers, timeout=10).json()
    
    return {
        "conta": perfil.get("emailAddress"),
        "total_geral": perfil.get("messagesTotal", 0),
        "inbox_total": inbox.get("messagesTotal", 0),
        "inbox_nao_lidos": inbox.get("messagesUnread", 0),
        "spam_total": spam.get("messagesTotal", 0),
        "spam_nao_lidos": spam.get("messagesUnread", 0),
        "trash_total": trash.get("messagesTotal", 0)
    }

def resumir_mensagens_recentes(limite=15, apenas_nao_lidos=True, access_token=None):
    token = access_token or obter_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    query = "in:inbox is:unread" if apenas_nao_lidos else "in:inbox"
    url_lista = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults={limite}"
    
    resp = requests.get(url_lista, headers=headers, timeout=12)
    if resp.status_code != 200:
        return []
        
    mensagens_raw = resp.json().get("messages", [])
    if not mensagens_raw:
        return []
        
    def buscar_detalhe_compacto(mid):
        u = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"
        r = requests.get(u, headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        headers_dict = {h["name"].lower(): h["value"] for h in d.get("payload", {}).get("headers", [])}
        labels = d.get("labelIds", [])
        return {
            "id": d.get("id"),
            "remetente": headers_dict.get("from", "Desconhecido"),
            "assunto": headers_dict.get("subject", "(Sem assunto)"),
            "data": headers_dict.get("date", ""),
            "trecho": d.get("snippet", "")[:120],
            "nao_lido": "UNREAD" in labels
        }

    resultados = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futuros = [ex.submit(buscar_detalhe_compacto, m["id"]) for m in mensagens_raw]
        for f in as_completed(futuros):
            res = f.result()
            if res:
                resultados.append(res)
                
    return resultados

def inspecionar_mensagem(mensagem_id, access_token=None):
    token = access_token or obter_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mensagem_id}?format=full"
    
    resp = requests.get(url, headers=headers, timeout=12)
    if resp.status_code != 200:
        return {"erro": f"Mensagem não encontrada: {resp.status_code}"}
        
    dados = resp.json()
    headers_dict = {h["name"].lower(): h["value"] for h in dados.get("payload", {}).get("headers", [])}
    
    # Extrair snippet sanitizado (defesa contra prompt injection)
    snippet = dados.get("snippet", "")
    snippet_limpo = re.sub(r"[<>{}\[\]\n\r]+", " ", snippet).strip()[:500]
    
    return {
        "id": dados.get("id"),
        "remetente": headers_dict.get("from", "Desconhecido"),
        "destinatario": headers_dict.get("to", ""),
        "assunto": headers_dict.get("subject", "(Sem assunto)"),
        "data": headers_dict.get("date", ""),
        "resumo_seguro": snippet_limpo
    }

def listar_ids_por_busca(query="in:inbox", access_token=None):
    token = access_token or obter_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    ids_encontrados = []
    page_token = None
    
    while True:
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults=500"
        if page_token:
            url += f"&pageToken={page_token}"
            
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            break
            
        dados = r.json()
        mensagens = dados.get("messages", [])
        for m in mensagens:
            ids_encontrados.append(m["id"])
            
        page_token = dados.get("nextPageToken")
        if not page_token:
            break
            
    return ids_encontrados

def _enviar_para_lixeira_individual(msg_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash"
    for tentativa in range(3):
        try:
            r = requests.post(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return True
            if r.status_code == 429:
                time.sleep(1.0 * (tentativa + 1))
        except Exception:
            time.sleep(0.5)
    return False

def mover_para_lixeira_em_lote(ids_mensagens, access_token=None, callback_progresso=None):
    token = access_token or obter_access_token()
    total = len(ids_mensagens)
    concluidos = 0
    sucessos = 0
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        futuros = {
            executor.submit(_enviar_para_lixeira_individual, mid, token): mid
            for mid in ids_mensagens
        }
        for futuro in as_completed(futuros):
            concluidos += 1
            if futuro.result():
                sucessos += 1
            if callback_progresso and (concluidos % 25 == 0 or concluidos == total):
                callback_progresso(concluidos, total, sucessos)
                
    return sucessos

def bloquear_e_descartar_remetente(remetente, access_token=None):
    token = access_token or obter_access_token()
    # 1. Localizar mensagens
    ids = listar_ids_por_busca(f"from:{remetente}", token)
    descartados = 0
    if ids:
        descartados = mover_para_lixeira_em_lote(ids, token)
        
    # 2. Registrar na lista negra local
    ARQUIVO_REMETENTES_BLOQUEADOS.parent.mkdir(parents=True, exist_ok=True)
    bloqueados = []
    if ARQUIVO_REMETENTES_BLOQUEADOS.exists():
        try:
            with open(ARQUIVO_REMETENTES_BLOQUEADOS, "r", encoding="utf-8") as f:
                bloqueados = json.load(f)
        except Exception:
            bloqueados = []
            
    if remetente not in bloqueados:
        bloqueados.append(remetente)
        with open(ARQUIVO_REMETENTES_BLOQUEADOS, "w", encoding="utf-8") as f:
            json.dump(bloqueados, f, indent=2)
            
    return {
        "remetente": remetente,
        "mensagens_descartadas": descartados,
        "status": "bloqueado_com_sucesso"
    }
