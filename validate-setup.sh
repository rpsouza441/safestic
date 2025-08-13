#!/bin/bash
# Script de validação final do setup Safestic
# Verifica se todos os componentes estão funcionando corretamente

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# Contador de erros
ERROR_COUNT=0

# Função para verificar comando
check_command() {
    local cmd=$1
    local name=$2
    
    if command -v "$cmd" >/dev/null 2>&1; then
        local version=$("$cmd" --version 2>/dev/null | head -1 || echo "unknown")
        log_success "$name encontrado: $version"
        return 0
    else
        log_error "$name não encontrado"
        ((ERROR_COUNT++))
        return 1
    fi
}

# Função para verificar arquivo
check_file() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        local size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "unknown")
        log_success "$name encontrado ($size)"
        return 0
    else
        log_error "$name não encontrado: $file"
        ((ERROR_COUNT++))
        return 1
    fi
}

# Função para verificar diretório
check_directory() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        local count=$(find "$dir" -type f 2>/dev/null | wc -l || echo "0")
        log_success "$name encontrado ($count arquivos)"
        return 0
    else
        log_error "$name não encontrado: $dir"
        ((ERROR_COUNT++))
        return 1
    fi
}

echo "🔍 === VALIDAÇÃO FINAL DO SETUP SAFESTIC ==="
echo ""

# 1. Verificar dependências do sistema
log_info "1. Verificando dependências do sistema..."
check_command "git" "Git"
check_command "make" "Make" || check_command "mingw32-make" "Make (MinGW)"
check_command "python" "Python" || check_command "python3" "Python3"
check_command "restic" "Restic"
echo ""

# 2. Verificar arquivos do projeto
log_info "2. Verificando arquivos do projeto..."
check_file "Makefile" "Makefile"
check_file ".env.example" "Arquivo de exemplo .env"
check_file "requirements.txt" "Dependências Python"
check_file "pyproject.toml" "Configuração do projeto"
check_file "SETUP_SAFESTIC.md" "Guia de setup"
echo ""

# 3. Verificar scripts
log_info "3. Verificando scripts de setup..."
check_file "scripts/setup_linux.sh" "Script de setup Linux"
check_file "scripts/setup_windows.sh" "Script de setup Windows"
check_file "check-backup-health.sh" "Script de verificação de saúde"
check_file "safestic-backup.ps1" "Script PowerShell"
check_file "validate-setup.sh" "Script de validação"
echo ""

# 4. Verificar diretórios
log_info "4. Verificando estrutura de diretórios..."
check_directory "services" "Diretório de serviços"
check_directory "scripts" "Diretório de scripts"
if [ -d "venv" ]; then
    log_success "Ambiente virtual encontrado"
else
    log_warning "Ambiente virtual não encontrado (execute o setup)"
fi
if [ -d "logs" ]; then
    log_success "Diretório de logs encontrado"
else
    log_info "Diretório de logs será criado automaticamente"
fi
echo ""

# 5. Verificar versão do Python
log_info "5. Verificando versão do Python..."
if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    log_error "Python não encontrado"
    ((ERROR_COUNT++))
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        log_success "Python $PYTHON_VERSION (compatível)"
    else
        log_error "Python 3.10+ necessário. Encontrado: $PYTHON_VERSION"
        ((ERROR_COUNT++))
    fi
fi
echo ""

# 6. Verificar ambiente virtual (se existir)
if [ -d "venv" ]; then
    log_info "6. Verificando ambiente virtual..."
    
    # Ativar ambiente virtual
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_success "Ambiente virtual ativado (Linux/Mac)"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        log_success "Ambiente virtual ativado (Windows)"
    else
        log_error "Script de ativação do ambiente virtual não encontrado"
        ((ERROR_COUNT++))
    fi
    
    # Verificar dependências Python
    if [ -f "requirements.txt" ]; then
        log_info "Verificando dependências Python instaladas..."
        
        # Verificar algumas dependências críticas
        CRITICAL_DEPS=("python-dotenv" "keyring" "pydantic" "pytest")
        for dep in "${CRITICAL_DEPS[@]}"; do
            if pip show "$dep" >/dev/null 2>&1; then
                log_success "$dep instalado"
            else
                log_warning "$dep não instalado (execute: pip install -r requirements.txt)"
            fi
        done
    fi
else
    log_info "6. Ambiente virtual não encontrado (será criado no setup)"
fi
echo ""

# 7. Verificar configuração (se .env existir)
if [ -f ".env" ]; then
    log_info "7. Verificando arquivo .env..."
    
    # Verificar variáveis críticas
    CRITICAL_VARS=("STORAGE_PROVIDER" "STORAGE_BUCKET" "CREDENTIAL_SOURCE" "BACKUP_SOURCE_DIRS")
    for var in "${CRITICAL_VARS[@]}"; do
        if grep -q "^$var=" ".env" 2>/dev/null; then
            log_success "$var configurado"
        else
            log_warning "$var não configurado em .env"
        fi
    done
else
    log_info "7. Arquivo .env não encontrado (copie de .env.example)"
fi
echo ""

# 8. Testar Makefile
log_info "8. Testando targets do Makefile..."
MAKE_CMD="make"
if ! command -v make >/dev/null 2>&1; then
    if command -v mingw32-make >/dev/null 2>&1; then
        MAKE_CMD="mingw32-make"
    else
        log_error "Make não encontrado"
        ((ERROR_COUNT++))
        MAKE_CMD=""
    fi
fi

if [ -n "$MAKE_CMD" ]; then
    # Testar help
    if $MAKE_CMD help >/dev/null 2>&1; then
        log_success "Makefile funcional"
        
        # Verificar targets importantes
        IMPORTANT_TARGETS=("backup" "init" "check" "list" "restore" "dry-run" "stats")
        log_info "Verificando targets disponíveis..."
        for target in "${IMPORTANT_TARGETS[@]}"; do
            if $MAKE_CMD -n "$target" >/dev/null 2>&1; then
                log_success "Target '$target' disponível"
            else
                log_warning "Target '$target' não encontrado"
            fi
        done
    else
        log_error "Erro ao executar Makefile"
        ((ERROR_COUNT++))
    fi
fi
echo ""

# 9. Verificar permissões de scripts
log_info "9. Verificando permissões de scripts..."
SCRIPTS=("scripts/setup_linux.sh" "scripts/setup_windows.sh" "check-backup-health.sh" "validate-setup.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            log_success "$script executável"
        else
            log_info "$script não executável (normal no Windows)"
        fi
    fi
done
echo ""

# 10. Resumo final
log_info "=== RESUMO DA VALIDAÇÃO ==="
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    log_success "🎉 SETUP VALIDADO COM SUCESSO!"
    echo ""
    log_info "✅ Todos os componentes estão funcionando corretamente"
    log_info "📋 Próximos passos recomendados:"
    echo "   1. Configure o arquivo .env (copie de .env.example)"
    echo "   2. Configure credenciais seguras"
    echo "   3. Execute: make check"
    echo "   4. Execute: make init (se repositório novo)"
    echo "   5. Execute: make dry-run (teste)"
    echo "   6. Execute: make backup (primeiro backup)"
    echo "   7. Configure agendamento (systemd/Task Scheduler)"
else
    log_error "❌ VALIDAÇÃO FALHOU - $ERROR_COUNT erro(s) encontrado(s)"
    echo ""
    log_info "🔧 Ações recomendadas:"
    echo "   1. Execute o script de setup apropriado:"
    echo "      - Linux: ./scripts/setup_linux.sh"
    echo "      - Windows: ./scripts/setup_windows.sh"
    echo "   2. Reinicie o terminal após o setup"
    echo "   3. Execute este script novamente"
    echo ""
    exit 1
fi

echo ""
log_success "Validação concluída! Sistema Safestic pronto para uso."