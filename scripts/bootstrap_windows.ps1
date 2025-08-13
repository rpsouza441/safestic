#!/usr/bin/env powershell
# Bootstrap script para Windows - instala todas as dependências do zero
# Uso: .\scripts\bootstrap_windows.ps1 [-AssumeYes]

param(
    [switch]$AssumeYes
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    switch ($Type) {
        "ERROR" { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        default { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
    }
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Install-WithWinget {
    param([string]$Package, [string]$Name)
    try {
        Write-Status "Instalando $Name via winget..."
        if ($AssumeYes) {
            winget install --id $Package --silent --accept-package-agreements --accept-source-agreements
        } else {
            winget install --id $Package --interactive
        }
        Write-Status "$Name instalado com sucesso" "SUCCESS"
        return $true
    } catch {
        Write-Status "Falha ao instalar $Name via winget: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Install-WithChoco {
    param([string]$Package, [string]$Name)
    try {
        Write-Status "Instalando $Name via chocolatey..."
        if ($AssumeYes) {
            choco install $Package -y
        } else {
            choco install $Package
        }
        Write-Status "$Name instalado com sucesso" "SUCCESS"
        return $true
    } catch {
        Write-Status "Falha ao instalar $Name via chocolatey: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

Write-Status "=== BOOTSTRAP SAFESTIC PARA WINDOWS ==="
Write-Status "Verificando e instalando dependências..."

# Verificar se está executando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Status "Este script precisa ser executado como Administrador" "ERROR"
    Write-Status "Clique com botão direito no PowerShell e selecione 'Executar como Administrador'" "WARNING"
    exit 1
}

# Detectar gerenciador de pacotes disponível
$hasWinget = Test-Command "winget"
$hasChoco = Test-Command "choco"

if (-not $hasWinget -and -not $hasChoco) {
    Write-Status "Instalando winget (App Installer)..." "WARNING"
    try {
        # Instalar winget via Microsoft Store ou GitHub
        $progressPreference = 'silentlyContinue'
        Invoke-WebRequest -Uri "https://aka.ms/getwinget" -OutFile "$env:TEMP\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
        Add-AppxPackage "$env:TEMP\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
        $hasWinget = $true
        Write-Status "Winget instalado com sucesso" "SUCCESS"
    } catch {
        Write-Status "Falha ao instalar winget. Tentando instalar chocolatey..." "WARNING"
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            $hasChoco = $true
            Write-Status "Chocolatey instalado com sucesso" "SUCCESS"
        } catch {
            Write-Status "Falha ao instalar gerenciadores de pacote" "ERROR"
            exit 1
        }
    }
}

# Instalar Git for Windows (se não estiver instalado)
if (-not (Test-Command "git")) {
    Write-Status "Git não encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        $installed = Install-WithWinget "Git.Git" "Git for Windows"
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "git" "Git for Windows"
    }
    if (-not $installed) {
        Write-Status "Falha ao instalar Git" "ERROR"
        exit 1
    }
} else {
    Write-Status "Git já instalado: $(git --version)" "SUCCESS"
}

# Instalar GNU Make
if (-not (Test-Command "make")) {
    Write-Status "Make não encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        $installed = Install-WithWinget "GnuWin32.Make" "GNU Make"
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "make" "GNU Make"
    }
    if (-not $installed) {
        Write-Status "Falha ao instalar Make" "ERROR"
        exit 1
    }
} else {
    Write-Status "Make já instalado: $(make --version | Select-Object -First 1)" "SUCCESS"
}

# Instalar Python 3.10+
if (-not (Test-Command "python")) {
    Write-Status "Python não encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        $installed = Install-WithWinget "Python.Python.3.12" "Python 3.12"
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "python" "Python"
    }
    if (-not $installed) {
        Write-Status "Falha ao instalar Python" "ERROR"
        exit 1
    }
} else {
    $pythonVersion = python --version
    Write-Status "Python já instalado: $pythonVersion" "SUCCESS"
    # Verificar versão mínima
    $version = [Version]($pythonVersion -replace "Python ", "")
    if ($version -lt [Version]"3.10.0") {
        Write-Status "Python $version é muito antigo. Mínimo: 3.10" "ERROR"
        exit 1
    }
}

# Instalar pip (geralmente vem com Python)
if (-not (Test-Command "pip")) {
    Write-Status "pip não encontrado. Instalando..."
    try {
        python -m ensurepip --upgrade
        Write-Status "pip instalado com sucesso" "SUCCESS"
    } catch {
        Write-Status "Falha ao instalar pip" "ERROR"
        exit 1
    }
} else {
    Write-Status "pip já instalado: $(pip --version)" "SUCCESS"
}

# Instalar Restic
if (-not (Test-Command "restic")) {
    Write-Status "Restic não encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        $installed = Install-WithWinget "restic.restic" "Restic"
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "restic" "Restic"
    }
    if (-not $installed) {
        Write-Status "Falha ao instalar Restic" "ERROR"
        exit 1
    }
} else {
    Write-Status "Restic já instalado: $(restic version)" "SUCCESS"
}

# Atualizar PATH se necessário
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

# Verificar instalações finais
Write-Status "=== VERIFICAÇÃO FINAL ==="
$tools = @(
    @{Name="Git"; Command="git --version"},
    @{Name="Make"; Command="make --version"},
    @{Name="Python"; Command="python --version"},
    @{Name="pip"; Command="pip --version"},
    @{Name="Restic"; Command="restic version"}
)

$allOk = $true
foreach ($tool in $tools) {
    try {
        $version = Invoke-Expression $tool.Command
        Write-Status "$($tool.Name): $($version.Split("`n")[0])" "SUCCESS"
    } catch {
        Write-Status "$($tool.Name): FALHOU" "ERROR"
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Status "Algumas ferramentas falharam na verificação" "ERROR"
    Write-Status "Pode ser necessário reiniciar o terminal ou adicionar ao PATH manualmente" "WARNING"
    exit 1
}

# Chamar setup do Git Bash
Write-Status "Chamando setup específico do Git Bash..."
try {
    $setupArgs = if ($AssumeYes) { "--assume-yes" } else { "" }
    bash -lc "cd '$PWD' && ./scripts/setup_windows.sh $setupArgs"
    Write-Status "Setup concluído com sucesso!" "SUCCESS"
} catch {
    Write-Status "Falha no setup do Git Bash: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Status "=== BOOTSTRAP CONCLUÍDO ==="
Write-Status "Todas as dependências foram instaladas com sucesso!" "SUCCESS"
Write-Status "Próximos passos:" "INFO"
Write-Status "1. Reinicie o terminal se necessário" "INFO"
Write-Status "2. Configure o arquivo .env" "INFO"
Write-Status "3. Execute: make init" "INFO"
Write-Status "4. Execute: make backup" "INFO"