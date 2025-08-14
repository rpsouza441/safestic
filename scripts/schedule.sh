#!/bin/bash
# Script de agendamento simplificado para Linux (crontab)
# Cria tarefas agendadas usando scripts shell diretos
# Uso: ./scripts/schedule_simple.sh [install|remove|status]

set -e

# Configuracoes
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="Safestic"
CURRENT_USER=$(whoami)

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funcoes de log
write_log_info() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${BLUE}INFO: $1${NC}"
}

write_log_success() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}SUCCESS: $1${NC}"
}

write_log_warning() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${YELLOW}WARNING: $1${NC}"
}

write_log_error() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${RED}ERROR: $1${NC}"
}

# Verificar se crontab esta disponivel
check_crontab() {
    if ! command -v crontab &> /dev/null; then
        write_log_error "crontab nao encontrado. Instale cron/crontab primeiro."
        exit 1
    fi
}

# Instalar tarefas no crontab
install_simple_tasks() {
    write_log_info "=== INSTALANDO TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    check_crontab
    
    # Verificar se os scripts existem
    local backup_script="$PROJECT_DIR/scripts/backup_task.sh"
    local prune_script="$PROJECT_DIR/scripts/prune_task.sh"
    
    if [ ! -f "$backup_script" ]; then
        write_log_error "Script de backup nao encontrado: $backup_script"
        exit 1
    fi
    
    if [ ! -f "$prune_script" ]; then
        write_log_error "Script de prune nao encontrado: $prune_script"
        exit 1
    fi
    
    # Tornar scripts executaveis
    chmod +x "$backup_script" "$prune_script"
    
    # Obter crontab atual (ignorar erro se nao existir)
    local temp_cron=$(mktemp)
    crontab -l 2>/dev/null > "$temp_cron" || true
    
    # Remover entradas antigas do Safestic se existirem
    sed -i '/# Safestic-Backup-Simple/d' "$temp_cron"
    sed -i '/# Safestic-Prune-Simple/d' "$temp_cron"
    grep -v "$backup_script" "$temp_cron" > "${temp_cron}.tmp" || true
    grep -v "$prune_script" "${temp_cron}.tmp" > "$temp_cron" || true
    rm -f "${temp_cron}.tmp"
    
    # Adicionar novas entradas
    echo "" >> "$temp_cron"
    echo "# Safestic-Backup-Simple - Backup diario as 02:00" >> "$temp_cron"
    echo "0 2 * * * $backup_script >/dev/null 2>&1" >> "$temp_cron"
    echo "" >> "$temp_cron"
    echo "# Safestic-Prune-Simple - Prune semanal aos domingos as 03:00" >> "$temp_cron"
    echo "0 3 * * 0 $prune_script >/dev/null 2>&1" >> "$temp_cron"
    
    # Instalar novo crontab
    if crontab "$temp_cron"; then
        write_log_success "Tarefas agendadas instaladas com sucesso"
        write_log_info "Backup: execucao diaria as 02:00"
        write_log_info "Prune: execucao semanal aos domingos as 03:00"
        write_log_info "Logs serao salvos em: logs/backup_task.log e logs/prune_task.log"
    else
        write_log_error "Falha ao instalar tarefas no crontab"
        rm -f "$temp_cron"
        exit 1
    fi
    
    rm -f "$temp_cron"
    write_log_success "=== TAREFAS SIMPLIFICADAS INSTALADAS COM SUCESSO ==="
}

# Remover tarefas do crontab
remove_simple_tasks() {
    write_log_info "=== REMOVENDO TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    check_crontab
    
    # Obter crontab atual
    local temp_cron=$(mktemp)
    if ! crontab -l 2>/dev/null > "$temp_cron"; then
        write_log_warning "Nenhum crontab encontrado para o usuario atual"
        rm -f "$temp_cron"
        return 0
    fi
    
    # Remover entradas do Safestic
    local backup_script="$PROJECT_DIR/scripts/backup_task.sh"
    local prune_script="$PROJECT_DIR/scripts/prune_task.sh"
    
    sed -i '/# Safestic-Backup-Simple/d' "$temp_cron"
    sed -i '/# Safestic-Prune-Simple/d' "$temp_cron"
    grep -v "$backup_script" "$temp_cron" > "${temp_cron}.tmp" || true
    grep -v "$prune_script" "${temp_cron}.tmp" > "$temp_cron" || true
    rm -f "${temp_cron}.tmp"
    
    # Reinstalar crontab limpo
    if crontab "$temp_cron"; then
        write_log_success "Tarefas do Safestic removidas do crontab"
    else
        write_log_error "Falha ao atualizar crontab"
        rm -f "$temp_cron"
        exit 1
    fi
    
    rm -f "$temp_cron"
    write_log_success "=== TAREFAS SIMPLIFICADAS REMOVIDAS COM SUCESSO ==="
}

# Mostrar status das tarefas
show_simple_task_status() {
    write_log_info "=== STATUS DAS TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    check_crontab
    
    echo ""
    write_log_info "Crontab atual do usuario $CURRENT_USER:"
    echo "$(printf '%*s' 50 '' | tr ' ' '-')"
    
    if crontab -l 2>/dev/null | grep -E "(Safestic|backup_task|prune_task)"; then
        echo "$(printf '%*s' 50 '' | tr ' ' '-')"
    else
        write_log_warning "Nenhuma tarefa do Safestic encontrada no crontab"
    fi
    
    echo ""
    write_log_info "Verificando logs recentes:"
    
    local backup_log="$PROJECT_DIR/logs/backup_task.log"
    local prune_log="$PROJECT_DIR/logs/prune_task.log"
    
    if [ -f "$backup_log" ]; then
        echo ""
        write_log_info "Ultimas 5 linhas do log de backup:"
        tail -n 5 "$backup_log" 2>/dev/null || write_log_warning "Erro ao ler log de backup"
    else
        write_log_warning "Log de backup nao encontrado: $backup_log"
    fi
    
    if [ -f "$prune_log" ]; then
        echo ""
        write_log_info "Ultimas 5 linhas do log de prune:"
        tail -n 5 "$prune_log" 2>/dev/null || write_log_warning "Erro ao ler log de prune"
    else
        write_log_warning "Log de prune nao encontrado: $prune_log"
    fi
    
    echo ""
    write_log_info "Para ver logs completos:"
    echo "  Backup: tail -f $backup_log"
    echo "  Prune:  tail -f $prune_log"
}

# Mostrar ajuda
show_help() {
    echo "Uso: $0 [install|remove|status|help]"
    echo ""
    echo "Comandos:"
    echo "  install  - Instala tarefas agendadas no crontab"
    echo "  remove   - Remove tarefas agendadas do crontab"
    echo "  status   - Mostra status das tarefas agendadas"
    echo "  help     - Mostra esta ajuda"
    echo ""
    echo "Agendamento:"
    echo "  Backup: Diario as 02:00"
    echo "  Prune:  Semanal aos domingos as 03:00"
}

# Executar acao principal
case "${1:-help}" in
    "install")
        install_simple_tasks
        ;;
    "remove")
        remove_simple_tasks
        ;;
    "status")
        show_simple_task_status
        ;;
    "help")
        show_help
        ;;
    *)
        write_log_error "Acao invalida: $1"
        show_help
        exit 1
        ;;
esac

write_log_info "Operacao '${1:-help}' concluida."
