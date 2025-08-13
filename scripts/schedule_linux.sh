#!/usr/bin/env bash
# Script de agendamento para Linux (systemd) - FASE 3
# Instala e configura serviços systemd para backup e prune automático
# Uso: ./scripts/schedule_linux.sh [install|remove|status] [--user]

set -euo pipefail

# Processar argumentos
ACTION=""
USER_MODE=false

for arg in "$@"; do
    case $arg in
        install|remove|status)
            ACTION="$arg"
            ;;
        --user)
            USER_MODE=true
            ;;
        *)
            echo "Uso: $0 [install|remove|status] [--user]"
            echo "  install - Instala os serviços systemd"
            echo "  remove  - Remove os serviços systemd"
            echo "  status  - Mostra status dos serviços"
            echo "  --user  - Usa systemd do usuário (sem sudo)"
            exit 1
            ;;
    esac
done

if [ -z "$ACTION" ]; then
    echo "Erro: Ação requerida (install|remove|status)"
    exit 1
fi

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${RED}❌ $1${NC}"
}

# Configurações
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
PROJECT_NAME="safestic"
USER_NAME="$(whoami)"

# Definir diretórios baseado no modo
if [ "$USER_MODE" = true ]; then
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    SYSTEMCTL_CMD="systemctl --user"
    log_info "Modo usuário: usando systemd do usuário"
else
    SYSTEMD_DIR="/etc/systemd/system"
    SYSTEMCTL_CMD="sudo systemctl"
    log_info "Modo sistema: usando systemd do sistema (requer sudo)"
fi

# Função para criar serviço de backup
create_backup_service() {
    local service_file="$SYSTEMD_DIR/${PROJECT_NAME}-backup.service"
    
    log_info "Criando serviço de backup: $service_file"
    
    local content="[Unit]
Description=Safestic Backup Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/make backup
ExecStartPost=/usr/bin/make check
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

    if [ "$USER_MODE" = true ]; then
        content="${content//WantedBy=multi-user.target/WantedBy=default.target}"
        mkdir -p "$SYSTEMD_DIR"
        echo "$content" > "$service_file"
    else
        echo "$content" | sudo tee "$service_file" > /dev/null
    fi
    
    log_success "Serviço de backup criado"
}

# Função para criar timer de backup
create_backup_timer() {
    local timer_file="$SYSTEMD_DIR/${PROJECT_NAME}-backup.timer"
    
    log_info "Criando timer de backup: $timer_file"
    
    local content="[Unit]
Description=Safestic Backup Timer
Requires=${PROJECT_NAME}-backup.service

[Timer]
OnCalendar=daily
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target"

    if [ "$USER_MODE" = true ]; then
        echo "$content" > "$timer_file"
    else
        echo "$content" | sudo tee "$timer_file" > /dev/null
    fi
    
    log_success "Timer de backup criado (execução diária)"
}

# Função para criar serviço de prune
create_prune_service() {
    local service_file="$SYSTEMD_DIR/${PROJECT_NAME}-prune.service"
    
    log_info "Criando serviço de prune: $service_file"
    
    local content="[Unit]
Description=Safestic Prune Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/make prune
ExecStartPost=/usr/bin/make check
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"

    if [ "$USER_MODE" = true ]; then
        content="${content//WantedBy=multi-user.target/WantedBy=default.target}"
        echo "$content" > "$service_file"
    else
        echo "$content" | sudo tee "$service_file" > /dev/null
    fi
    
    log_success "Serviço de prune criado"
}

# Função para criar timer de prune
create_prune_timer() {
    local timer_file="$SYSTEMD_DIR/${PROJECT_NAME}-prune.timer"
    
    log_info "Criando timer de prune: $timer_file"
    
    local content="[Unit]
Description=Safestic Prune Timer
Requires=${PROJECT_NAME}-prune.service

[Timer]
OnCalendar=weekly
RandomizedDelaySec=2h
Persistent=true

[Install]
WantedBy=timers.target"

    if [ "$USER_MODE" = true ]; then
        echo "$content" > "$timer_file"
    else
        echo "$content" | sudo tee "$timer_file" > /dev/null
    fi
    
    log_success "Timer de prune criado (execução semanal)"
}

# Função para instalar serviços
install_services() {
    log_info "=== INSTALANDO SERVIÇOS SYSTEMD ==="
    
    # Verificar se systemd está disponível
    if ! command -v systemctl >/dev/null 2>&1; then
        log_error "systemctl não encontrado. Este sistema usa systemd?"
        exit 1
    fi
    
    # Criar diretório se necessário (modo usuário)
    if [ "$USER_MODE" = true ]; then
        mkdir -p "$SYSTEMD_DIR"
    fi
    
    # Criar serviços e timers
    create_backup_service
    create_backup_timer
    create_prune_service
    create_prune_timer
    
    # Recarregar systemd
    log_info "Recarregando systemd..."
    $SYSTEMCTL_CMD daemon-reload
    
    # Habilitar e iniciar timers
    log_info "Habilitando timers..."
    $SYSTEMCTL_CMD enable "${PROJECT_NAME}-backup.timer"
    $SYSTEMCTL_CMD enable "${PROJECT_NAME}-prune.timer"
    
    $SYSTEMCTL_CMD start "${PROJECT_NAME}-backup.timer"
    $SYSTEMCTL_CMD start "${PROJECT_NAME}-prune.timer"
    
    log_success "=== SERVIÇOS INSTALADOS COM SUCESSO ==="
    log_info "Backup: execução diária com delay aleatório de até 1h"
    log_info "Prune: execução semanal com delay aleatório de até 2h"
    log_info "Use 'systemctl --user status' ou 'sudo systemctl status' para verificar"
}

# Função para remover serviços
remove_services() {
    log_info "=== REMOVENDO SERVIÇOS SYSTEMD ==="
    
    # Parar e desabilitar timers
    for service in "${PROJECT_NAME}-backup" "${PROJECT_NAME}-prune"; do
        log_info "Parando e desabilitando $service..."
        $SYSTEMCTL_CMD stop "${service}.timer" 2>/dev/null || true
        $SYSTEMCTL_CMD disable "${service}.timer" 2>/dev/null || true
        $SYSTEMCTL_CMD stop "${service}.service" 2>/dev/null || true
        $SYSTEMCTL_CMD disable "${service}.service" 2>/dev/null || true
    done
    
    # Remover arquivos
    for file in "${PROJECT_NAME}-backup.service" "${PROJECT_NAME}-backup.timer" "${PROJECT_NAME}-prune.service" "${PROJECT_NAME}-prune.timer"; do
        local full_path="$SYSTEMD_DIR/$file"
        if [ -f "$full_path" ]; then
            log_info "Removendo $full_path"
            if [ "$USER_MODE" = true ]; then
                rm -f "$full_path"
            else
                sudo rm -f "$full_path"
            fi
        fi
    done
    
    # Recarregar systemd
    log_info "Recarregando systemd..."
    $SYSTEMCTL_CMD daemon-reload
    
    log_success "=== SERVIÇOS REMOVIDOS COM SUCESSO ==="
}

# Função para mostrar status
show_status() {
    log_info "=== STATUS DOS SERVIÇOS SYSTEMD ==="
    
    for service in "${PROJECT_NAME}-backup" "${PROJECT_NAME}-prune"; do
        echo ""
        log_info "Status do $service:"
        
        # Status do timer
        echo "Timer:"
        $SYSTEMCTL_CMD status "${service}.timer" --no-pager -l || true
        
        # Status do serviço
        echo "\nServiço:"
        $SYSTEMCTL_CMD status "${service}.service" --no-pager -l || true
        
        # Próxima execução
        echo "\nPróxima execução:"
        $SYSTEMCTL_CMD list-timers "${service}.timer" --no-pager || true
        
        echo "\n" + "="*50
    done
    
    # Logs recentes
    log_info "Logs recentes (últimas 10 linhas):"
    journalctl --user -u "${PROJECT_NAME}-*" -n 10 --no-pager || \
    sudo journalctl -u "${PROJECT_NAME}-*" -n 10 --no-pager || true
}

# Executar ação
case $ACTION in
    install)
        install_services
        ;;
    remove)
        remove_services
        ;;
    status)
        show_status
        ;;
esac

log_info "Operação '$ACTION' concluída."