#!/usr/bin/env bash
# =============================================================
#  KOTHAR v4.0 — Daemon de Inicialização
#  Engenheiro Kothar | Ugarit Digital
# =============================================================
#  Inicia a API do Kothar como daemon em background.
#  Usado pelo `kothar start` quando Docker não está disponível.
# =============================================================

set -euo pipefail

KOTHAR_DIR="${HOME}/kothar"
PID_FILE="${KOTHAR_DIR}/.kothar_api.pid"
LOG_FILE="${KOTHAR_DIR}/.kothar_api.log"
VENV="${KOTHAR_DIR}/.venv"

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

start_api() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if kill -0 "${PID}" 2>/dev/null; then
            echo -e "${CYAN}[INFO]${RESET} API já rodando (PID ${PID})"
            return 0
        fi
    fi

    # Ativa virtualenv se existir
    if [ -f "${VENV}/bin/activate" ]; then
        # shellcheck disable=SC1090
        source "${VENV}/bin/activate"
    fi

    cd "${KOTHAR_DIR}"
    nohup python3 -m uvicorn backend.api.main:app \
        --host 0.0.0.0 --port 8080 \
        --log-level info \
        >> "${LOG_FILE}" 2>&1 &

    echo $! > "${PID_FILE}"
    sleep 1

    if kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
        echo -e "${GREEN}✅ API iniciada${RESET} (PID $(cat "${PID_FILE}")) — http://localhost:8080"
    else
        echo -e "${RED}❌ Falha ao iniciar API. Ver logs: ${LOG_FILE}${RESET}"
        exit 1
    fi
}

stop_api() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        kill "${PID}" 2>/dev/null && echo -e "${GREEN}✅ API parada${RESET}" || true
        rm -f "${PID_FILE}"
    else
        echo "API não está rodando."
    fi
}

status_api() {
    if [ -f "${PID_FILE}" ] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
        echo -e "${GREEN}● API rodando${RESET} (PID $(cat "${PID_FILE}"))"
    else
        echo "○ API parada"
    fi
}

case "${1:-start}" in
    start)  start_api  ;;
    stop)   stop_api   ;;
    restart) stop_api; sleep 1; start_api ;;
    status) status_api ;;
    *) echo "Uso: $0 {start|stop|restart|status}" ;;
esac
