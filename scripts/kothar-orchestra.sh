#!/bin/bash
# ============================================================
# KOTHAR DOCKER ORCHESTRATOR v1.0
# Inicialização inteligente de containers com dependências
# Uso: kothar-orchestra.sh <projeto> [servico]
# ============================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/kothar-orchestra-$(date +%Y%m%d).log"
MAX_WAIT=60
HEALTH_CHECK_INTERVAL=3

# Logging
log() {
    echo -e "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "${BLUE}► $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================
# DETECÇÃO DE PROJETO
# ============================================================

detect_project() {
    local dir="$1"

    # Mapear diretórios para configurações
    case "$dir" in
        *disparo*|*disparo-em-massa*)
            echo "disparo-em-massa"
            ;;
        *crm*|*saphia*|*evo*)
            echo "crm-saphia"
            ;;
        *orby*|*orbytwin*)
            echo "orby-ia"
            ;;
        *chronodesk*)
            echo "chronodesk"
            ;;
        *bioleads*)
            echo "bioleads"
            ;;
        *linkdabio*)
            echo "linkdabio"
            ;;
        *ratoflix*)
            echo "ratoflix"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# ============================================================
# DEPENDÊNCIAS POR PROJETO
# ============================================================

get_dependencies() {
    local project="$1"

    case "$project" in
        "crm-saphia")
            echo "postgres redis"
            ;;
        "disparo-em-massa")
            echo "postgres"
            ;;
        "orby-ia")
            echo "postgres redis"
            ;;
        "chronodesk")
            echo "redis"
            ;;
        *)
            echo ""
            ;;
    esac
}

# ============================================================
# HEALTH CHECKS
# ============================================================

wait_for_postgres() {
    local container="$1"
    log "⏳ Aguardando PostgreSQL ($container) ficar pronto..."

    for i in $(seq 1 $MAX_WAIT); do
        if docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; then
            log "${GREEN}✓ PostgreSQL ($container) está pronto${NC}"
            return 0
        fi
        sleep $HEALTH_CHECK_INTERVAL
    done

    log "${RED}✗ Timeout: PostgreSQL não ficou pronto em ${MAX_WAIT}s${NC}"
    return 1
}

wait_for_redis() {
    local container="$1"
    log "⏳ Aguardando Redis ($container) ficar pronto..."

    for i in $(seq 1 $MAX_WAIT); do
        if docker exec "$container" redis-cli ping 2>/dev/null | grep -q PONG; then
            log "${GREEN}✓ Redis ($container) está pronto${NC}"
            return 0
        fi
        sleep $HEALTH_CHECK_INTERVAL
    done

    log "${RED}✗ Timeout: Redis não ficou pronto em ${MAX_WAIT}s${NC}"
    return 1
}

wait_for_service() {
    local project="$1"
    local service="$2"

    log "⏳ Aguardando serviço '$service' ficar pronto..."

    for i in $(seq 1 $MAX_WAIT); do
        # Verificar se container está rodando
        if ! docker ps --format '{{.Names}}' | grep -q "$service"; then
            sleep $HEALTH_CHECK_INTERVAL
            continue
        fi

        # Verificações específicas por serviço
        case "$service" in
            *postgres*)
                wait_for_postgres "$service" && return 0
                ;;
            *redis*)
                wait_for_redis "$service" && return 0
                ;;
            *)
                # Verificar se não saiu com erro
                status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null)
                if [[ "$status" == "running" ]]; then
                    log "${GREEN}✓ Serviço '$service' está rodando${NC}"
                    return 0
                fi
                ;;
        esac
        sleep $HEALTH_CHECK_INTERVAL
    done

    log "${YELLOW}⚠ Timeout ou erro no serviço '$service'${NC}"
    return 1
}

# ============================================================
# INICIALIZAÇÃO INTELIGENTE
# ============================================================

start_dependencies() {
    local project="$1"
    local compose_dir="$2"

    local deps=$(get_dependencies "$project")

    if [[ -z "$deps" ]]; then
        log "ℹ Nenhuma dependência definida para $project"
        return 0
    fi

    log_step "Subindo dependências para $project"

    # Verificar e lidar com conflitos de porta
    detect_port_conflicts "$compose_dir"

    # Subir apenas containers de dependência
    for dep in $deps; do
        log "📦 Iniciando: $dep"
        cd "$compose_dir"

        # Tentar docker compose ou docker-compose
        if docker compose up -d "$dep" 2>/dev/null; then
            :
        elif docker-compose up -d "$dep" 2>/dev/null; then
            :
        else
            log "${YELLOW}⚠ Não foi possível subir $dep${NC}"
            continue
        fi

        # Aguardar ficar pronto
        wait_for_service "$project" "$dep" || true
    done

    log "${GREEN}✓ Dependências iniciadas${NC}"
}

# Detectar e resolver conflitos de porta
detect_port_conflicts() {
    local compose_dir="$1"

    # Verificar conflitos comuns
    if ss -tlnp | grep -q ":5432.*postgresql"; then
        log "${YELLOW}⚠ PostgreSQL do sistema detectado na porta 5432${NC}"

        # Criar .env se não existir com porta alternativa
        if [[ ! -f "$compose_dir/.env" ]]; then
            cat > "$compose_dir/.env" << 'ENVEOF'
# Portas alternativas para evitar conflitos com serviços do sistema
POSTGRES_PORT=5433
REDIS_PORT=6380
ENVEOF
            log "${GREEN}✓ .env criado com portas alternativas${NC}"
        fi

        # Ajustar compose se necessário
        if grep -q "127.0.0.1:5432:5432" "$compose_dir/docker-compose.yml" 2>/dev/null; then
            sed -i 's/127.0.0.1:5432:5432/127.0.0.1:${POSTGRES_PORT:-5433}:5432/g' "$compose_dir/docker-compose.yml"
            log "${GREEN}✓ Porta do PostgreSQL ajustada para 5433${NC}"
        fi
    fi
}

start_main_service() {
    local project="$1"
    local compose_dir="$2"
    local service="$3"

    log_step "Subindo serviço principal: $service"

    cd "$compose_dir"

    # Subir serviço principal
    if docker compose up -d "$service" 2>/dev/null; then
        :
    elif docker-compose up -d "$service" 2>/dev/null; then
        :
    else
        # Se não especificou serviço, subir todos
        log "📦 Iniciando todos os serviços..."
        docker compose up -d 2>/dev/null || docker-compose up -d
    fi

    # Aguardar e mostrar status
    sleep 3
    show_status "$project" "$compose_dir"
}

show_status() {
    local project="$1"
    local compose_dir="$2"

    log_step "Status dos containers"

    cd "$compose_dir"

    echo -e "\n${BLUE}┌─────────────────┬──────────┬────────┐${NC}"
    echo -e "${BLUE}│ Container       │ Status   │ Ports  │${NC}"
    echo -e "${BLUE}├─────────────────┼──────────┼────────┤${NC}"

    docker compose ps 2>/dev/null | tail -n +2 | while read line; do
        local name=$(echo "$line" | awk '{print $1}')
        local status=$(echo "$line" | awk '{print $3}')
        local ports=$(echo "$line" | awk '{print $4}')

        local color="$GREEN"
        if [[ "$status" == *"Up"* ]] && [[ "$status" != *"healthy"* ]]; then
            color="$YELLOW"
        elif [[ "$status" == *"Exit"* ]]; then
            color="$RED"
        fi

        printf "${BLUE}│${NC} %-15s ${color}│ %-8s ${BLUE}│ %-6s ${BLUE}│${NC}\n" "$name" "$status" "$ports"
    done

    echo -e "${BLUE}└─────────────────┴──────────┴────────┘${NC}"
}

# ============================================================
# COMANDOS PRINCIPAIS
# ============================================================

cmd_start() {
    local project="$1"
    local service="$2"
    local compose_dir=""

    # Encontrar diretório do projeto
    case "$project" in
        "disparo-em-massa")
            if [[ -d "$HOME/kothar/disparo-em-massa" ]]; then
                compose_dir="$HOME/kothar/disparo-em-massa"
            elif [[ -d "$HOME/disparo-em-massa" ]]; then
                compose_dir="$HOME/disparo-em-massa"
            fi
            ;;
        "crm-saphia"|"crm"|"evo"|"sophia")
            # Verificar variantes de maiúsculas/minúsculas
            if [[ -d "$HOME/kothar/crm-saphia" ]]; then
                compose_dir="$HOME/kothar/crm-saphia"
            elif [[ -d "$HOME/crm-Sophia" ]]; then
                compose_dir="$HOME/crm-Sophia"
            elif [[ -d "$HOME/crm-saphia" ]]; then
                compose_dir="$HOME/crm-saphia"
            fi
            ;;
        "orby-ia"|"orby")
            if [[ -d "$HOME/Orby.ia" ]]; then
                compose_dir="$HOME/Orby.ia"
            elif [[ -d "$HOME/orby-ia" ]]; then
                compose_dir="$HOME/orby-ia"
            fi
            ;;
        "chronodesk")
            compose_dir="$HOME/chronodesk"
            ;;
        "bioleads")
            if [[ -d "$HOME/kothar/bioleads" ]]; then
                compose_dir="$HOME/kothar/bioleads"
            fi
            ;;
        "linkdabio")
            if [[ -d "$HOME/kothar/linkdabio" ]]; then
                compose_dir="$HOME/kothar/linkdabio"
            fi
            ;;
        "ratoflix")
            if [[ -d "$HOME/kothar/ratoflix" ]]; then
                compose_dir="$HOME/kothar/ratoflix"
            fi
            ;;
        "monitor-admin"|"monitor")
            if [[ -d "$HOME/Monitor-Admin" ]]; then
                compose_dir="$HOME/Monitor-Admin"
            fi
            ;;
        *)
            log "${RED}✗ Projeto '$project' não encontrado${NC}"
            echo ""
            echo "Projetos disponíveis:"
            echo "  - crm-saphia       → ~/crm-Sophia"
            echo "  - orby-ia          → ~/Orby.ia"
            echo "  - chronodesk       → ~/chronodesk"
            echo "  - monitor-admin    → ~/Monitor-Admin"
            echo "  - disparo-em-massa → ~/kothar/disparo-em-massa"
            echo "  - all              → todos"
            exit 1
            ;;
    esac

    if [[ ! -d "$compose_dir" ]]; then
        log "${RED}✗ Diretório não encontrado: $compose_dir${NC}"
        exit 1
    fi

    log_step "Iniciando projeto: $project"
    log "📂 Diretório: $compose_dir"

    # 1. Subir dependências primeiro
    start_dependencies "$project" "$compose_dir"

    # 2. Pausa para estabilização
    log "⏳ Pausa de 5s para estabilização..."
    sleep 5

    # 3. Subir serviço principal
    start_main_service "$project" "$compose_dir" "$service"
}

cmd_stop() {
    local project="$1"
    local compose_dir=""

    # Função auxiliar para encontrar diretório
    find_compose_dir() {
        case "$1" in
            "disparo-em-massa")
                [[ -d "$HOME/kothar/disparo-em-massa" ]] && echo "$HOME/kothar/disparo-em-massa" && return 0
                [[ -d "$HOME/disparo-em-massa" ]] && echo "$HOME/disparo-em-massa" && return 0
                return 1
                ;;
            "crm-saphia"|"crm"|"evo"|"sophia")
                [[ -d "$HOME/kothar/crm-saphia" ]] && echo "$HOME/kothar/crm-saphia" && return 0
                [[ -d "$HOME/crm-Sophia" ]] && echo "$HOME/crm-Sophia" && return 0
                [[ -d "$HOME/crm-saphia" ]] && echo "$HOME/crm-saphia" && return 0
                return 1
                ;;
            "orby-ia"|"orby")
                [[ -d "$HOME/Orby.ia" ]] && echo "$HOME/Orby.ia" && return 0
                [[ -d "$HOME/orby-ia" ]] && echo "$HOME/orby-ia" && return 0
                return 1
                ;;
            "chronodesk") [[ -d "$HOME/chronodesk" ]] && echo "$HOME/chronodesk" && return 0 ;;
            "monitor-admin"|"monitor") [[ -d "$HOME/Monitor-Admin" ]] && echo "$HOME/Monitor-Admin" && return 0 ;;
            *) return 1 ;;
        esac
    }

    if [[ "$project" == "all" ]]; then
        log_step "Parando TODOS os projetos"
        for proj in crm-Sophia Orby.ia chronodesk Monitor-Admin; do
            if [[ -d "$HOME/$proj" ]]; then
                echo -e "\n${YELLOW}━━━ $proj ━━━${NC}"
                (cd "$HOME/$proj" && docker compose stop 2>/dev/null || docker-compose stop 2>/dev/null)
            fi
        done
        log "${GREEN}✓ Todos os projetos parados${NC}"
        return
    fi

    compose_dir=$(find_compose_dir "$project")
    if [[ -z "$compose_dir" ]]; then
        log "${RED}✗ Projeto '$project' não encontrado${NC}"
        return 1
    fi

    log_step "Parando projeto: $project"
    cd "$compose_dir"
    docker compose stop 2>/dev/null || docker-compose stop 2>/dev/null
    log "${GREEN}✓ Projeto '$project' parado${NC}"
}

cmd_status() {
    local project="$1"

    # Função auxiliar para encontrar diretório
    find_compose_dir() {
        case "$1" in
            "disparo-em-massa")
                [[ -d "$HOME/kothar/disparo-em-massa" ]] && echo "$HOME/kothar/disparo-em-massa" && return 0
                [[ -d "$HOME/disparo-em-massa" ]] && echo "$HOME/disparo-em-massa" && return 0
                return 1
                ;;
            "crm-saphia"|"crm"|"evo"|"sophia")
                [[ -d "$HOME/kothar/crm-saphia" ]] && echo "$HOME/kothar/crm-saphia" && return 0
                [[ -d "$HOME/crm-Sophia" ]] && echo "$HOME/crm-Sophia" && return 0
                [[ -d "$HOME/crm-saphia" ]] && echo "$HOME/crm-saphia" && return 0
                return 1
                ;;
            "orby-ia"|"orby")
                [[ -d "$HOME/Orby.ia" ]] && echo "$HOME/Orby.ia" && return 0
                [[ -d "$HOME/orby-ia" ]] && echo "$HOME/orby-ia" && return 0
                return 1
                ;;
            "chronodesk") [[ -d "$HOME/chronodesk" ]] && echo "$HOME/chronodesk" && return 0 ;;
            "monitor-admin"|"monitor") [[ -d "$HOME/Monitor-Admin" ]] && echo "$HOME/Monitor-Admin" && return 0 ;;
            *) return 1 ;;
        esac
    }

    if [[ "$project" == "all" ]]; then
        log_step "Status de todos os projetos"
        for proj in crm-Sophia Orby.ia chronodesk Monitor-Admin; do
            if [[ -d "$HOME/$proj" ]]; then
                echo -e "\n${YELLOW}━━━ $proj ━━━${NC}"
                (cd "$HOME/$proj" && docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null)
            fi
        done
    else
        local compose_dir=$(find_compose_dir "$project")
        if [[ -z "$compose_dir" ]]; then
            log "${RED}✗ Projeto '$project' não encontrado${NC}"
            exit 1
        fi
        show_status "$project" "$compose_dir"
    fi
}

cmd_restart() {
    cmd_stop "$1"
    sleep 2
    cmd_start "$1" ""
}

# ============================================================
# HELP
# ============================================================

show_help() {
    cat << EOF
${BLUE}
╔══════════════════════════════════════════════════════╗
║       KOTHAR DOCKER ORCHESTRATOR v1.0               ║
╚══════════════════════════════════════════════════════╝${NC}

${GREEN}Uso:${NC} kothar-orchestra.sh <comando> [projeto] [serviço]

${YELLOW}Comandos:${NC}
  start <projeto>   Iniciar projeto com dependências
  stop <projeto>    Parar projeto
  restart <projeto> Reiniciar projeto
  status [projeto]  Ver status (all = todos)
  help              Mostrar esta ajuda

${YELLOW}Projetos:${NC}
  disparo-em-massa  (postgres)
  crm-saphia        (postgres + redis)
  orby-ia           (postgres + redis)
  chronodesk        (redis)
  all               (todos os projetos)

${YELLOW}Exemplos:${NC}
  kothar-orchestra.sh start crm-saphia
  kothar-orchestra.sh start orby-ia
  kothar-orchestra.sh status all
  kothar-orchestra.sh stop all

EOF
}

# ============================================================
# MAIN
# ============================================================

main() {
    local command="${1:-help}"
    local project="${2:-}"
    local service="${3:-}"

    case "$command" in
        start|up)
            if [[ -z "$project" ]]; then
                log "${RED}✗ Especifique o projeto${NC}"
                show_help
                exit 1
            fi
            cmd_start "$project" "$service"
            ;;
        stop|down)
            if [[ -z "$project" ]]; then
                log "${RED}✗ Especifique o projeto${NC}"
                show_help
                exit 1
            fi
            cmd_stop "$project"
            ;;
        restart)
            if [[ -z "$project" ]]; then
                log "${RED}✗ Especifique o projeto${NC}"
                exit 1
            fi
            cmd_restart "$project"
            ;;
        status|ps)
            cmd_status "${project:-all}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log "${RED}✗ Comando desconhecido: $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
