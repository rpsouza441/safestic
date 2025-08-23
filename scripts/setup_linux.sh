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

# Determinar comando sudo (ou vazio se rodando como root)
SUDO="sudo"
if ! check_command sudo; then
    if [ "$EUID" -eq 0 ]; then
        SUDO=""
    else
        log_error "sudo nao encontrado. Instale o sudo ou execute como root"
        exit 1
    fi
fi

install_packages() {
    local packages="$1"
    local install_cmd=""
    
    case $DISTRO in
        ubuntu|debian)
            log_info "Atualizando lista de pacotes..."
            $SUDO apt update
            install_cmd="$SUDO apt install"
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd -y"
            fi
            ;;
        fedora|centos|rhel)
            if check_command dnf; then
                install_cmd="$SUDO dnf install"
            elif check_command yum; then
                install_cmd="$SUDO yum install"
            fi
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd -y"
            fi
            ;;
        arch|manjaro)
            install_cmd="$SUDO pacman -S"
            if [ "$ASSUME_YES" = true ]; then
                install_cmd="$install_cmd --noconfirm"
            fi
            ;;
        opensuse*)
            install_cmd="$SUDO zypper install"
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
                local cmd="$SUDO apt install restic"
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
                local cmd="$SUDO dnf install restic"
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
                local cmd="$SUDO pacman -S restic"
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
        $SUDO mv /tmp/restic /usr/local/bin/restic
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
        PACKAGES="$BASIC_PACKAGES python3-venv python3-dev libdbus-glib-1-dev gnome-keyring pkg-config cmake build-essential libdbus-1-dev"
        ;;
    fedora|centos|rhel)
        PACKAGES="$BASIC_PACKAGES python3-devel dbus-glib-devel gnome-keyring pkgconf cmake gcc-c++ dbus-devel"
        ;;
    arch|manjaro)
        PACKAGES="git make python python-pip curl bzip2 python-devel dbus-glib gnome-keyring pkgconf cmake base-devel dbus"
        ;;
    opensuse*)
        PACKAGES="$BASIC_PACKAGES python3-devel dbus-1-glib-devel gnome-keyring pkg-config cmake gcc-c++ dbus-1-devel"
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

# Funcao para detectar ambiente Python gerenciado externamente
check_externally_managed() {
    local python_cmd="$1"
    local pip_cmd="$2"
    
    # Verificar se existe arquivo EXTERNALLY-MANAGED
    local python_path=$($python_cmd -c "import sys; print(sys.prefix)" 2>/dev/null)
    if [ -f "$python_path/EXTERNALLY-MANAGED" ]; then
        return 0  # Ambiente gerenciado
    fi
    
    # Testar instalacao simples para detectar restricoes
    if $pip_cmd install --dry-run pip 2>&1 | grep -q "externally-managed-environment"; then
        return 0  # Ambiente gerenciado
    fi
    
    # Verificar distribuicoes conhecidas com restricoes
    if [ "$DISTRO" = "debian" ] || [ "$DISTRO" = "ubuntu" ]; then
        # Debian 12+ e Ubuntu 24+ tem ambientes gerenciados por padrao
        local version_major=$(echo "$VERSION" | cut -d. -f1)
        if [ "$DISTRO" = "debian" ] && [ "$version_major" -ge 12 ]; then
            return 0  # Ambiente gerenciado
        elif [ "$DISTRO" = "ubuntu" ] && [ "$version_major" -ge 24 ]; then
            return 0  # Ambiente gerenciado
        fi
    fi
    
    return 1  # Nao gerenciado
}

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
    if check_externally_managed "$PYTHON_CMD" "$PIP_CMD"; then
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
    fi
fi

if [ -f "pyproject.toml" ]; then
    log_info "Detectado pyproject.toml. Instalando dependencias..."
    if $PIP_CMD install -e .; then
        log_success "Dependencias do pyproject.toml instaladas"
        
        # Instalar dependencias opcionais de seguranca se ambiente virtual estiver ativo
        if [ "$VENV_ACTIVATED" = true ]; then
            log_info "Instalando dependencias do keyring para Linux..."
            # Tentar instalar dbus-python e secretstorage primeiro
            if $PIP_CMD install secretstorage; then
                log_success "secretstorage instalado com sucesso"
                
                # Tentar instalar dbus-python
                if $PIP_CMD install dbus-python; then
                    log_success "dbus-python instalado com sucesso"
                else
                    log_warning "Falha ao instalar dbus-python. Tentando alternativa keyrings.alt..."
                    if $PIP_CMD install keyrings.alt; then
                        log_success "keyrings.alt instalado como alternativa"
                    else
                        log_warning "Falha ao instalar keyrings.alt. Keyring usara backend de fallback"
                    fi
                fi
            else
                log_warning "Falha ao instalar secretstorage. Tentando keyrings.alt..."
                if $PIP_CMD install keyrings.alt; then
                    log_success "keyrings.alt instalado como alternativa"
                else
                    log_warning "Falha ao instalar dependencias base do keyring"
                fi
            fi
            
            log_info "Instalando dependencias opcionais de seguranca (keyring)..."
            if $PIP_CMD install -e ".[security]"; then
                log_success "Dependencias de seguranca instaladas"
            else
                log_warning "Falha ao instalar dependencias de seguranca. Keyring nao estara disponivel."
            fi
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

# Verificar se keyring esta funcionando (apenas se ambiente virtual estiver ativo)
if [ "$VENV_ACTIVATED" = true ]; then
    log_info "Testando funcionalidade do keyring..."
    if python -c "import keyring; print('Keyring backend:', keyring.get_keyring())" 2>/dev/null; then
        log_success "Keyring configurado e funcionando"
    else
        log_warning "Keyring pode nao estar totalmente funcional"
        log_info "Se houver problemas com keyring, tente:"
        log_info "1. Reiniciar a sessao ou executar: dbus-run-session -- sh"
        log_info "2. Inicializar o gnome-keyring: echo 'senha' | gnome-keyring-daemon --unlock"
        log_info "3. Ou usar apenas variaveis de ambiente (.env) como alternativa"
    fi
fi

log_info "Proximos passos:"
log_info "1. Configure o arquivo .env baseado no .env.example"
log_info "2. Execute: make init"
log_info "3. Execute: make backup"
