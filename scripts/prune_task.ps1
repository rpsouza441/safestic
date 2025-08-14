# Script de prune automatizado para Windows
# Executa limpeza de snapshots antigos e verificacao usando Python diretamente
# Uso: .\scripts\prune_task.ps1

param(
    [string]$LogFile = "logs\prune_task.log"
)

# Configuracoes
$ProjectDir = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectDir ".venv\Scripts\Activate.ps1"
$LogDir = Join-Path $ProjectDir "logs"
$FullLogPath = Join-Path $ProjectDir $LogFile

# Criar diretorio de logs se nao existir
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Funcao de log
function Write-TaskLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $FullLogPath -Value $logEntry
}

try {
    Write-TaskLog "=== INICIANDO PRUNE AUTOMATIZADO ===" "INFO"
    
    # Mudar para diretorio do projeto
    Set-Location $ProjectDir
    Write-TaskLog "Diretorio de trabalho: $ProjectDir" "INFO"
    
    # Ativar ambiente virtual se existir
    if (Test-Path $VenvPath) {
        Write-TaskLog "Ativando ambiente virtual..." "INFO"
        & $VenvPath
    } else {
        Write-TaskLog "Ambiente virtual nao encontrado, usando Python global" "WARN"
    }
    
    # Executar prune
    Write-TaskLog "Executando limpeza de snapshots antigos..." "INFO"
    $pruneResult = & python "manual_prune.py" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-TaskLog "Prune concluido com sucesso" "SUCCESS"
        Write-TaskLog "Saida do prune: $pruneResult" "INFO"
    } else {
        Write-TaskLog "Falha no prune. Codigo de saida: $LASTEXITCODE" "ERROR"
        Write-TaskLog "Erro: $pruneResult" "ERROR"
        throw "Prune falhou"
    }
    
    # Executar verificacao
    Write-TaskLog "Executando verificacao do repositorio..." "INFO"
    $checkResult = & python "check_restic_access.py" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-TaskLog "Verificacao concluida com sucesso" "SUCCESS"
        Write-TaskLog "Saida da verificacao: $checkResult" "INFO"
    } else {
        Write-TaskLog "Falha na verificacao. Codigo de saida: $LASTEXITCODE" "WARN"
        Write-TaskLog "Erro: $checkResult" "WARN"
    }
    
    Write-TaskLog "=== PRUNE AUTOMATIZADO CONCLUIDO ===" "SUCCESS"
    exit 0
    
} catch {
    Write-TaskLog "Erro critico durante prune: $($_.Exception.Message)" "ERROR"
    Write-TaskLog "=== PRUNE AUTOMATIZADO FALHOU ===" "ERROR"
    exit 1
}