#!/usr/bin/env bash
# Setup script para Windows (Git Bash) - FASE 2
# Verifica e instala dependências necessárias para o Safestic
# Uso: ./scripts/setup_windows.sh [--assume-yes]

set -euo pipefail

# Processar argumentos
ASSUME_YES=false
for arg in "$@"; do
    case $arg in
        --assume-yes)
            ASSUME_YES=true
            shift
            ;;
        *)
            echo "Uso: $0 [--assume-yes]"
            exit 1
            ;;
    esac
done

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_command() {
    command -v "$1" >/dev/null 2>&1
}

install_with_winget() {
    local package="$1"
    local name="$2"
    
    log_info "Instalando $name via winget..."
    local cmd="winget install --id $package --silent --accept-package-agreements --accept-source-agreements"
    if [ "$ASSUME_YES" = false ]; then
        cmd="winget install --id $package --interactive"
    fi
    
    if powershell.exe -Command "$cmd" 2>/dev/null; then
        log_success "$name instalado com sucesso"
        return 0
    else
        log_error "Falha ao instalar $name via winget"
        return 1
    fi
}

install_with_choco() {
    local package="$1"
    local name="$2"
    
    log_info "Instalando $name via chocolatey..."
    local cmd="choco install $package"
    if [ "$ASSUME_YES" = true ]; then
        cmd="choco install $package -y"
    fi
    
    if powershell.exe -Command "$cmd" 2>/dev/null; then
        log_success "$name instalado com sucesso"
        return 0
    else
        log_error "Falha ao instalar $name via chocolatey"
        return 1
    fi
}

log_info "=== SETUP SAFESTIC PARA WINDOWS (GIT BASH) ==="
log_info "Verificando e instalando dependencias..."

# Verificar se winget esta disponivel
HAS_WINGET=false
if powershell.exe -Command "Get-Command winget -ErrorAction SilentlyContinue" >/dev/null 2>&1; then
    HAS_WINGET=true
    log_success "winget detectado"
fi

# Verificar se chocolatey esta disponivel
HAS_CHOCO=false
if powershell.exe -Command "Get-Command choco -ErrorAction SilentlyContinue" >/dev/null 2>&1; then
    HAS_CHOCO=true
    log_success "chocolatey detectado"
fi

if [ "$HAS_WINGET" = false ] && [ "$HAS_CHOCO" = false ]; then
    log_error "Nenhum gerenciador de pacotes encontrado (winget ou chocolatey)"
    log_error "Execute primeiro: scripts/bootstrap_windows.ps1"
    exit 1
fi

# Verificar e instalar Git (se necessario)
if check_command git; then
    log_success "Git ja instalado: $(git --version)"
else
    log_warning "Git nao encontrado. Instalando..."
    INSTALLED=false
    
    if [ "$HAS_WINGET" = true ]; then
        if install_with_winget "Git.Git" "Git for Windows"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ] && [ "$HAS_CHOCO" = true ]; then
        if install_with_choco "git" "Git for Windows"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ]; then
        log_error "Falha ao instalar Git"
        exit 1
    fi
fi

# Verificar e instalar Make
if check_command make; then
    log_success "Make ja instalado: $(make --version | head -n1)"
else
    log_warning "Make nao encontrado. Instalando..."
    INSTALLED=false
    
    if [ "$HAS_WINGET" = true ]; then
        if install_with_winget "GnuWin32.Make" "GNU Make"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ] && [ "$HAS_CHOCO" = true ]; then
        if install_with_choco "make" "GNU Make"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ]; then
        log_error "Falha ao instalar Make"
        exit 1
    fi
fi

# Verificar e instalar Python 3.10+
if check_command python; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    log_success "Python ja instalado: Python $PYTHON_VERSION"
    
    # Verificar se a versao e >= 3.10
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        log_error "Python $PYTHON_VERSION e muito antigo. Versao minima: 3.10"
        exit 1
    fi
else
    log_warning "Python nao encontrado. Instalando..."
    INSTALLED=false
    
    if [ "$HAS_WINGET" = true ]; then
        if install_with_winget "Python.Python.3.12" "Python 3.12"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ] && [ "$HAS_CHOCO" = true ]; then
        if install_with_choco "python" "Python"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ]; then
        log_error "Falha ao instalar Python"
        exit 1
    fi
fi

# Verificar e instalar pip
if check_command pip; then
    log_success "pip ja instalado: $(pip --version)"
else
    log_warning "pip nao encontrado. Instalando..."
    if python -m ensurepip --upgrade; then
        log_success "pip instalado com sucesso"
    else
        log_error "Falha ao instalar pip"
        exit 1
    fi
fi

# Verificar e instalar Restic
if check_command restic; then
    log_success "Restic ja instalado: $(restic version)"
else
    log_warning "Restic nao encontrado. Instalando..."
    INSTALLED=false
    
    if [ "$HAS_WINGET" = true ]; then
        if install_with_winget "restic.restic" "Restic"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ] && [ "$HAS_CHOCO" = true ]; then
        if install_with_choco "restic" "Restic"; then
            INSTALLED=true
        fi
    fi
    
    if [ "$INSTALLED" = false ]; then
        log_error "Falha ao instalar Restic"
        exit 1
    fi
fi

# Instalar dependencias Python do projeto
log_info "Instalando dependencias Python do projeto..."

if [ -f "pyproject.toml" ]; then
    log_info "Detectado pyproject.toml. Instalando dependencias..."
    if pip install -e .; then
        log_success "Dependencias do pyproject.toml instaladas"
    else
        log_error "Falha ao instalar dependencias do pyproject.toml"
        exit 1
    fi
elif [ -f "requirements.txt" ]; then
    log_info "Detectado requirements.txt. Instalando dependencias..."
    if pip install -r requirements.txt; then
        log_success "Dependencias do requirements.txt instaladas"
    else
        log_error "Falha ao instalar dependencias do requirements.txt"
        exit 1
    fi
else
    log_warning "Nenhum arquivo de dependencias encontrado (pyproject.toml ou requirements.txt)"
fi

# Verificacao final
log_info "=== VERIFICACAO FINAL ==="

TOOLS=("git --version" "make --version" "python --version" "pip --version" "restic version")
ALL_OK=true

for tool_cmd in "${TOOLS[@]}"; do
    tool_name=$(echo $tool_cmd | cut -d' ' -f1)
    if eval $tool_cmd >/dev/null 2>&1; then
        version=$(eval $tool_cmd 2>&1 | head -n1)
        log_success "$tool_name: $version"
    else
        log_error "$tool_name: FALHOU"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    log_error "Algumas ferramentas falharam na verificacao"
    log_warning "Pode ser necessario reiniciar o terminal ou adicionar ao PATH manualmente"
    exit 1
fi

log_success "=== SETUP CONCLUIDO COM SUCESSO ==="
log_info "Todas as dependencias foram instaladas e verificadas!"
log_info "Proximos passos:"
log_info "1. Configure o arquivo .env baseado no .env.example"
log_info "2. Execute: make init"
log_info "3. Execute: make backup"