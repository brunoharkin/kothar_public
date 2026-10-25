#!/usr/bin/env python3
import os
import glob
import time
import json
import urllib.request
import urllib.error

BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
API_URL = "http://localhost:3000/api/trace/batch"

def post_traces(traces):
    if not traces:
        return
    data = json.dumps({"traces": traces}).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req)
    except Exception as e:
        print(f"Erro ao enviar traces: {e}")

def main():
    print(f"Monitorando logs do Gemini em {BRAIN_DIR}...")
    files_state = {}
    
    while True:
        try:
            pattern = os.path.join(BRAIN_DIR, "*", ".system_generated", "logs", "transcript.jsonl")
            current_files = glob.glob(pattern)
            
            for file_path in current_files:
                if file_path not in files_state:
                    # Lê do começo para carregar a sessão inteira
                    files_state[file_path] = 0
            
            for file_path in list(files_state.keys()):
                try:
                    if not os.path.exists(file_path):
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.seek(files_state[file_path])
                        lines = f.readlines()
                        files_state[file_path] = f.tell()
                        
                        if lines:
                            session_id = file_path.split("brain/")[1].split("/")[0]
                            traces_batch = []
                            
                            for line in lines:
                                if not line.strip():
                                    continue
                                try:
                                    data = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                    
                                source = data.get("source", "")
                                msg_type = data.get("type", "")
                                created_at = data.get("created_at", "")
                                content = data.get("content", "")
                                thinking = data.get("thinking", "")
                                tool_calls = data.get("tool_calls", [])
                                status = data.get("status", "success").lower()
                                
                                # USER
                                if source == "USER_EXPLICIT" and msg_type == "USER_INPUT":
                                    traces_batch.append({
                                        "session_id": session_id,
                                        "timestamp": created_at,
                                        "tool": "Chat:User",
                                        "input": content,
                                        "output": "",
                                        "status": "success",
                                        "agent_name": "gemini",
                                        "event_type": "user_message"
                                    })
                                
                                # MODEL
                                elif source == "MODEL" and msg_type == "PLANNER_RESPONSE":
                                    if thinking:
                                        traces_batch.append({
                                            "session_id": session_id,
                                            "timestamp": created_at,
                                            "tool": "Gemini:thinking",
                                            "input": thinking,
                                            "output": "",
                                            "status": "success",
                                            "agent_name": "gemini",
                                            "event_type": "thinking"
                                        })
                                    
                                    if content:
                                        traces_batch.append({
                                            "session_id": session_id,
                                            "timestamp": created_at,
                                            "tool": "Chat:Agent",
                                            "input": "",
                                            "output": content,
                                            "status": "success",
                                            "agent_name": "gemini",
                                            "event_type": "assistant_response"
                                        })
                                        
                                    for tc in tool_calls:
                                        t_name = tc.get("name", "tool")
                                        t_args = tc.get("arguments", {})
                                        traces_batch.append({
                                            "session_id": session_id,
                                            "timestamp": created_at,
                                            "tool": t_name,
                                            "input": json.dumps(t_args),
                                            "output": "(Execução iniciada pelo Gemini)",
                                            "status": "success",
                                            "agent_name": "gemini",
                                            "event_type": "tool_call"
                                        })
                                        
                                # SYSTEM TOOLS OR OTHERS
                                elif source == "SYSTEM" and content and isinstance(content, str):
                                    traces_batch.append({
                                        "session_id": session_id,
                                        "timestamp": created_at,
                                        "tool": "System:Info",
                                        "input": msg_type,
                                        "output": str(content)[:2000],
                                        "status": status,
                                        "agent_name": "system",
                                        "event_type": "system_info"
                                    })
                                    
                            post_traces(traces_batch)
                except Exception as e:
                    print(f"Error processando {file_path}: {e}")
        except Exception as e:
            pass
            
        time.sleep(2.0)

if __name__ == "__main__":
    main()
