#!/usr/bin/env bash
# Script auxiliar para ativar o ambiente virtual do Safestic
# Uso: source ./activate_venv.sh

set -euo pipefail

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se o ambiente virtual existe
if [ ! -f ".venv/bin/activate" ]; then
    log_error "Ambiente virtual não encontrado em .venv/"
    log_info "Execute primeiro: ./scripts/setup_linux.sh"
    return 1 2>/dev/null || exit 1
fi

# Verificar se já está ativado
if [ -n "${VIRTUAL_ENV:-}" ]; then
    if [ "$VIRTUAL_ENV" = "$(pwd)/.venv" ]; then
        log_info "Ambiente virtual já está ativado"
        return 0 2>/dev/null || exit 0
    else
        log_info "Desativando ambiente virtual anterior: $VIRTUAL_ENV"
        deactivate 2>/dev/null || true
    fi
fi

# Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
source ".venv/bin/activate"

if [ -n "${VIRTUAL_ENV:-}" ]; then
    log_success "Ambiente virtual ativado: $VIRTUAL_ENV"
    log_info "Python: $(which python)"
    log_info "Pip: $(which pip)"
    log_info "Para desativar, execute: deactivate"
else
    log_error "Falha ao ativar ambiente virtual"
    return 1 2>/dev/null || exit 1
fi