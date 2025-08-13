#!/bin/bash
# Script de verificação de saúde do backup Safestic
# Verifica se os backups estão atualizados e o sistema está funcionando

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔍 Verificando saúde do backup..."

# Verificar se o ambiente virtual está ativo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log_info "Ativando ambiente virtual..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        log_error "Ambiente virtual não encontrado. Execute o setup primeiro."
        exit 1
    fi
fi

# Verificar último snapshot
log_info "Verificando último backup..."
LAST_BACKUP=$(python -c "
from services.restic_client import ResticClient
from services.restic import load_restic_config
from datetime import datetime, timedelta

try:
    config = load_restic_config()
    client = ResticClient(config.repository_url, config.environment)
    snapshots = client.list_snapshots()
    
    if snapshots:
        last = snapshots[0]
        print(last['time'])
    else:
        print('NEVER')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>/dev/null || echo "ERROR")

if [[ "$LAST_BACKUP" == "ERROR" ]]; then
    log_error "Erro ao verificar snapshots. Verifique a configuração."
    exit 1
elif [[ "$LAST_BACKUP" == "NEVER" ]]; then
    log_error "Nenhum backup encontrado!"
    exit 1
else
    log_info "Último backup: $LAST_BACKUP"
fi

# Verificar se backup é recente (últimas 25 horas)
log_info "Verificando se o backup está atualizado..."
python -c "
from datetime import datetime, timedelta
import sys

last_backup = '$LAST_BACKUP'
if last_backup == 'NEVER':
    print('❌ Nenhum backup encontrado!')
    sys.exit(1)

try:
    # Tentar diferentes formatos de data
    try:
        last_time = datetime.fromisoformat(last_backup.replace('Z', '+00:00'))
    except:
        # Formato alternativo
        last_time = datetime.strptime(last_backup, '%Y-%m-%dT%H:%M:%S.%f%z')
    
    now = datetime.now(last_time.tzinfo)
    time_diff = now - last_time
    
    if time_diff > timedelta(hours=25):
        hours_ago = int(time_diff.total_seconds() / 3600)
        if hours_ago > 24:
            days_ago = hours_ago // 24
            print(f'⚠️  Último backup há {days_ago} dias ({hours_ago}h)')
        else:
            print(f'⚠️  Último backup há {hours_ago} horas')
        sys.exit(1)
    else:
        hours_ago = int(time_diff.total_seconds() / 3600)
        print(f'✅ Backup recente (há {hours_ago}h)')
except Exception as e:
    print(f'❌ Erro ao verificar data: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    log_warning "Backup desatualizado detectado!"
    BACKUP_OUTDATED=true
else
    log_success "Backup está atualizado"
    BACKUP_OUTDATED=false
fi

# Verificar integridade do repositório
log_info "Verificando integridade do repositório..."
if make check >/dev/null 2>&1; then
    log_success "Configuração válida"
else
    log_error "Problemas na configuração detectados"
    exit 1
fi

# Verificar espaço em disco (logs)
log_info "Verificando espaço em disco para logs..."
if [ -d "logs" ]; then
    LOG_SIZE=$(du -sh logs 2>/dev/null | cut -f1 || echo "0")
    log_info "Tamanho dos logs: $LOG_SIZE"
    
    # Limpar logs antigos se necessário (>100MB)
    LOG_SIZE_BYTES=$(du -sb logs 2>/dev/null | cut -f1 || echo "0")
    if [ "$LOG_SIZE_BYTES" -gt 104857600 ]; then  # 100MB
        log_warning "Logs ocupando muito espaço ($LOG_SIZE). Limpando logs antigos..."
        find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
        log_info "Logs antigos removidos"
    fi
else
    log_info "Diretório de logs não encontrado"
fi

# Verificar conectividade com repositório
log_info "Testando conectividade com repositório..."
python -c "
from services.restic_client import ResticClient
from services.restic import load_restic_config

try:
    config = load_restic_config()
    client = ResticClient(config.repository_url, config.environment)
    # Tentar listar snapshots como teste de conectividade
    snapshots = client.list_snapshots()
    print(f'✅ Conectividade OK - {len(snapshots)} snapshots encontrados')
except Exception as e:
    print(f'❌ Erro de conectividade: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    log_error "Problemas de conectividade detectados"
    exit 1
fi

# Resumo final
echo ""
log_info "=== RESUMO DA VERIFICAÇÃO ==="

if [ "$BACKUP_OUTDATED" = "true" ]; then
    log_warning "⚠️  ATENÇÃO: Backup desatualizado!"
    log_info "Recomendação: Execute 'make backup' para criar um novo backup"
    echo ""
    log_info "Para executar backup agora:"
    log_info "  make backup"
    echo ""
    exit 1
else
    log_success "✅ Sistema de backup saudável!"
    echo ""
    log_info "Próximas verificações recomendadas:"
    log_info "  - Execute este script diariamente"
    log_info "  - Monitore os logs em logs/"
    log_info "  - Teste restaurações periodicamente"
    echo ""
fi

log_success "Verificação concluída com sucesso!"