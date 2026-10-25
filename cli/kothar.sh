#!/usr/bin/env bash
# =============================================================
#  KOTHAR v4.0 — CLI Principal
#  Engenheiro Kothar | Ugarit Digital
# =============================================================
#  Uso: kothar [comando] [opções]
# =============================================================

set -euo pipefail

KOTHAR_DIR="${HOME}/kothar"
KOTHAR_VERSION="4.0.0"
API_URL="${KOTHAR_API_URL:-http://localhost:8080}"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# =============================================================
# Funções auxiliares
# =============================================================

log_info()    { echo -e "${CYAN}[INFO]${RESET} $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}   $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "${RED}[ERRO]${RESET}  $*" >&2; }

print_banner() {
    echo -e "${BOLD}"
    echo "  ██╗  ██╗ ██████╗ ████████╗██╗  ██╗ █████╗ ██████╗ "
    echo "  ██║ ██╔╝██╔═══██╗╚══██╔══╝██║  ██║██╔══██╗██╔══██╗"
    echo "  █████╔╝ ██║   ██║   ██║   ███████║███████║██████╔╝"
    echo "  ██╔═██╗ ██║   ██║   ██║   ██╔══██║██╔══██║██╔══██╗"
    echo "  ██║  ██╗╚██████╔╝   ██║   ██║  ██║██║  ██║██║  ██║"
    echo "  ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"
    echo -e "${RESET}"
    echo -e "  ${BOLD}🎵 Engenheiro Kothar v${KOTHAR_VERSION}${RESET} | Ugarit Digital"
    echo ""
}

check_docker() {
    if ! docker info &>/dev/null; then
        log_error "Docker não está rodando. Inicie o Docker e tente novamente."
        exit 1
    fi
}

api_get() {
    curl -sf "${API_URL}$1" 2>/dev/null || echo '{"error": "API offline"}'
}

# =============================================================
# Comandos
# =============================================================

cmd_help() {
    print_banner
    echo -e "${BOLD}USO:${RESET}"
    echo "  kothar [comando] [opções]"
    echo ""
    echo -e "${BOLD}STACK:${RESET}"
    echo -e "  ${GREEN}start${RESET}                 Inicia toda a stack Docker"
    echo -e "  ${GREEN}stop${RESET}                  Para a stack Docker"
    echo -e "  ${GREEN}restart${RESET}               Reinicia a stack"
    echo -e "  ${GREEN}status${RESET}                Status dos serviços e containers"
    echo -e "  ${GREEN}logs [serviço]${RESET}        Logs em tempo real de um container"
    echo ""
    echo -e "${BOLD}SESSÕES:${RESET}"
    echo -e "  ${GREEN}session create [nome]${RESET}  Cria nova sessão (nome = agent name)"
    echo -e "  ${GREEN}session current${RESET}        Mostra sessão atual deste terminal"
    echo -e "  ${GREEN}session list${RESET}          Lista todas as sessões"
    echo -e "  ${GREEN}session end${RESET}           Encerra sessão + gera relatório"
    echo -e "  ${GREEN}session resume [id]${RESET}    Retoma sessão existente"
    echo ""
    echo -e "${BOLD}OBSERVABILIDADE:${RESET}"
    echo -e "  ${GREEN}trace${RESET}                 Exibe traces recentes"
    echo -e "  ${GREEN}trace [session] -f${RESET}    Modo live (tail -f dos agentes)"
    echo -e "  ${GREEN}sessions${RESET}              Lista sessões ativas"
    echo ""
    echo -e "${BOLD}SETUP:${RESET}"
    echo -e "  ${GREEN}setup${RESET}                 Setup inicial (tabelas, coleções, skills)"
    echo -e "  ${GREEN}hooks${RESET}                 Instala hooks no Gemini CLI e Claude CLI"
    echo -e "  ${GREEN}version${RESET}               Versão do Kothar"
    echo ""
    echo -e "${BOLD}EXEMPLOS:${RESET}"
    echo "  kothar start"
    echo "  kothar setup"
    echo "  kothar hooks"
    echo "  kothar session create claude-code"
    echo "  kothar session create meu-bot"
    echo "  kothar session current"
    echo "  kothar trace -f                # live de todos os agentes"
    echo "  kothar trace abc123 -f         # live de uma sessão específica"
    echo "  kothar session end              # encerra + compila relatório"
    echo ""
}


cmd_start() {
    check_docker
    log_info "Iniciando stack Kothar v${KOTHAR_VERSION}..."

    # Verifica portas críticas
    for porta in 5440 6381 7474 7687 8000 8080 3030; do
        if lsof -i ":${porta}" &>/dev/null 2>&1; then
            log_warn "Porta ${porta} em uso. Verifique conflitos."
        fi
    done

    cd "${KOTHAR_DIR}"

    # Copia .env se não existir
    if [ ! -f .env ]; then
        cp .env.example .env
        log_warn ".env criado a partir do .env.example — edite as credenciais antes de usar em produção!"
    fi

    docker compose up -d --remove-orphans
    log_success "Stack iniciada! Acesse o dashboard em http://localhost:3030"
}

cmd_stop() {
    check_docker
    log_info "Parando stack Kothar..."
    cd "${KOTHAR_DIR}"
    docker compose down
    log_success "Stack parada."
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    check_docker
    print_banner

    echo -e "${BOLD}📦 CONTAINERS:${RESET}"
    docker ps --filter "name=kothar" \
        --format "  {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
        | column -t || log_warn "Nenhum container Kothar rodando."

    echo ""
    echo -e "${BOLD}🌐 API:${RESET}"
    local health
    health=$(api_get "/health/")
    echo "  ${health}" | python3 -m json.tool 2>/dev/null || echo "  Offline"

    echo ""
    echo -e "${BOLD}🗂️ PROJETOS GERENCIADOS:${RESET}"
    echo "  CRM Sophia     → ~/crm-Sophia    (portas: 2785, 5433, 6380)"
    echo "  ChronoDesk     → ~/chronodesk    (porta: 3000)"
    echo "  Orby.ia        → ~/Orby.ia       (portas: 5440, 6381)"
    echo "  Disparo Massa  → ~/disparo-em-massa (portas: 2786, 5432)"
    echo ""
}

cmd_logs() {
    check_docker
    local service="${1:-kothar_api}"
    docker logs -f --tail=100 "${service}"
}

cmd_setup() {
    log_info "Executando setup inicial do Kothar..."
    cd "${KOTHAR_DIR}"
    python3 scripts/setup.py
}

cmd_hooks() {
    log_info "Instalando hooks nos CLIs do Gemini e Claude..."
    bash "${KOTHAR_DIR}/hooks/install_hooks.sh"
}

cmd_trace_live() {
    local session="${1:-}"
    local follow="${2:-}"
    local args=""
    
    if [ "${session}" = "-f" ] || [ "${session}" = "--follow" ]; then
        follow="${session}"
        session=""
    fi
    
    [ -n "${session}" ] && args="--session ${session}"
    [ "${follow}" = "-f" ] || [ "${follow}" = "--follow" ] && args="${args} --follow"
    python3 "${KOTHAR_DIR}/scripts/trace_live.py" ${args}
}

cmd_sessions() {
    python3 "${KOTHAR_DIR}/scripts/trace_live.py" --sessions
}

cmd_session() {
    local action="${1:-}"
    shift || true

    if [ "$action" = "create" ]; then
        # Capturar nome do agente - priority: arg > env > whoami
        local agent_name="${1:-}"
        [ -z "$agent_name" ] && agent_name="${KOTHAR_AGENT_NAME:-}"
        [ -z "$agent_name" ] && agent_name="${USER:-kothar}"

        # Info do ambiente
        local terminal="${TERM:-unknown}"
        local pid=$$
        local hostname="${HOSTNAME:-localhost}"

        local res
        res=$(curl -s -X POST "${API_URL}/api/sessions/" \
            -H "Content-Type: application/json" \
            -d "{
                \"agent_name\": \"${agent_name}\",
                \"task_summary\": \"Sessão ${agent_name} - Terminal ${terminal}\",
                \"llm_model\": \"${KOTHAR_MODEL:-unknown}\",
                \"metadata\": {
                    \"terminal\": \"${terminal}\",
                    \"pid\": ${pid},
                    \"hostname\": \"${hostname}\",
                    \"cwd\": \"$(pwd)\",
                    \"created_via\": \"kothar_cli\"
                }
            }")

        local new_id
        new_id=$(echo "$res" | grep -o '"id":"[^"]*' | cut -d'"' -f4 || true)

        if [ -n "$new_id" ]; then
            # Salvar sessão no arquivo específico deste processo
            local session_file="/tmp/kothar_session_${pid}.json"
            echo "{\"kothar_session_id\": \"${new_id}\", \"agent_name\": \"${agent_name}\", \"created_at\": \"$(date -Iseconds)\"}" > "$session_file"

            log_success "Sessão criada: ${new_id}"
            log_info "Agente: ${agent_name}"
            log_info "Arquivo de sessão: ${session_file}"
            echo ""
            echo "Para ver traces: kothar trace ${new_id} -f"
        else
            log_error "Falha ao criar sessão. API respondeu: $res"
        fi

    elif [ "$action" = "current" ] || [ "$action" = "status" ]; then
        # Mostrar sessão atual
        local pid=$$
        local session_file="/tmp/kothar_session_${pid}.json"
        if [ -f "$session_file" ]; then
            cat "$session_file"
        else
            log_error "Nenhuma sessão ativa neste terminal."
            log_info "Crie uma nova: kothar session create [nome]"
        fi

    elif [ "$action" = "list" ]; then
        # Listar sessões ativas
        cmd_sessions

    elif [ "$action" = "end" ] || [ "$action" = "close" ]; then
        # Encerrar sessão atual
        local pid=$$
        local session_file="/tmp/kothar_session_${pid}.json"
        if [ -f "$session_file" ]; then
            local session_id
            session_id=$(cat "$session_file" | grep -o '"kothar_session_id":"[^"]*' | cut -d'"' -f4 || true)
            if [ -n "$session_id" ]; then
                log_info "Encerrando sessão: ${session_id}"
                curl -s -X PATCH "${API_URL}/api/sessions/${session_id}/complete" \
                    -H "Content-Type: application/json" \
                    -d '{"status": "completed"}' > /dev/null

                # Compilar relatório
                curl -s -X POST "${API_URL}/api/orchestrate/compile" \
                    -H "Content-Type: application/json" \
                    -d "{\"session_id\": \"${session_id}\"}" > /dev/null

                rm -f "$session_file"
                log_success "Sessão encerrada e compilada!"
            fi
        else
            log_error "Nenhuma sessão ativa para encerrar."
        fi

    elif [ "$action" = "resume" ]; then
        local sid="${1:-}"
        if [ -z "$sid" ]; then
            log_error "Uso: kothar session resume [session_id]"
            return 1
        fi
        local res
        res=$(api_get "/api/sessions/${sid}")
        if echo "$res" | grep -q '"error"'; then
            log_error "Sessão não encontrada: $sid"
        else
            log_success "Sessão recuperada: $sid"
            local session_file="/tmp/kothar_session_$$.json"
            echo "{\"kothar_session_id\": \"${sid}\", \"resumed\": true}" > "$session_file"
            log_info "Arquivo de sessão: ${session_file}"
        fi

    else
        echo ""
        echo -e "${BOLD}USO: kothar session [comando]${RESET}"
        echo ""
        echo -e "${BOLD}Comandos:${RESET}"
        echo -e "  ${GREEN}create [nome]${RESET}   Cria nova sessão (nome = agent name)"
        echo -e "  ${GREEN}current${RESET}          Mostra sessão atual"
        echo -e "  ${GREEN}list${RESET}             Lista todas as sessões"
        echo -e "  ${GREEN}end${RESET}              Encerra sessão atual + compila"
        echo -e "  ${GREEN}resume [id]${RESET}      Retoma uma sessão existente"
        echo ""
        echo -e "${BOLD}Exemplos:${RESET}"
        echo "  kothar session create meu_agente"
        echo "  kothar session create claude-code"
        echo "  kothar session current"
        echo "  kothar session end"
        echo ""
    fi
}

# =============================================================
# Dispatcher
# =============================================================

COMMAND="${1:-help}"
shift || true

case "${COMMAND}" in
    start)       cmd_start "$@" ;;
    stop)        cmd_stop "$@" ;;
    restart)     cmd_restart "$@" ;;
    status)      cmd_status "$@" ;;
    logs)        cmd_logs "$@" ;;
    trace)       cmd_trace_live "$@" ;;
    sessions)    cmd_sessions "$@" ;;
    session)     cmd_session "$@" ;;
    health)      cmd_health "$@" ;;
    setup)       cmd_setup "$@" ;;
    hooks)       cmd_hooks "$@" ;;
    version|--version|-v) cmd_version ;;
    help|--help|-h|"")    cmd_help ;;
    *)
        log_error "Comando desconhecido: '${COMMAND}'"
        echo ""
        cmd_help
        exit 1
        ;;
esac

