#!/usr/bin/env python3
"""
KOTHAR WATCHDOG API - API de Controle Seguro
Recebe comandos via HTTP e executa ações no watchdog
"""

import os
import sys
import json
import hashlib
import hmac
from pathlib import Path
from flask import Flask, request, jsonify

# Carregar .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

# Importar watchdog
sys.path.insert(0, str(Path(__file__).parent))
from kothar_watchdog import KotharWatchdog, SystemMonitor, ProcessManager

app = Flask(__name__)

# Config
API_SECRET = os.environ.get("WATCHDOG_API_SECRET", "change-me-in-production")
PORT = int(os.environ.get("WATCHDOG_API_PORT", 5555))

# Instâncias
watchdog = KotharWatchdog()
monitor = SystemMonitor()
process_manager = ProcessManager(monitor)

# ═══════════════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def verify_signature(data: str, signature: str) -> bool:
    """Verifica assinatura HMAC"""
    expected = hmac.new(
        API_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.before_request
def authenticate():
    """Autenticação simples por header"""
    # Skip health check
    if request.path == '/health':
        return None

    # Verificar API key
    api_key = request.headers.get('X-API-Key', '')

    if not api_key:
        return jsonify({"error": "API key required"}), 401

    # Verificar HMAC
    expected = hashlib.sha256((api_key + API_SECRET).encode()).hexdigest()
    if not verify_signature(request.path, request.headers.get('X-Signature', '')):
        return jsonify({"error": "Invalid signature"}), 403

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "kothar-watchdog-api"})

@app.route('/status', methods=['GET'])
def get_status():
    """Retorna status atual do sistema"""
    status = monitor.get_status()
    return jsonify({
        "cpu_percent": status.cpu_percent,
        "memory_percent": status.memory_percent,
        "memory_available_gb": status.memory_available_gb,
        "disk_percent": status.disk_percent,
        "processes_count": status.processes_count,
        "warnings": status.warnings,
        "criticals": status.criticals,
        "top_cpu": status.top_cpu_processes,
        "top_memory": status.top_memory_processes,
        "timestamp": status.timestamp
    })

@app.route('/processes', methods=['GET'])
def list_processes():
    """Lista processos ordenados"""
    cpu = request.args.get('sort', 'cpu')  # cpu ou memory

    status = monitor.get_status()
    processes = status.top_cpu_processes if cpu == 'cpu' else status.top_memory_processes

    # Adicionar info de prioridade
    for p in processes:
        p['is_priority'] = monitor.is_priority_process(p['name'])

    return jsonify({"processes": processes, "sort": cpu})

@app.route('/process/<int:pid>/kill', methods=['POST'])
def kill_process(pid):
    """Encerra um processo"""
    reason = request.json.get('reason', 'Solicitado via API') if request.json else 'Solicitado via API'

    success = process_manager.kill_process(pid, reason)

    return jsonify({
        "success": success,
        "pid": pid,
        "reason": reason
    })

@app.route('/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """Limpa cache do sistema"""
    results = process_manager.cleanup_cache()
    return jsonify({
        "success": True,
        "cleared": results['cleared'],
        "failed": results['failed']
    })

@app.route('/watchdog/start', methods=['POST'])
def start_watchdog():
    """Inicia o watchdog em background"""
    import threading

    if watchdog.running:
        return jsonify({"status": "already_running"})

    thread = threading.Thread(target=watchdog.run)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started"})

@app.route('/watchdog/stop', methods=['POST'])
def stop_watchdog():
    """Para o watchdog"""
    watchdog.stop()
    return jsonify({"status": "stopped"})

@app.route('/watchdog/status', methods=['GET'])
def watchdog_status():
    """Status do watchdog"""
    return jsonify({
        "running": watchdog.running,
        "pid": os.getpid()
    })

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🐕 KOTHAR WATCHDOG API                                    ║
║  Servidor de controle do watchdog                           ║
║  Porta: {PORT}                                              ║
║  🔐 Autenticação: X-API-Key + X-Signature                  ║
╚══════════════════════════════════════════════════════════════╝
""")

    app.run(
        host='127.0.0.1',
        port=PORT,
        debug=False,
        threaded=True
    )
