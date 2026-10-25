#!/bin/bash
#=============================================================
# KOTHAR v4.0 - Script de Start Completo
# Uso: ./scripts/kothar_start.sh [start|stop|restart|status]
#=============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTHAR_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$KOTHAR_DIR/.venv"
API_PID_FILE="$KOTHAR_DIR/.kothar_api.pid"
LOG_FILE="$KOTHAR_DIR/.kothar_api.log"

cd "$KOTHAR_DIR"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[KOTHAR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[KOTHAR]${NC} $1"; }
log_error() { echo -e "${RED}[KOTHAR]${NC} $1"; }

start_containers() {
    log_info "Iniciando containers Docker..."
    docker-compose up -d postgres redis

    # Aguarda containers ficarem prontos
    log_info "Aguardando containers ficarem prontos..."
    sleep 5

    # Verifica
    if docker ps --format '{{.Names}}' | grep -q kothar_postgres; then
        log_info "✅ PostgreSQL rodando"
    else
        log_error "❌ PostgreSQL não está rodando"
    fi

    if docker ps --format '{{.Names}}' | grep -q kothar_redis; then
        log_info "✅ Redis rodando"
    else
        log_error "❌ Redis não está rodando"
    fi
}

stop_containers() {
    log_info "Parando containers..."
    docker-compose stop postgres redis 2>/dev/null || true
    log_info "✅ Containers parados"
}

start_api() {
    # Verifica virtualenv
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtualenv não encontrada em $VENV_DIR"
        exit 1
    fi

    # Ativa virtualenv
    source "$VENV_DIR/bin/activate"

    # Verifica se já está rodando
    if [ -f "$API_PID_FILE" ]; then
        PID=$(cat "$API_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_warn "API já está rodando (PID: $PID)"
            return 0
        else
            rm -f "$API_PID_FILE"
        fi
    fi

    # Executa migração primeiro
    log_info "Executando migração do banco..."
    python -m backend.migrations.add_flow_execution 2>/dev/null || log_warn "Migração já aplicada ou falhou"

    # Inicia API em background
    log_info "Iniciando API Kothar em background..."
    nohup python -m backend.api.main > "$LOG_FILE" 2>&1 &
    API_PID=$!
    echo $API_PID > "$API_PID_FILE"

    # Aguarda iniciar
    sleep 3

    if kill -0 "$API_PID" 2>/dev/null; then
        log_info "✅ API iniciada (PID: $API_PID)"
        log_info "   Logs: tail -f $LOG_FILE"
        log_info "   API: http://localhost:8080"
    else
        log_error "❌ Falha ao iniciar API"
        cat "$LOG_FILE"
        exit 1
    fi
}

stop_api() {
    if [ -f "$API_PID_FILE" ]; then
        PID=$(cat "$API_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$API_PID_FILE"
            log_info "✅ API parada"
        else
            rm -f "$API_PID_FILE"
            log_info "API não estava rodando"
        fi
    else
        log_info "API não está rodando"
    fi
}

status() {
    echo ""
    echo "=== CONTAINERS ==="
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker indisponível"

    echo ""
    echo "=== API STATUS ==="
    if [ -f "$API_PID_FILE" ]; then
        PID=$(cat "$API_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${GREEN}✅ API rodando${NC} (PID: $PID)"
            echo "   Logs: tail -f $LOG_FILE"
            echo "   API: http://localhost:8080"
        else
            echo -e "${YELLOW}⚠️  API marcada como rodando mas PID morto${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  API não está rodando${NC}"
    fi

    echo ""
    echo "=== CIRCUIT BREAKERS ==="
    curl -s http://localhost:8080/api/flow/circuit-breakers 2>/dev/null | python -m json.tool 2>/dev/null || echo "API indisponível"
}

case "${1:-start}" in
    start)
        start_containers
        start_api
        status
        ;;
    stop)
        stop_api
        stop_containers
        ;;
    restart)
        stop_api
        start_api
        ;;
    status)
        status
        ;;
    migrate)
        source "$VENV_DIR/bin/activate"
        python -m backend.migrations.add_flow_execution
        ;;
    test)
        source "$VENV_DIR/bin/activate"
        python -m backend.tests.test_harness
        ;;
    *)
        echo "Uso: $0 [start|stop|restart|status|migrate|test]"
        exit 1
        ;;
esac
