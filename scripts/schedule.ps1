# Script de agendamento simplificado para Windows
# Cria tarefas agendadas usando scripts PowerShell diretos
# Uso: .\scripts\schedule_simple.ps1 [install|remove|status] [-AsUser]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "remove", "status")]
    [string]$Action,
    
    [switch]$AsUser = $false
)

# Configuracoes
$ProjectDir = Split-Path -Parent $PSScriptRoot
$ProjectName = "Safestic"
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Carregar APP_NAME do arquivo .env
$EnvFile = Join-Path $ProjectDir ".env"
$AppName = "safestic"  # Valor padrao
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile
    foreach ($line in $envContent) {
        if ($line -match "^APP_NAME=(.+)$") {
            $AppName = $matches[1].Trim('"').Trim("'")
            break
        }
    }
}

# Funcoes de log
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] INFO: $Message" -ForegroundColor Blue
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SUCCESS: $Message" -ForegroundColor Green
}

function Write-LogWarning {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: $Message" -ForegroundColor Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $Message" -ForegroundColor Red
}

# Verificar se esta executando como administrador
function Test-IsAdmin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Criar tarefa de backup simplificada
function New-SimpleBackupTask {
    $taskName = "$ProjectName-Backup-$AppName"
    Write-LogInfo "Criando tarefa de backup simplificada: $taskName"
    
    $backupScript = Join-Path $ProjectDir "scripts\backup_task.ps1"
    
    # Definir acao - executa o script PowerShell diretamente
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$backupScript`""
    
    # Definir trigger (diario as 02:00)
    $trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
    
    # Definir configuracoes basicas
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $settings.ExecutionTimeLimit = "PT2H"  # Timeout de 2 horas
    
    # Definir principal (sempre como usuario atual para evitar problemas de permissao)
    $principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive
    Write-LogInfo "Tarefa sera executada como usuario: $CurrentUser"
    
    # Registrar tarefa
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
        Write-LogSuccess "Tarefa de backup criada com sucesso"
    }
    catch {
        Write-LogError "Falha ao criar tarefa de backup: $($_.Exception.Message)"
        throw
    }
}

# Criar tarefa de prune simplificada
function New-SimplePruneTask {
    $taskName = "$ProjectName-Prune-$AppName"
    Write-LogInfo "Criando tarefa de prune simplificada: $taskName"
    
    $pruneScript = Join-Path $ProjectDir "scripts\prune_task.ps1"
    
    # Definir acao - executa o script PowerShell diretamente
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$pruneScript`""
    
    # Definir trigger (semanal aos domingos as 03:00)
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "03:00AM"
    
    # Definir configuracoes basicas
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $settings.ExecutionTimeLimit = "PT3H"  # Timeout de 3 horas
    
    # Definir principal (sempre como usuario atual para evitar problemas de permissao)
    $principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive
    Write-LogInfo "Tarefa sera executada como usuario: $CurrentUser"
    
    # Registrar tarefa
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
        Write-LogSuccess "Tarefa de prune criada com sucesso"
    }
    catch {
        Write-LogError "Falha ao criar tarefa de prune: $($_.Exception.Message)"
        throw
    }
}

# Instalar tarefas
function Install-SimpleTasks {
    Write-LogInfo "=== INSTALANDO TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    # Verificar se os scripts existem
    $backupScript = Join-Path $ProjectDir "scripts\backup_task.ps1"
    $pruneScript = Join-Path $ProjectDir "scripts\prune_task.ps1"
    
    if (-not (Test-Path $backupScript)) {
        Write-LogError "Script de backup nao encontrado: $backupScript"
        throw "Script de backup nao encontrado"
    }
    
    if (-not (Test-Path $pruneScript)) {
        Write-LogError "Script de prune nao encontrado: $pruneScript"
        throw "Script de prune nao encontrado"
    }
    
    # Criar tarefas
    New-SimpleBackupTask
    New-SimplePruneTask
    
    Write-LogSuccess "=== TAREFAS SIMPLIFICADAS INSTALADAS COM SUCESSO ==="
    Write-LogInfo "Backup: execucao diaria as 02:00"
    Write-LogInfo "Prune: execucao semanal aos domingos as 03:00"
    Write-LogInfo "Logs serao salvos em: logs/backup_task.log e logs/prune_task.log"
}

# Remover tarefas
function Remove-SimpleTasks {
    Write-LogInfo "=== REMOVENDO TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    $taskNames = @("$ProjectName-Backup-$AppName", "$ProjectName-Prune-$AppName")
    
    foreach ($taskName in $taskNames) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Write-LogInfo "Removendo tarefa: $taskName"
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-LogSuccess "Tarefa $taskName removida"
            } else {
                Write-LogWarning "Tarefa $taskName nao encontrada"
            }
        }
        catch {
            Write-LogError "Falha ao remover tarefa ${taskName}: $($_.Exception.Message)"
        }
    }
    
    Write-LogSuccess "=== TAREFAS SIMPLIFICADAS REMOVIDAS COM SUCESSO ==="
}

# Mostrar status das tarefas
function Show-SimpleTaskStatus {
    Write-LogInfo "=== STATUS DAS TAREFAS AGENDADAS SIMPLIFICADAS ==="
    
    $taskNames = @("$ProjectName-Backup-$AppName", "$ProjectName-Prune-$AppName")
    
    foreach ($taskName in $taskNames) {
        Write-Host ""
        Write-LogInfo "Status da tarefa: $taskName"
        
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Write-Host "  Estado: $($task.State)" -ForegroundColor Cyan
                Write-Host "  Ultima execucao: $($task.LastRunTime)" -ForegroundColor Cyan
                Write-Host "  Proxima execucao: $($task.NextRunTime)" -ForegroundColor Cyan
                Write-Host "  Ultimo resultado: $($task.LastTaskResult)" -ForegroundColor Cyan
                
                # Mostrar detalhes do trigger
                $trigger = $task.Triggers[0]
                if ($trigger) {
                    Write-Host "  Agendamento: $($trigger.StartBoundary)" -ForegroundColor Cyan
                }
            } else {
                Write-LogWarning "Tarefa $taskName nao encontrada"
            }
        }
        catch {
            Write-LogError "Erro ao obter status da tarefa ${taskName}: $($_.Exception.Message)"
        }
        
        Write-Host ("-" * 50)
    }
    
    # Mostrar todas as tarefas do Safestic
    Write-LogInfo "Todas as tarefas do $ProjectName":
    try {
        Get-ScheduledTask -TaskName "$ProjectName-*" -ErrorAction SilentlyContinue | Format-Table TaskName, State, LastRunTime, NextRunTime -AutoSize
    }
    catch {
        Write-LogWarning "Nenhuma tarefa do $ProjectName encontrada"
    }
}

# Executar acao principal
try {
    switch ($Action) {
        "install" {
            Install-SimpleTasks
        }
        "remove" {
            Remove-SimpleTasks
        }
        "status" {
            Show-SimpleTaskStatus
        }
    }
    
    Write-LogInfo "Operacao '$Action' concluida."
}
catch {
    Write-LogError "Falha na operacao '$Action': $($_.Exception.Message)"
    exit 1
}