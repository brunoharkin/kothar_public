"""
=============================================================
 KOTHAR v4.0 — Gerenciador de Agenda (Google Calendar API)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import datetime
from pathlib import Path
import requests

from backend.servicos.comunicacao_google.gerenciador_email import obter_access_token

def listar_proximos_eventos(dias_a_frente=2, max_eventos=10, access_token=None):
    token = access_token or obter_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    agora = datetime.datetime.now(datetime.timezone.utc)
    limite = agora + datetime.timedelta(days=dias_a_frente)
    
    time_min = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    time_max = limite.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = (
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
        f"?timeMin={time_min}&timeMax={time_max}&singleEvents=true"
        f"&orderBy=startTime&maxResults={max_eventos}"
    )
    
    resp = requests.get(url, headers=headers, timeout=12)
    if resp.status_code != 200:
        return {"erro": f"Falha ao consultar agenda: {resp.status_code}"}
        
    items = resp.json().get("items", [])
    eventos_compactos = []
    
    for item in items:
        inicio = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
        fim = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
        eventos_compactos.append({
            "id": item.get("id"),
            "titulo": item.get("summary", "(Sem título)"),
            "inicio": inicio,
            "fim": fim,
            "local": item.get("location", ""),
            "link": item.get("htmlLink", "")
        })
        
    return {
        "total_eventos": len(eventos_compactos),
        "periodo_dias": dias_a_frente,
        "eventos": eventos_compactos
    }
