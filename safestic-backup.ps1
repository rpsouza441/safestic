# Script PowerShell para execução de backup Safestic no Windows
# Para uso com Task Scheduler

param(
    [string]$Action = "backup",
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# Configurar localização e encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Função para log com timestamp
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN"  { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage -ForegroundColor White }
    }
    
    # Log para arquivo se diretório existir
    if (Test-Path "logs") {
        $logFile = "logs\safestic-powershell-$(Get-Date -Format 'yyyyMMdd').log"
        Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
    }
}

# Verificar se estamos no diretório correto
if (-not (Test-Path "Makefile")) {
    Write-Log "Makefile não encontrado. Execute este script no diretório do projeto Safestic." "ERROR"
    exit 1
}

# Verificar se ambiente virtual existe
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Log "Ambiente virtual não encontrado. Execute o setup primeiro." "ERROR"
    Write-Log "Execute: .\scripts\setup_windows.sh" "INFO"
    exit 1
}

try {
    Write-Log "Iniciando execução do Safestic - Ação: $Action" "INFO"
    
    # Ativar ambiente virtual
    Write-Log "Ativando ambiente virtual..." "INFO"
    & .\venv\Scripts\activate.ps1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao ativar ambiente virtual"
    }
    
    # Verificar se Make está disponível
    $makeCommand = Get-Command "make" -ErrorAction SilentlyContinue
    if (-not $makeCommand) {
        Write-Log "Make não encontrado no PATH. Tentando usar mingw32-make..." "WARN"
        $makeCommand = Get-Command "mingw32-make" -ErrorAction SilentlyContinue
        if (-not $makeCommand) {
            throw "Make não encontrado. Instale GNU Make ou execute o setup."
        }
        $makeExe = "mingw32-make"
    } else {
        $makeExe = "make"
    }
    
    # Executar ação solicitada
    switch ($Action.ToLower()) {
        "backup" {
            if ($DryRun) {
                Write-Log "Executando simulação de backup (dry-run)..." "INFO"
                & $makeExe dry-run
            } else {
                Write-Log "Executando backup..." "INFO"
                & $makeExe backup
            }
        }
        "check" {
            Write-Log "Verificando configuração..." "INFO"
            & $makeExe check
        }
        "list" {
            Write-Log "Listando snapshots..." "INFO"
            & $makeExe list
        }
        "stats" {
            Write-Log "Obtendo estatísticas..." "INFO"
            & $makeExe stats
        }
        "validate" {
            Write-Log "Executando validação completa..." "INFO"
            & $makeExe validate
        }
        "init" {
            Write-Log "Inicializando repositório..." "INFO"
            & $makeExe init
        }
        "health" {
            Write-Log "Verificando saúde do backup..." "INFO"
            if (Test-Path "check-backup-health.sh") {
                & bash check-backup-health.sh
            } else {
                Write-Log "Script de verificação de saúde não encontrado" "ERROR"
                exit 1
            }
        }
        default {
            Write-Log "Ação não reconhecida: $Action" "ERROR"
            Write-Log "Ações disponíveis: backup, check, list, stats, validate, init, health" "INFO"
            exit 1
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Ação '$Action' executada com sucesso!" "SUCCESS"
    } else {
        throw "Ação '$Action' falhou com código de saída: $LASTEXITCODE"
    }
    
} catch {
    Write-Log "Erro durante execução: $($_.Exception.Message)" "ERROR"
    Write-Log "Detalhes: $($_.ScriptStackTrace)" "ERROR" 
    exit 1
} finally {
    # Desativar ambiente virtual (se necessário)
    if ($env:VIRTUAL_ENV) {
        Write-Log "Desativando ambiente virtual..." "INFO"
        deactivate 2>$null
    }
}

Write-Log "Execução concluída." "INFO"