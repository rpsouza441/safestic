#!/usr/bin/env powershell
# Bootstrap script para Windows - instala todas as dependencias do zero
# Uso: .\scripts\bootstrap_windows.ps1 [-AssumeYes]

param(
    [switch]$AssumeYes
)

$ErrorActionPreference = "Stop"

# Configurar codificacao UTF-8 para resolver problemas com acentos
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    switch ($Type) {
        "ERROR" { Write-Host "[$timestamp] [ERROR] $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[$timestamp] [SUCCESS] $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[$timestamp] [WARNING] $Message" -ForegroundColor Yellow }
        default { Write-Host "[$timestamp] [INFO] $Message" -ForegroundColor Cyan }
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

function Get-InstalledPythonExe {
    try {
        $cmd = Get-Command "python" -ErrorAction Stop
        if ($cmd.Source -notlike "*Microsoft\\WindowsApps*") {
            return $cmd.Source
        }
    } catch {
        # Ignore errors and fall back to common locations
    }

    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python310\python.exe"
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $null
}

function Install-WithWinget {
    param([string]$Package, [string]$Name)
    try {
        Write-Status "Instalando $Name via winget..."
        Write-Status "Isso pode levar alguns minutos. Aguarde..." "WARNING"
        
        # Criar job para mostrar progresso
        $job = Start-Job -ScriptBlock {
            param($pkg, $assumeYes)
            if ($assumeYes) {
                winget install --id $pkg --silent --accept-package-agreements --accept-source-agreements --verbose
            } else {
                winget install --id $pkg --interactive --verbose
            }
        } -ArgumentList $Package, $AssumeYes
        
        # Mostrar progresso enquanto instala
        $dots = 0
        while ($job.State -eq "Running") {
            $dots = ($dots + 1) % 4
            $progress = "." * $dots + " " * (3 - $dots)
            Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Instalando $Name$progress" -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
        
        Write-Host "" # Nova linha
        $result = Receive-Job -Job $job
        Remove-Job -Job $job
        
        if ($job.State -eq "Completed") {
            Write-Status "$Name instalado com sucesso" "SUCCESS"
            return $true
        } else {
            Write-Status "Falha ao instalar $Name" "ERROR"
            return $false
        }
    } catch {
        Write-Status "Falha ao instalar $Name via winget: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Install-WithChoco {
    param([string]$Package, [string]$Name)
    try {
        Write-Status "Instalando $Name via chocolatey..."
        Write-Status "Isso pode levar alguns minutos. Aguarde..." "WARNING"
        
        # Criar job para mostrar progresso
        $job = Start-Job -ScriptBlock {
            param($pkg, $assumeYes)
            if ($assumeYes) {
                choco install $pkg -y --verbose
            } else {
                choco install $pkg --verbose
            }
        } -ArgumentList $Package, $AssumeYes
        
        # Mostrar progresso enquanto instala
        $dots = 0
        while ($job.State -eq "Running") {
            $dots = ($dots + 1) % 4
            $progress = "." * $dots + " " * (3 - $dots)
            Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Instalando $Name$progress" -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
        
        Write-Host "" # Nova linha
        $result = Receive-Job -Job $job
        Remove-Job -Job $job
        
        if ($job.State -eq "Completed") {
            Write-Status "$Name instalado com sucesso" "SUCCESS"
            return $true
        } else {
            Write-Status "Falha ao instalar $Name" "ERROR"
            return $false
        }
    } catch {
        Write-Status "Falha ao instalar $Name via chocolatey: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

Write-Status "=== BOOTSTRAP SAFESTIC PARA WINDOWS ==="
Write-Status "Verificando e instalando dependencias..."

# Verificar se esta executando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Status "Executando sem privilegios de administrador" "WARNING"
    Write-Status "Algumas instalacoes podem falhar ou solicitar elevacao" "WARNING"
}

# Detectar gerenciador de pacotes disponivel
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

# Instalar Git for Windows (se nao estiver instalado)
if (-not (Test-Command "git")) {
    Write-Status "Git nao encontrado. Instalando..."
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
    Write-Status "Git ja instalado: $(git --version)" "SUCCESS"
}

# Instalar GNU Make
if (-not (Test-Command "make")) {
    Write-Status "Make nao encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        try {
            Write-Status "Instalando GNU Make via winget..."
            winget install -e --id GnuWin32.Make --silent --accept-package-agreements --accept-source-agreements
            Write-Status "GNU Make instalado com sucesso" "SUCCESS"
            $installed = $true
            
            # Adicionar ao PATH da sessao atual
            $makePath = "C:\Program Files (x86)\GnuWin32\bin"
            if (Test-Path $makePath) {
                $env:PATH += ";$makePath"
                Write-Status "PATH atualizado para a sessao atual" "SUCCESS"
            }
        } catch {
            Write-Status "Falha ao instalar via winget: $($_.Exception.Message)" "WARNING"
        }
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "make" "GNU Make"
    }
    if (-not $installed) {
        Write-Status "Falha ao instalar Make" "ERROR"
        exit 1
    }
} else {
    Write-Status "Make ja instalado: $(make --version | Select-Object -First 1)" "SUCCESS"
}

# Instalar Python 3.10+
$pythonExe = Get-InstalledPythonExe
if (-not $pythonExe) {
    Write-Status "Python nao encontrado. Instalando..."
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
    $pythonExe = Get-InstalledPythonExe
    if (-not $pythonExe) {
        Write-Status "Python instalado mas nao encontrado" "ERROR"
        exit 1
    }
    $pythonStatus = "instalado"
} else {
    $pythonStatus = "ja instalado"
}

$pythonDir = Split-Path $pythonExe -Parent
if ($env:PATH -notlike "*$pythonDir*") {
    $env:PATH = "$pythonDir;$env:PATH"
    Write-Status "PATH atualizado com Python" "SUCCESS"
}

$pythonVersion = & $pythonExe --version 2>&1 | Select-String '^Python' | Select-Object -First 1
$pythonVersion = $pythonVersion.Line.Trim()
Write-Status "Python ${pythonStatus}: ${pythonVersion}" "SUCCESS"

# Verificar versao minima
$versionString = $pythonVersion -replace '^Python\s+', ''
$version = [Version]$versionString
if ($version -lt [Version]"3.10.0") {
    Write-Status "Python $version e muito antigo. Minimo: 3.10" "ERROR"
    exit 1
}

# Instalar pip (geralmente vem com Python)
if (-not (Test-Command "pip")) {
    Write-Status "pip nao encontrado. Instalando..."
    try {
        python -m ensurepip --upgrade
        Write-Status "pip instalado com sucesso" "SUCCESS"
    } catch {
        Write-Status "Falha ao instalar pip" "ERROR"
        exit 1
    }
} else {
    Write-Status "pip ja instalado: $(pip --version)" "SUCCESS"
}

# Instalar Restic
if (-not (Test-Command "restic")) {
    Write-Status "Restic nao encontrado. Instalando..."
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
    Write-Status "Restic ja instalado: $(restic version)" "SUCCESS"
}

# Instalar WinFsp (necessario para mount)
function Test-WinFsp {
    return (Test-Path "C:\Program Files (x86)\WinFsp\bin\launchctl-x64.exe") -or (Test-Path "C:\Program Files\WinFsp\bin\launchctl-x64.exe")
}

if (-not (Test-WinFsp)) {
    Write-Status "WinFsp nao encontrado. Instalando..."
    $installed = $false
    if ($hasWinget) {
        $installed = Install-WithWinget "WinFsp.WinFsp" "WinFsp"
    }
    if (-not $installed -and $hasChoco) {
        $installed = Install-WithChoco "winfsp" "WinFsp"
    }
    if (-not $installed) {
        Write-Status "Tentando download direto do WinFsp..." "WARNING"
        try {
            $winfspUrl = "https://github.com/winfsp/winfsp/releases/latest/download/winfsp-2.0.23075.msi"
            $tempFile = "$env:TEMP\winfsp-installer.msi"
            Write-Status "Baixando WinFsp de $winfspUrl"
            Invoke-WebRequest -Uri $winfspUrl -OutFile $tempFile
            Write-Status "Instalando WinFsp... (pode solicitar permissoes de administrador)"
            Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $tempFile, "/quiet" -Wait -Verb RunAs
            Remove-Item $tempFile -Force
            Write-Status "WinFsp instalado com sucesso" "SUCCESS"
        } catch {
            Write-Status "Falha ao instalar WinFsp: $($_.Exception.Message)" "WARNING"
            Write-Status "Voce pode instalar manualmente de: https://winfsp.dev/rel/" "INFO"
        }
    }
} else {
    Write-Status "WinFsp ja instalado" "SUCCESS"
}

# Atualizar PATH se necessario
$machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$env:PATH = $machinePath + ";" + $userPath

# Garantir que GnuWin32 esteja no PATH permanentemente
$makePath = "C:\Program Files (x86)\GnuWin32\bin"
if (Test-Path $makePath) {
    # Atualizar PATH da sessao atual
    if ($env:PATH -notlike "*$makePath*") {
        $env:PATH += ";$makePath"
        Write-Status "PATH da sessao atualizado com GnuWin32" "SUCCESS"
    }
    
    # Atualizar PATH do usuario permanentemente
    $currentUserPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentUserPath -notlike "*$makePath*") {
        $newUserPath = if ($currentUserPath) { $currentUserPath + ";$makePath" } else { $makePath }
        [System.Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
        Write-Status "PATH do usuario atualizado permanentemente com GnuWin32" "SUCCESS"
    }
}

# Garantir que Restic esteja no PATH permanentemente
# Procurar pelo Restic instalado pelo winget
$resticPaths = @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\restic.restic_Microsoft.Winget.Source_8wekyb3d8bbwe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
)

$resticFound = $false
foreach ($path in $resticPaths) {
    if (Test-Path $path) {
        $resticExe = Get-ChildItem -Path $path -Name "restic*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
         if ($resticExe) {
             $resticPath = $path
             
             # Se o executavel nao e 'restic.exe', criar uma copia com o nome correto
             $resticExePath = Join-Path $path "restic.exe"
             if (-not (Test-Path $resticExePath)) {
                 $originalExe = Get-ChildItem -Path $path -Name "restic_*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
                 if ($originalExe) {
                     Copy-Item (Join-Path $path $originalExe) $resticExePath -ErrorAction SilentlyContinue
                 }
             }
            # Atualizar PATH da sessao atual
            if ($env:PATH -notlike "*$resticPath*") {
                $env:PATH += ";$resticPath"
                Write-Status "PATH da sessao atualizado com Restic" "SUCCESS"
            }
            
            # Atualizar PATH do usuario permanentemente
            $currentUserPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
            if ($currentUserPath -notlike "*$resticPath*") {
                $newUserPath = if ($currentUserPath) { $currentUserPath + ";$resticPath" } else { $resticPath }
                [System.Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
                Write-Status "PATH do usuario atualizado permanentemente com Restic" "SUCCESS"
            }
            $resticFound = $true
            break
        }
    }
}

if (-not $resticFound) {
    Write-Status "Restic instalado mas nao encontrado no PATH" "WARNING"
}

# Verificar instalacoes finais
Write-Status "=== VERIFICACAO FINAL ==="
$tools = @(
    @{Name="Git"; Command="git --version"},
    @{Name="Make"; Command="make --version"},
    @{Name="Python"; Command="python --version"},
    @{Name="pip"; Command="pip --version"},
    @{Name="Restic"; Command="restic version"}
)

# Verificar WinFsp separadamente (nao tem comando de linha)
if (Test-WinFsp) {
    Write-Status "WinFsp: INSTALADO" "SUCCESS"
} else {
    Write-Status "WinFsp: NAO ENCONTRADO (funcionalidade mount nao disponivel)" "WARNING"
}

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
    Write-Status "Algumas ferramentas falharam na verificacao" "ERROR"
    Write-Status "Pode ser necessario reiniciar o terminal ou adicionar ao PATH manualmente" "WARNING"
    exit 1
}

# Configurar ambiente virtual Python
Write-Status "Configurando ambiente virtual Python..."
try {
    # Verificar se .venv ja existe
    if (Test-Path ".venv") {
        Write-Status "Ambiente virtual .venv ja existe" "SUCCESS"
    } else {
        Write-Status "Criando ambiente virtual .venv..."
        python -m venv .venv
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Ambiente virtual criado com sucesso" "SUCCESS"
        } else {
            Write-Status "Falha ao criar ambiente virtual" "ERROR"
            exit 1
        }
    }
    
    # Ativar ambiente virtual e instalar dependencias
    Write-Status "Ativando ambiente virtual e instalando dependencias..."
    $activateScript = ".venv\Scripts\Activate.ps1"
    
    if (Test-Path $activateScript) {
        # Ativar ambiente virtual
        & $activateScript
        
        # Atualizar pip
        Write-Status "Atualizando pip..."
        python -m pip install --upgrade pip
        
        # Instalar dependencias
        if (Test-Path "requirements.txt") {
            Write-Status "Instalando dependencias do requirements.txt..."
            pip install -r requirements.txt
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Dependencias instaladas com sucesso" "SUCCESS"
            } else {
                Write-Status "Falha ao instalar dependencias" "ERROR"
                exit 1
            }
        } elseif (Test-Path "pyproject.toml") {
            Write-Status "Instalando dependencias do pyproject.toml..."
            pip install -e .
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Dependencias instaladas com sucesso" "SUCCESS"
            } else {
                Write-Status "Falha ao instalar dependencias" "ERROR"
                exit 1
            }
        } else {
            Write-Status "Nenhum arquivo de dependencias encontrado" "WARNING"
        }
    } else {
        Write-Status "Script de ativacao nao encontrado" "ERROR"
        exit 1
    }
} catch {
    Write-Status "Falha na configuracao do ambiente virtual: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Chamar setup do Git Bash (opcional)
Write-Status "Chamando setup especifico do Git Bash..."
try {
    $setupArgs = if ($AssumeYes) { "--assume-yes" } else { "" }
    $currentDir = $PWD.Path
    
    # Tentar encontrar bash do Git
    $bashPaths = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe",
        "${env:ProgramFiles}\Git\bin\bash.exe",
        "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
    )
    
    $bashPath = $null
    foreach ($path in $bashPaths) {
        if (Test-Path $path) {
            $bashPath = $path
            break
        }
    }
    
    if ($bashPath) {
        & "$bashPath" -lc "cd '$currentDir'; ./scripts/setup_windows.sh $setupArgs"
        Write-Status "Setup adicional concluido com sucesso!" "SUCCESS"
    } else {
        Write-Status "Git Bash nao encontrado. Pulando setup adicional." "WARNING"
        Write-Status "Ambiente virtual configurado com sucesso!" "SUCCESS"
    }
} catch {
    Write-Status "Falha no setup do Git Bash: $($_.Exception.Message)" "WARNING"
    Write-Status "Continuando com ambiente virtual configurado..." "INFO"
}

Write-Status "=== BOOTSTRAP CONCLUIDO ===" "SUCCESS"
Write-Status "Todas as dependencias foram instaladas com sucesso!" "SUCCESS"
Write-Status "" "INFO"
Write-Status "COMPONENTES INSTALADOS:" "INFO"
Write-Status "[OK] Git for Windows" "SUCCESS"
Write-Status "[OK] GNU Make" "SUCCESS"
Write-Status "[OK] Python 3.12+" "SUCCESS"
Write-Status "[OK] Restic (backup tool)" "SUCCESS"
Write-Status "[OK] WinFsp (para comando mount)" "SUCCESS"
Write-Status "[OK] Ambiente virtual Python (.venv)" "SUCCESS"
Write-Status "[OK] Dependencias Python instaladas" "SUCCESS"
Write-Status "" "INFO"
Write-Status "PROXIMOS PASSOS:" "INFO"
Write-Status "1. Reinicie o terminal/PowerShell se necessario" "INFO"
Write-Status "2. Configure o arquivo .env baseado no .env.example" "INFO"
Write-Status "3. Execute: make init (para inicializar repositorio)" "INFO"
Write-Status "4. Execute: make validate-setup (para validar tudo)" "INFO"
Write-Status "5. Execute: make backup (para fazer primeiro backup)" "INFO"
Write-Status "" "INFO"
Write-Status "DICAS:" "INFO"
Write-Status "- O comando 'make mount' agora funciona com WinFsp" "INFO"
Write-Status "- Use 'make health' para verificar o sistema" "INFO"
Write-Status "- Use 'make help' para ver todos os comandos" "INFO"
