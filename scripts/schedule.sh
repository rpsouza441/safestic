#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_FILE="$PROJECT_DIR/config/.env"
TASK_NAME="SafesticBackup"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

ACTION=${1:-install}
UNAME=$(uname -s 2>/dev/null || echo "")

log() {
    echo "[schedule] $1"
}

install_linux() {
    if [[ -z "${SCHEDULE_CRON:-}" ]]; then
        echo "SCHEDULE_CRON nao definido." >&2
        exit 1
    fi
    command -v crontab >/dev/null 2>&1 || { echo "crontab nao encontrado." >&2; exit 1; }
    mkdir -p "$PROJECT_DIR/logs"
    tmp=$(mktemp)
    crontab -l 2>/dev/null | grep -v "make backup" | grep -v "$PROJECT_DIR" > "$tmp" || true
    echo "${SCHEDULE_CRON} cd $PROJECT_DIR && make backup >> $PROJECT_DIR/logs/cron-backup.log 2>&1" >> "$tmp"
    crontab "$tmp"
    rm -f "$tmp"
    log "Agendamento cron instalado: ${SCHEDULE_CRON}"
}

remove_linux() {
    command -v crontab >/dev/null 2>&1 || { echo "crontab nao encontrado." >&2; exit 1; }
    tmp=$(mktemp)
    crontab -l 2>/dev/null | grep -v "$PROJECT_DIR" | grep -v "make backup" > "$tmp" || true
    crontab "$tmp"
    rm -f "$tmp"
    log "Entradas cron removidas."
}

status_linux() {
    command -v crontab >/dev/null 2>&1 || { echo "crontab nao encontrado." >&2; exit 1; }
    crontab -l 2>/dev/null | grep "$PROJECT_DIR" || echo "Nenhuma entrada encontrada."
}

windows_paths() {
    local path
    path=$1
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -w "$path"
    else
        echo "$path"
    fi
}

install_windows() {
    if [[ -z "${SCHEDULE_WIN_TIME:-}" ]]; then
        echo "SCHEDULE_WIN_TIME nao definido." >&2
        exit 1
    fi
    command -v schtasks.exe >/dev/null 2>&1 || { echo "schtasks.exe nao encontrado." >&2; exit 1; }
    local bash_path project_win command_str schedule_args
    bash_path=$(command -v bash)
    project_win=$(windows_paths "$PROJECT_DIR")
    bash_path=$(windows_paths "$bash_path")
    command_str="\"$bash_path\" -lc 'cd \"$project_win\" && make backup'"
    schedule_args=("/SC" "DAILY")
    if [[ -n "${SCHEDULE_WIN_DAYS:-}" ]]; then
        schedule_args=("/SC" "WEEKLY" "/D" "$SCHEDULE_WIN_DAYS")
    fi
    schtasks.exe /Delete /TN "$TASK_NAME" /F >/dev/null 2>&1 || true
    schtasks.exe /Create /TN "$TASK_NAME" "${schedule_args[@]}" /ST "$SCHEDULE_WIN_TIME" /TR "$command_str" /F >/dev/null
    log "Tarefa agendada no Windows criada para $SCHEDULE_WIN_TIME."
}

remove_windows() {
    schtasks.exe /Delete /TN "$TASK_NAME" /F >/dev/null 2>&1 || true
    log "Tarefa $TASK_NAME removida."
}

status_windows() {
    schtasks.exe /Query /TN "$TASK_NAME" 2>/dev/null || echo "Tarefa $TASK_NAME nao encontrada."
}

case "$ACTION" in
    install)
        if [[ "$UNAME" == MINGW* || "$UNAME" == MSYS* ]]; then
            install_windows
        else
            install_linux
        fi
        ;;
    remove)
        if [[ "$UNAME" == MINGW* || "$UNAME" == MSYS* ]]; then
            remove_windows
        else
            remove_linux
        fi
        ;;
    status)
        if [[ "$UNAME" == MINGW* || "$UNAME" == MSYS* ]]; then
            status_windows
        else
            status_linux
        fi
        ;;
    *)
        echo "Uso: $0 {install|remove|status}" >&2
        exit 1
        ;;
esac
