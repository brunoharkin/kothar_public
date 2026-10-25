#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR WATCHDOG - Script de Inicialização
# Inicia o watchdog junto com o sistema ou manualmente
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTHAR_DIR="$(dirname "$SCRIPT_DIR")"
WATCHDOG_PID="$HOME/.kothar/watchdog.pid"
LOG_FILE="$HOME/.kothar/logs/watchdog.log"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Verificar se já está rodando
is_running() {
    if [ -f "$WATCHDOG_PID" ]; then
        PID=$(cat "$WATCHDOG_PID")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start() {
    if is_running; then
        log "${YELLOW}Watchdog já está rodando (PID: $(cat $WATCHDOG_PID))${NC}"
        return 1
    fi

    log "${GREEN}Iniciando Kothar Watchdog...${NC}"

    # Criar diretórios
    mkdir -p "$(dirname "$WATCHDOG_PID")"
    mkdir -p "$(dirname "$LOG_FILE")"

    # Carregar .env
    source "$KOTHAR_DIR/.env" 2>/dev/null

    # Iniciar em background
    cd "$KOTHAR_DIR"
    nohup python3 "$SCRIPT_DIR/kothar-watchdog.py" > "$LOG_FILE" 2>&1 &
    PID=$!

    echo "$PID" > "$WATCHDOG_PID"

    sleep 2

    if is_running; then
        log "${GREEN}✅ Watchdog iniciado com sucesso (PID: $PID)${NC}"
        log "📄 Log: $LOG_FILE"
    else
        log "${RED}❌ Falha ao iniciar watchdog${NC}"
        return 1
    fi
}

stop() {
    if ! is_running; then
        log "${YELLOW}Watchdog não está rodando${NC}"
        return 1
    fi

    PID=$(cat "$WATCHDOG_PID")
    log "${YELLOW}Encerrando watchdog (PID: $PID)...${NC}"

    kill "$PID" 2>/dev/null
    sleep 2

    if ! is_running; then
        rm -f "$WATCHDOG_PID"
        log "${GREEN}✅ Watchdog encerrado${NC}"
    else
        log "${RED}Forçando encerramento...${NC}"
        kill -9 "$PID" 2>/dev/null
        rm -f "$WATCHDOG_PID"
    fi
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if is_running; then
        PID=$(cat "$WATCHDOG_PID")
        log "${GREEN}🟢 Watchdog ATIVO (PID: $PID)${NC}"
        echo ""
        echo "Últimas linhas do log:"
        tail -5 "$LOG_FILE" 2>/dev/null || echo "Log não disponível"
    else
        log "${RED}🔴 Watchdog INATIVO${NC}"
    fi
}

log_cmd() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log "${YELLOW}Log não encontrado: $LOG_FILE${NC}"
    fi
}

# Instalar como serviço systemd (para Ubuntu/Debian)
install_systemd() {
    SERVICE_FILE="$HOME/.config/systemd/user/kothar-watchdog.service"

    mkdir -p "$(dirname "$SERVICE_FILE")"

    cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Kothar Watchdog - Monitor de Sistema 24/7
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/kothar
ExecStart=%h/.venv/bin/python %h/kothar/scripts/kothar-watchdog.py
Restart=always
RestartSec=10
StandardOutput=append:%h/.kothar/logs/watchdog.log
StandardError=append:%h/.kothar/logs/watchdog.log

[Install]
WantedBy=default.target
EOF

    log "${GREEN}✅ Serviço systemd criado em: $SERVICE_FILE${NC}"
    log "Para ativar: systemctl --user enable kothar-watchdog"
    log "Para iniciar: systemctl --user start kothar-watchdog"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    log)
        log_cmd
        ;;
    install)
        install_systemd
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|log|install}"
        echo ""
        echo "  start   - Inicia o watchdog"
        echo "  stop    - Encerra o watchdog"
        echo "  restart - Reinicia o watchdog"
        echo "  status  - Mostra status atual"
        echo "  log     - Mostra log em tempo real"
        echo "  install - Cria serviço systemd"
        exit 1
        ;;
esac
