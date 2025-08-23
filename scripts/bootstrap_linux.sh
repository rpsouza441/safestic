#!/bin/bash
# Bootstrap script para Linux - instala todas as dependencias do zero
# Uso: ./scripts/bootstrap_linux.sh [--assume-yes]

set -e

# Configurar cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Flags
ASSUME_YES=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --assume-yes|-y)
            ASSUME_YES=true
            shift
            ;;
        *)
            echo "Uso: $0 [--assume-yes|-y]"
            exit 1
            ;;
    esac
done

function write_status() {
    local message="$1"
    local type="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $type in
        "ERROR")
            echo -e "${RED}[$timestamp] [ERROR] $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] [SUCCESS] $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] [WARNING] $message${NC}"
            ;;
        *)
            echo -e "${CYAN}[$timestamp] [INFO] $message${NC}"
            ;;
    esac
}

function command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determinar comando sudo (ou vazio se rodando como root)
SUDO="sudo"
if ! command_exists sudo; then
    if [[ $EUID -eq 0 ]]; then
        SUDO=""
    else
        write_status "sudo nao encontrado. Instale o sudo ou execute como root." "ERROR"
        exit 1
    fi
fi

function detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID"
    elif command_exists lsb_release; then
        lsb_release -si | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

function install_package() {
    local package="$1"
    local distro="$2"
    
    case $distro in
        ubuntu|debian)
            if $ASSUME_YES; then
                $SUDO apt-get install -y "$package"
            else
                $SUDO apt-get install "$package"
            fi
            ;;
        fedora|rhel|centos)
            if command_exists dnf; then
                if $ASSUME_YES; then
                    $SUDO dnf install -y "$package"
                else
                    $SUDO dnf install "$package"
                fi
            else
                if $ASSUME_YES; then
                    $SUDO yum install -y "$package"
                else
                    $SUDO yum install "$package"
                fi
            fi
            ;;
        arch|manjaro)
            if $ASSUME_YES; then
                $SUDO pacman -S --noconfirm "$package"
            else
                $SUDO pacman -S "$package"
            fi
            ;;
        opensuse*)
            if $ASSUME_YES; then
                $SUDO zypper install -y "$package"
            else
                $SUDO zypper install "$package"
            fi
            ;;
        *)
            write_status "Distribuicao nao suportada: $distro" "ERROR"
            return 1
            ;;
    esac
}

function update_package_manager() {
    local distro="$1"
    
    write_status "Atualizando lista de pacotes..."
    case $distro in
        ubuntu|debian)
            $SUDO apt-get update
            ;;
        fedora|rhel|centos)
            if command_exists dnf; then
                $SUDO dnf check-update || true
            else
                $SUDO yum check-update || true
            fi
            ;;
        arch|manjaro)
            $SUDO pacman -Sy
            ;;
        opensuse*)
            $SUDO zypper refresh
            ;;
    esac
}

function install_restic() {
    local distro="$1"
    
    if command_exists restic; then
        write_status "Restic ja instalado: $(restic version | head -n1)" "SUCCESS"
        return 0
    fi
    
    write_status "Instalando Restic..."
    
    # Tentar instalar via gerenciador de pacotes primeiro
    case $distro in
        ubuntu|debian)
            if install_package "restic" "$distro" 2>/dev/null; then
                write_status "Restic instalado via apt" "SUCCESS"
                return 0
            fi
            ;;
        fedora|rhel|centos)
            if install_package "restic" "$distro" 2>/dev/null; then
                write_status "Restic instalado via dnf/yum" "SUCCESS"
                return 0
            fi
            ;;
        arch|manjaro)
            if install_package "restic" "$distro" 2>/dev/null; then
                write_status "Restic instalado via pacman" "SUCCESS"
                return 0
            fi
            ;;
    esac
    
    # Se falhou, instalar via download direto
    write_status "Instalando Restic via download direto..."
    
    local arch
    case $(uname -m) in
        x86_64) arch="amd64" ;;
        aarch64) arch="arm64" ;;
        armv7l) arch="arm" ;;
        *) 
            write_status "Arquitetura nao suportada: $(uname -m)" "ERROR"
            return 1
            ;;
    esac
    
    local latest_version
    latest_version=$(curl -s https://api.github.com/repos/restic/restic/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
    
    if [[ -z "$latest_version" ]]; then
        write_status "Falha ao obter versao mais recente do Restic" "ERROR"
        return 1
    fi
    
    local download_url="https://github.com/restic/restic/releases/download/${latest_version}/restic_${latest_version#v}_linux_${arch}.bz2"
    local temp_file="/tmp/restic.bz2"
    
    if curl -L -o "$temp_file" "$download_url"; then
        bunzip2 "$temp_file"
        $SUDO mv "/tmp/restic" "/usr/local/bin/restic"
        $SUDO chmod +x "/usr/local/bin/restic"
        write_status "Restic instalado com sucesso: $(restic version | head -n1)" "SUCCESS"
    else
        write_status "Falha ao baixar Restic" "ERROR"
        return 1
    fi
}

function setup_python_environment() {
    write_status "Configurando ambiente Python..."
    
    # Verificar se Python esta instalado
    if ! command_exists python3; then
        write_status "Python3 nao encontrado. Instalando..." "WARNING"
        install_package "python3" "$DISTRO"
    fi
    
    # Verificar se pip esta instalado
    if ! command_exists pip3; then
        write_status "pip3 nao encontrado. Instalando..." "WARNING"
        case $DISTRO in
            ubuntu|debian)
                install_package "python3-pip" "$DISTRO"
                ;;
            *)
                install_package "python3-pip" "$DISTRO"
                ;;
        esac
    fi
    
    # Verificar se venv esta disponivel
    if ! python3 -m venv --help >/dev/null 2>&1; then
        write_status "python3-venv nao encontrado. Instalando..." "WARNING"
        case $DISTRO in
            ubuntu|debian)
                install_package "python3-venv" "$DISTRO"
                ;;
            fedora|rhel|centos)
                install_package "python3-venv" "$DISTRO"
                ;;
        esac
    fi
    
    # Criar ambiente virtual se nao existir
    if [[ ! -d ".venv" ]]; then
        write_status "Criando ambiente virtual..."
        python3 -m venv .venv
        write_status "Ambiente virtual criado" "SUCCESS"
    else
        write_status "Ambiente virtual ja existe" "SUCCESS"
    fi
    
    # Ativar ambiente virtual e instalar dependencias
    write_status "Ativando ambiente virtual e instalando dependencias..."
    source .venv/bin/activate
    
    # Atualizar pip
    write_status "Atualizando pip..."
    python -m pip install --upgrade pip
    
    # Instalar dependencias
    if [[ -f "requirements.txt" ]]; then
        write_status "Instalando dependencias do requirements.txt..."
        pip install -r requirements.txt
        if [[ $? -eq 0 ]]; then
            write_status "Dependencias instaladas com sucesso" "SUCCESS"
        else
            write_status "Falha ao instalar dependencias" "ERROR"
            exit 1
        fi
    elif [[ -f "pyproject.toml" ]]; then
        write_status "Instalando dependencias do pyproject.toml..."
        pip install -e .
        if [[ $? -eq 0 ]]; then
            write_status "Dependencias instaladas com sucesso" "SUCCESS"
        else
            write_status "Falha ao instalar dependencias" "ERROR"
            exit 1
        fi
    else
        write_status "Nenhum arquivo de dependencias encontrado" "WARNING"
    fi
}

write_status "=== BOOTSTRAP SAFESTIC PARA LINUX ==="
write_status "Verificando e instalando dependencias..."

# Detectar distribuicao
DISTRO=$(detect_distro)
write_status "Distribuicao detectada: $DISTRO"

# Verificar se esta executando como root
if [[ $EUID -eq 0 ]]; then
    write_status "Executando como root" "WARNING"
    write_status "Recomenda-se executar como usuario normal" "WARNING"
fi

# Atualizar gerenciador de pacotes
update_package_manager "$DISTRO"

# Instalar dependencias basicas
write_status "Instalando dependencias basicas..."
case $DISTRO in
    ubuntu|debian)
        install_package "curl" "$DISTRO"
        install_package "wget" "$DISTRO"
        install_package "git" "$DISTRO"
        install_package "make" "$DISTRO"
        install_package "python3" "$DISTRO"
        install_package "python3-pip" "$DISTRO"
        install_package "python3-venv" "$DISTRO"
        ;;
    fedora|rhel|centos)
        install_package "curl" "$DISTRO"
        install_package "wget" "$DISTRO"
        install_package "git" "$DISTRO"
        install_package "make" "$DISTRO"
        install_package "python3" "$DISTRO"
        install_package "python3-pip" "$DISTRO"
        install_package "python3-venv" "$DISTRO" 2>/dev/null || true
        ;;
    arch|manjaro)
        install_package "curl" "$DISTRO"
        install_package "wget" "$DISTRO"
        install_package "git" "$DISTRO"
        install_package "make" "$DISTRO"
        install_package "python" "$DISTRO"
        install_package "python-pip" "$DISTRO"
        ;;
    opensuse*)
        install_package "curl" "$DISTRO"
        install_package "wget" "$DISTRO"
        install_package "git" "$DISTRO"
        install_package "make" "$DISTRO"
        install_package "python3" "$DISTRO"
        install_package "python3-pip" "$DISTRO"
        install_package "python3-venv" "$DISTRO"
        ;;
esac

# Verificar instalacoes
if command_exists git; then
    write_status "Git ja instalado: $(git --version)" "SUCCESS"
else
    write_status "Falha ao instalar Git" "ERROR"
    exit 1
fi

if command_exists make; then
    write_status "Make ja instalado: $(make --version | head -n1)" "SUCCESS"
else
    write_status "Falha ao instalar Make" "ERROR"
    exit 1
fi

if command_exists python3; then
    write_status "Python3 ja instalado: $(python3 --version)" "SUCCESS"
else
    write_status "Falha ao instalar Python3" "ERROR"
    exit 1
fi

# Instalar Restic
install_restic "$DISTRO"

# Configurar ambiente Python
setup_python_environment

# Chamar setup adicional
write_status "Chamando setup adicional do Linux..."
if [[ -f "scripts/setup_linux.sh" ]]; then
    setup_args=""
    if $ASSUME_YES; then
        setup_args="--assume-yes"
    fi
    bash scripts/setup_linux.sh $setup_args
    write_status "Setup adicional concluido com sucesso!" "SUCCESS"
else
    write_status "Script setup_linux.sh nao encontrado" "WARNING"
fi

write_status "=== BOOTSTRAP CONCLUIDO ===" "SUCCESS"
write_status "Todas as dependencias foram instaladas com sucesso!" "SUCCESS"
write_status ""
write_status "COMPONENTES INSTALADOS:" 
write_status "[OK] Git" "SUCCESS"
write_status "[OK] GNU Make" "SUCCESS"
write_status "[OK] Python 3" "SUCCESS"
write_status "[OK] Restic (backup tool)" "SUCCESS"
write_status "[OK] Ambiente virtual Python (.venv)" "SUCCESS"
write_status "[OK] Dependencias Python instaladas" "SUCCESS"
write_status ""
write_status "PROXIMOS PASSOS:"
write_status "1. Reinicie o terminal se necessario"
write_status "2. Configure o arquivo .env baseado no .env.example"
write_status "3. Execute: make init (para inicializar repositorio)"
write_status "4. Execute: make validate-setup (para validar tudo)"
write_status "5. Execute: make backup (para fazer primeiro backup)"
write_status ""
write_status "DICAS:"
write_status "- Use 'make health' para verificar o sistema"
write_status "- Use 'make help' para ver todos os comandos"
write_status "- O ambiente virtual esta em .venv/"