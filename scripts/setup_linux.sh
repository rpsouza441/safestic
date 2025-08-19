#!/usr/bin/env bash
# Setup script para Linux - FASE 2
# Detecta distribuicao e instala dependencias necessarias para o Safestic
# Uso: ./scripts/setup_linux.sh [--assume-yes]

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

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    
    log_info "Distribuicao detectada: $DISTRO $VERSION"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

install_packages() {
    local packages="$1"
    local install_cmd=""
    
    case $DISTRO in
        ubuntu|debian)
            log_info "Atualizando lista de pacotes..."
            sudo apt update
            install_cmd="sudo apt install"
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd -y"
            fi
            ;;
        fedora|centos|rhel)
            if check_command dnf; then
                install_cmd="sudo dnf install"
            elif check_command yum; then
                install_cmd="sudo yum install"
            fi
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd -y"
            fi
            ;;
        arch|manjaro)
            install_cmd="sudo pacman -S"
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd --noconfirm"
            fi
            ;;
        opensuse*)
            install_cmd="sudo zypper install"
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd -y"
            fi
            ;;
        *)
            log_error "Distribuicao nao suportada: $DISTRO"
            exit 1
            ;;
    esac
    
    log_info "Instalando pacotes: $packages"
    if $install_cmd $packages; then
        log_success "Pacotes instalados com sucesso"
    else
        log_error "Falha ao instalar pacotes: $packages"
        exit 1
    fi
}

install_restic() {
    if check_command restic; then
        log_success "Restic ja instalado: $(restic version)"
        return 0
    fi
    
    log_info "Instalando Restic..."
    
    # Tentar instalar via gerenciador de pacotes primeiro
    case $DISTRO in
        ubuntu|debian)
            if apt-cache search restic | grep -q "^restic "; then
                local cmd="sudo apt install restic"
                if [ "$ASSUME_YES" = true ]; then
                    cmd="$cmd -y"
                fi
                if $cmd; then
                    return 0
                fi
            fi
            ;;
        fedora)
            if dnf search restic 2>/dev/null | grep -q restic; then
                local cmd="sudo dnf install restic"
                if [ "$ASSUME_YES" = true ]; then
                    cmd="$cmd -y"
                fi
                if $cmd; then
                    return 0
                fi
            fi
            ;;
        arch|manjaro)
            if pacman -Ss restic | grep -q restic; then
                local cmd="sudo pacman -S restic"
                if [ "$ASSUME_YES" = true ]; then
                    cmd="$cmd --noconfirm"
                fi
                if $cmd; then
                    return 0
                fi
            fi
            ;;
    esac
    
    # Se nao estiver disponivel no repositorio, instalar manualmente
    log_warning "Restic nao encontrado nos repositorios. Instalando manualmente..."
    
    # Detectar arquitetura
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) RESTIC_ARCH="amd64" ;;
        aarch64) RESTIC_ARCH="arm64" ;;
        armv7l) RESTIC_ARCH="arm" ;;
        *) log_error "Arquitetura nao suportada: $ARCH"; exit 1 ;;
    esac
    
    # Baixar e instalar Restic
    RESTIC_VERSION="0.16.4"
    RESTIC_URL="https://github.com/restic/restic/releases/download/v${RESTIC_VERSION}/restic_${RESTIC_VERSION}_linux_${RESTIC_ARCH}.bz2"
    
    log_info "Baixando Restic v$RESTIC_VERSION para $RESTIC_ARCH..."
    if curl -L "$RESTIC_URL" | bunzip2 > /tmp/restic; then
        chmod +x /tmp/restic
        sudo mv /tmp/restic /usr/local/bin/restic
        log_success "Restic instalado: $(restic version)"
    else
        log_error "Falha ao baixar/instalar Restic"
        exit 1
    fi
}





log_info "=== SETUP SAFESTIC PARA LINUX ==="
log_info "Detectando distribuicao..."

detect_distro

# Lista de pacotes basicos necessarios
BASIC_PACKAGES="git make python3 python3-pip curl bzip2"

# Ajustar nomes de pacotes por distribuicao
case $DISTRO in
    ubuntu|debian)
        PACKAGES="$BASIC_PACKAGES python3-venv"
        ;;
    fedora|centos|rhel)
        PACKAGES="$BASIC_PACKAGES python3-devel"
        ;;
    arch|manjaro)
        PACKAGES="git make python python-pip curl bzip2"
        ;;
    opensuse*)
        PACKAGES="$BASIC_PACKAGES python3-devel"
        ;;
    *)
        PACKAGES="$BASIC_PACKAGES"
        ;;
esac

# Verificar se ja estao instalados
log_info "Verificando dependencias..."

MISSING_PACKAGES=""
TOOLS_TO_CHECK=("git" "make" "python3")

for tool in "${TOOLS_TO_CHECK[@]}"; do
    if ! check_command "$tool"; then
        case $tool in
            python3)
                if [ "$DISTRO" = "arch" ] || [ "$DISTRO" = "manjaro" ]; then
                    MISSING_PACKAGES="$MISSING_PACKAGES python"
                else
                    MISSING_PACKAGES="$MISSING_PACKAGES python3"
                fi
                ;;
            *)
                MISSING_PACKAGES="$MISSING_PACKAGES $tool"
                ;;
        esac
    fi
done

# Verificar pip separadamente
if ! check_command pip3 && ! check_command pip; then
    if [ "$DISTRO" = "arch" ] || [ "$DISTRO" = "manjaro" ]; then
        MISSING_PACKAGES="$MISSING_PACKAGES python-pip"
    else
        MISSING_PACKAGES="$MISSING_PACKAGES python3-pip"
    fi
fi

if [ -n "$MISSING_PACKAGES" ]; then
    log_warning "Pacotes faltando:$MISSING_PACKAGES"
    install_packages "$PACKAGES"
else
    log_success "Todas as dependencias basicas ja estao instaladas"
fi

# Verificar versao do Python
PYTHON_CMD="python3"
if [ "$DISTRO" = "arch" ] || [ "$DISTRO" = "manjaro" ]; then
    PYTHON_CMD="python"
fi

if check_command "$PYTHON_CMD"; then
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        log_success "Python $PYTHON_VERSION encontrado"
    else
        log_error "Python 3.10+ necessario. Encontrado: $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python nao encontrado apos instalacao"
    exit 1
fi

# Instalar Restic
install_restic

# Funcao para criar ambiente virtual
setup_virtual_environment() {
    local python_cmd="$1"
    local venv_path=".venv"
    
    log_info "Criando ambiente virtual em $venv_path..."
    
    if $python_cmd -m venv "$venv_path"; then
        log_success "Ambiente virtual criado com sucesso"
        
        # Ativar ambiente virtual
        source "$venv_path/bin/activate"
        
        # Atualizar pip no ambiente virtual
        log_info "Atualizando pip no ambiente virtual..."
        pip install --upgrade pip
        
        log_success "Ambiente virtual configurado e ativado"
        return 0
    else
        log_error "Falha ao criar ambiente virtual"
        return 1
    fi
}

# Instalar dependencias Python do projeto
log_info "Instalando dependencias Python do projeto..."

# Usar pip3 se disponivel, senao pip
PIP_CMD="pip3"
if ! check_command pip3; then
    PIP_CMD="pip"
fi

# Verificar se ambiente virtual ja existe
VENV_ACTIVATED=false
if [ -f ".venv/bin/activate" ]; then
    log_info "Ambiente virtual existente encontrado. Ativando..."
    source ".venv/bin/activate"
    VENV_ACTIVATED=true
    PIP_CMD="pip"  # Usar pip do ambiente virtual
else
    # Verificar se o ambiente e gerenciado externamente
    log_info "Verificando se ambiente Python e gerenciado externamente..."
    
    # Tentar uma instalacao de teste simples
    if ! $PIP_CMD install --dry-run --quiet pip >/dev/null 2>&1; then
        # Se falhou, verificar se e por ambiente gerenciado
        if $PIP_CMD install --dry-run pip 2>&1 | grep -q "externally-managed-environment"; then
            log_warning "Ambiente Python gerenciado externamente detectado"
            log_info "Sera criado um ambiente virtual para evitar conflitos"
            
            if setup_virtual_environment "$PYTHON_CMD"; then
                VENV_ACTIVATED=true
                PIP_CMD="pip"  # Usar pip do ambiente virtual
            else
                log_error "Falha ao configurar ambiente virtual"
                log_info "Tentando instalacao com --break-system-packages (nao recomendado)"
                PIP_CMD="$PIP_CMD --break-system-packages"
            fi
        else
            # Outro tipo de erro, verificar arquivo EXTERNALLY-MANAGED
            local python_path=$($PYTHON_CMD -c "import sys; print(sys.prefix)" 2>/dev/null)
            if [ -f "$python_path/EXTERNALLY-MANAGED" ]; then
                log_warning "Arquivo EXTERNALLY-MANAGED detectado"
                log_info "Sera criado um ambiente virtual para evitar conflitos"
                
                if setup_virtual_environment "$PYTHON_CMD"; then
                    VENV_ACTIVATED=true
                    PIP_CMD="pip"  # Usar pip do ambiente virtual
                else
                    log_error "Falha ao configurar ambiente virtual"
                    log_info "Tentando instalacao com --break-system-packages (nao recomendado)"
                    PIP_CMD="$PIP_CMD --break-system-packages"
                fi
            fi
        fi
    else
        log_info "Ambiente Python permite instalacoes globais"
    fi
fi

if [ -f "pyproject.toml" ]; then
    log_info "Detectado pyproject.toml. Instalando dependencias..."
    if $PIP_CMD install -e .; then
        log_success "Dependencias do pyproject.toml instaladas"
        if [ "$VENV_ACTIVATED" = true ]; then
            log_info "Dependencias instaladas no ambiente virtual .venv"
            log_warning "Para usar o projeto, ative o ambiente virtual: source .venv/bin/activate"
        fi
    else
        log_error "Falha ao instalar dependencias do pyproject.toml"
        exit 1
    fi
elif [ -f "requirements.txt" ]; then
    log_info "Detectado requirements.txt. Instalando dependencias..."
    local install_cmd="$PIP_CMD install -r requirements.txt"
    if [ "$VENV_ACTIVATED" = false ]; then
        install_cmd="$install_cmd --user"
    fi
    
    if $install_cmd; then
        log_success "Dependencias do requirements.txt instaladas"
        if [ "$VENV_ACTIVATED" = true ]; then
            log_info "Dependencias instaladas no ambiente virtual .venv"
            log_warning "Para usar o projeto, ative o ambiente virtual: source .venv/bin/activate"
        fi
    else
        log_error "Falha ao instalar dependencias do requirements.txt"
        exit 1
    fi
else
    log_warning "Nenhum arquivo de dependencias encontrado (pyproject.toml ou requirements.txt)"
fi

# Verificacao final
log_info "=== VERIFICACAO FINAL ==="

TOOLS=("git --version" "make --version" "$PYTHON_CMD --version" "$PIP_CMD --version" "restic version")
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
    log_warning "Pode ser necessario reiniciar o terminal ou verificar o PATH"
    exit 1
fi

log_success "=== SETUP CONCLUIDO COM SUCESSO ==="
log_info "Todas as dependencias foram instaladas e verificadas!"
log_info "Proximos passos:"
log_info "1. Configure o arquivo .env baseado no .env.example"
log_info "2. Execute: make init"
log_info "3. Execute: make backup"
