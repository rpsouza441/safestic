#!/bin/bash
# Script de prune automatizado para Linux
# Executa limpeza de snapshots antigos e verificacao usando Python diretamente
# Uso: ./scripts/prune_task.sh

# Configuracoes
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_DIR/.venv/bin/activate"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="${1:-logs/prune_task.log}"
FULL_LOG_PATH="$PROJECT_DIR/$LOG_FILE"

# Criar diretorio de logs se nao existir
mkdir -p "$LOG_DIR"

# Funcao de log
write_task_log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"
    echo "$log_entry"
    echo "$log_entry" >> "$FULL_LOG_PATH"
}

# Funcao para sair com erro
exit_with_error() {
    write_task_log "$1" "ERROR"
    write_task_log "=== PRUNE AUTOMATIZADO FALHOU ===" "ERROR"
    exit 1
}

# Inicio do script
write_task_log "=== INICIANDO PRUNE AUTOMATIZADO ===" "INFO"

# Mudar para diretorio do projeto
cd "$PROJECT_DIR" || exit_with_error "Falha ao acessar diretorio do projeto: $PROJECT_DIR"
write_task_log "Diretorio de trabalho: $PROJECT_DIR" "INFO"

# Ativar ambiente virtual se existir
if [ -f "$VENV_PATH" ]; then
    write_task_log "Ativando ambiente virtual..." "INFO"
    source "$VENV_PATH"
else
    write_task_log "Ambiente virtual nao encontrado, usando Python global" "WARN"
fi

# Executar prune
write_task_log "Executando limpeza de snapshots antigos..." "INFO"
if python "manual_prune.py" 2>&1 | tee -a "$FULL_LOG_PATH"; then
    write_task_log "Prune concluido com sucesso" "SUCCESS"
else
    exit_with_error "Falha no prune. Codigo de saida: $?"
fi

# Executar verificacao
write_task_log "Executando verificacao do repositorio..." "INFO"
if python "check_restic_access.py" 2>&1 | tee -a "$FULL_LOG_PATH"; then
    write_task_log "Verificacao concluida com sucesso" "SUCCESS"
else
    write_task_log "Falha na verificacao. Codigo de saida: $?" "WARN"
    write_task_log "Continuando apesar da falha na verificacao..." "WARN"
fi

write_task_log "=== PRUNE AUTOMATIZADO CONCLUIDO ===" "SUCCESS"
exit 0
