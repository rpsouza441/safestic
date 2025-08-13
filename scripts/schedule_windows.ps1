# Script de agendamento para Windows (Task Scheduler) - FASE 3
# Instala e configura tarefas agendadas para backup e prune automático
# Uso: .\scripts\schedule_windows.ps1 [install|remove|status] [-AsUser]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "remove", "status")]
    [string]$Action,
    
    [switch]$AsUser = $false
)

# Configurações
$ProjectDir = Split-Path -Parent $PSScriptRoot
$ProjectName = "Safestic"
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Funções de log
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ℹ️  $Message" -ForegroundColor Blue
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ✅ $Message" -ForegroundColor Green
}

function Write-LogWarning {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ⚠️  $Message" -ForegroundColor Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ❌ $Message" -ForegroundColor Red
}

# Verificar se está executando como administrador
function Test-IsAdmin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Detectar Make disponível
function Get-MakeCommand {
    $makeCommands = @("make", "mingw32-make", "gmake")
    
    foreach ($cmd in $makeCommands) {
        try {
            $null = Get-Command $cmd -ErrorAction Stop
            Write-LogInfo "Make encontrado: $cmd"
            return $cmd
        }
        catch {
            continue
        }
    }
    
    Write-LogError "Nenhum comando Make encontrado. Instale Git for Windows ou MSYS2."
    throw "Make não encontrado"
}

# Criar tarefa de backup
function New-BackupTask {
    param([string]$MakeCmd)
    
    $taskName = "$ProjectName-Backup"
    Write-LogInfo "Criando tarefa de backup: $taskName"
    
    # Definir ação
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -Command `"Set-Location '$ProjectDir'; & $MakeCmd backup; & $MakeCmd check`""
    
    # Definir trigger (diário às 02:00 com delay aleatório de até 1h)
    $trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
    $trigger.RandomDelay = "PT1H"  # 1 hora de delay aleatório
    
    # Definir configurações
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    $settings.ExecutionTimeLimit = "PT2H"  # Timeout de 2 horas
    $settings.RestartCount = 3
    $settings.RestartInterval = "PT15M"  # Restart a cada 15 minutos se falhar
    
    # Definir principal (usuário)
    if ($AsUser) {
        $principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive
        Write-LogInfo "Tarefa será executada como usuário: $CurrentUser"
    } else {
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Write-LogInfo "Tarefa será executada como SYSTEM"
    }
    
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

# Criar tarefa de prune
function New-PruneTask {
    param([string]$MakeCmd)
    
    $taskName = "$ProjectName-Prune"
    Write-LogInfo "Criando tarefa de prune: $taskName"
    
    # Definir ação
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -Command `"Set-Location '$ProjectDir'; & $MakeCmd prune; & $MakeCmd check`""
    
    # Definir trigger (semanal aos domingos às 03:00 com delay aleatório de até 2h)
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "03:00AM"
    $trigger.RandomDelay = "PT2H"  # 2 horas de delay aleatório
    
    # Definir configurações
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    $settings.ExecutionTimeLimit = "PT3H"  # Timeout de 3 horas
    $settings.RestartCount = 2
    $settings.RestartInterval = "PT30M"  # Restart a cada 30 minutos se falhar
    
    # Definir principal (usuário)
    if ($AsUser) {
        $principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive
        Write-LogInfo "Tarefa será executada como usuário: $CurrentUser"
    } else {
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Write-LogInfo "Tarefa será executada como SYSTEM"
    }
    
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
function Install-Tasks {
    Write-LogInfo "=== INSTALANDO TAREFAS AGENDADAS ==="
    
    # Verificar privilégios se não for modo usuário
    if (-not $AsUser -and -not (Test-IsAdmin)) {
        Write-LogError "Modo sistema requer privilégios de administrador. Execute como administrador ou use -AsUser."
        throw "Privilégios insuficientes"
    }
    
    # Detectar comando Make
    $makeCmd = Get-MakeCommand
    
    # Verificar se o projeto existe
    if (-not (Test-Path "$ProjectDir\Makefile")) {
        Write-LogError "Makefile não encontrado em: $ProjectDir"
        throw "Projeto não encontrado"
    }
    
    # Criar tarefas
    New-BackupTask -MakeCmd $makeCmd
    New-PruneTask -MakeCmd $makeCmd
    
    Write-LogSuccess "=== TAREFAS INSTALADAS COM SUCESSO ==="
    Write-LogInfo "Backup: execução diária às 02:00 com delay aleatório de até 1h"
    Write-LogInfo "Prune: execução semanal aos domingos às 03:00 com delay aleatório de até 2h"
    Write-LogInfo "Use 'Get-ScheduledTask -TaskName `"$ProjectName-*`"' para verificar"
}

# Remover tarefas
function Remove-Tasks {
    Write-LogInfo "=== REMOVENDO TAREFAS AGENDADAS ==="
    
    $taskNames = @("$ProjectName-Backup", "$ProjectName-Prune")
    
    foreach ($taskName in $taskNames) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Write-LogInfo "Removendo tarefa: $taskName"
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-LogSuccess "Tarefa $taskName removida"
            } else {
                Write-LogWarning "Tarefa $taskName não encontrada"
            }
        }
        catch {
            Write-LogError "Falha ao remover tarefa $taskName`: $($_.Exception.Message)"
        }
    }
    
    Write-LogSuccess "=== TAREFAS REMOVIDAS COM SUCESSO ==="
}

# Mostrar status das tarefas
function Show-TaskStatus {
    Write-LogInfo "=== STATUS DAS TAREFAS AGENDADAS ==="
    
    $taskNames = @("$ProjectName-Backup", "$ProjectName-Prune")
    
    foreach ($taskName in $taskNames) {
        Write-Host ""
        Write-LogInfo "Status da tarefa: $taskName"
        
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Write-Host "  Estado: $($task.State)" -ForegroundColor Cyan
                Write-Host "  Última execução: $($task.LastRunTime)" -ForegroundColor Cyan
                Write-Host "  Próxima execução: $($task.NextRunTime)" -ForegroundColor Cyan
                Write-Host "  Último resultado: $($task.LastTaskResult)" -ForegroundColor Cyan
                
                # Mostrar detalhes do trigger
                $trigger = $task.Triggers[0]
                if ($trigger) {
                    Write-Host "  Agendamento: $($trigger.StartBoundary)" -ForegroundColor Cyan
                    if ($trigger.RandomDelay) {
                        Write-Host "  Delay aleatório: $($trigger.RandomDelay)" -ForegroundColor Cyan
                    }
                }
                
                # Mostrar histórico recente
                Write-Host "  Histórico recente:" -ForegroundColor Cyan
                $events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=200,201} -MaxEvents 5 -ErrorAction SilentlyContinue | Where-Object { $_.Message -like "*$taskName*" }
                if ($events) {
                    foreach ($event in $events) {
                        $status = if ($event.Id -eq 200) { "Iniciado" } else { "Concluído" }
                        Write-Host "    $($event.TimeCreated): $status" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "    Nenhum evento recente encontrado" -ForegroundColor Gray
                }
            } else {
                Write-LogWarning "Tarefa $taskName não encontrada"
            }
        }
        catch {
            Write-LogError "Erro ao obter status da tarefa $taskName`: $($_.Exception.Message)"
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

# Executar ação principal
try {
    switch ($Action) {
        "install" {
            Install-Tasks
        }
        "remove" {
            Remove-Tasks
        }
        "status" {
            Show-TaskStatus
        }
    }
    
    Write-LogInfo "Operação '$Action' concluída."
}
catch {
    Write-LogError "Falha na operação '$Action': $($_.Exception.Message)"
    exit 1
}