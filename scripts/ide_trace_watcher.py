#!/usr/bin/env python3
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

LOG_FILE = "/home/bruno/.gemini/antigravity/brain/bb03846e-471c-4649-ab61-ed09b2979218/.system_generated/logs/overview.txt"
API_BASE = "http://localhost:8080"

def get_token():
    req = urllib.request.Request(f"{API_BASE}/api/auth/login", data=json.dumps({"identifier": "ide_maestro"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["token"]
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def get_or_create_session(token):
    req = urllib.request.Request(f"{API_BASE}/api/session", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            sessions = json.loads(resp.read())
            for s in sessions:
                if s.get("name") == "Sessão IDE ao Vivo":
                    return s["id"]
    except:
        pass
    
    req = urllib.request.Request(f"{API_BASE}/api/session", data=json.dumps({"name": "Sessão IDE ao Vivo", "agent": "kothar", "sub_agent": "ide"}).encode(), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["id"]
    except Exception as e:
        print(f"Session error: {e}")
        return None

def send_trace(token, session_id, event_type, input_data, output_data):
    payload = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": event_type,
        "status": "success",
        "input": input_data,
        "output": output_data
    }
    req = urllib.request.Request(f"{API_BASE}/api/trace", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Trace error: {e}")

def main():
    if not os.path.exists(LOG_FILE):
        return
        
    token = get_token()
    if not token: return
    session_id = get_or_create_session(token)
    if not session_id: return

    # Começa a ler as últimas linhas e fica em tail
    p = subprocess.Popen(["tail", "-n", "0", "-f", LOG_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    for line in iter(p.stdout.readline, ''):
        try:
            data = json.loads(line)
        except:
            continue
            
        source = data.get("source")
        content = data.get("content", "")
        tool_calls = data.get("tool_calls", [])
        
        if source == "USER_EXPLICIT":
            # Extrair apenas a pergunta sem a tag
            clean_content = content
            if "<USER_REQUEST>" in content:
                clean_content = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            send_trace(token, session_id, "user_message", {"msg": clean_content}, {})
        elif source == "MODEL":
            if content:
                send_trace(token, session_id, "llm_response", {"msg": "Resposta do Maestro"}, {"result": content})
            if tool_calls:
                for tc in tool_calls:
                    send_trace(token, session_id, tc.get("name", "tool"), tc.get("args", {}), {})

if __name__ == "__main__":
    main()
