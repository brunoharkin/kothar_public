# 🐕 Comandos Rápidos - Kothar Watchdog

## ⚡ START / STOP

### Iniciar Watchdog
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh start
```

### Parar Watchdog
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh stop
```

### Reiniciar
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh restart
```

---

## 📊 STATUS

### Ver se está rodando
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh status
```

### Ver log em tempo real
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh log
```

### Verificação única (sem rodar 24/7)
```bash
python3 /home/bruno/kothar/scripts/kothar-watchdog.py --once
```

---

## 🧹 LIMPEZA

### Limpar cache manualmente
```bash
python3 /home/bruno/kothar/scripts/kothar-watchdog.py --cleanup
```

### Ver último status
```bash
cat ~/.kothar/watchdog_status.json | python3 -m json.tool
```

---

## ⚙️ INSTALAÇÃO

### Instalar como serviço (inicia com PC)
```bash
bash /home/bruno/kothar/scripts/kothar-watchdog.sh install
```

### Ativar inicialização automática
```bash
systemctl --user enable kothar-watchdog
systemctl --user start kothar-watchdog
```

---

## 🔧 CONFIGURAÇÃO

### Ajustar thresholds no .env
```bash
nano /home/bruno/kothar/.env
```

Parâmetros importantes:
- `WATCHDOG_CPU_CRITICAL=95`
- `WATCHDOG_MEMORY_CRITICAL=92`
- `WATCHDOG_AUTO_CLEANUP=true`
- `WATCHDOG_AUTO_KILL=false` (⚠️ CUIDADO!)

---

## 📁 ARQUIVOS

| Arquivo | Descrição |
|---------|-----------|
| Script principal | `/home/bruno/kothar/scripts/kothar-watchdog.py` |
| Inicializador | `/home/bruno/kothar/scripts/kothar-watchdog.sh` |
| PID | `~/.kothar/watchdog.pid` |
| Log | `~/.kothar/logs/watchdog.log` |
| Status | `~/.kothar/watchdog_status.json` |

---

## 🚨 ALERTAS

O watchdog vai te notificar quando:
- CPU > 80% (aviso) / > 95% (crítico)
- Memória > 80% (aviso) / > 92% (crítico)
- Disco > 85%
- Processo pesado detectado

Configure Telegram em `.env` para receber alertas:
```bash
WATCHDOG_BOT_TOKEN=seu_token
WATCHDOG_CHAT_ID=seu_chat_id
```
