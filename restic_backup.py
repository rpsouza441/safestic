import os
import sys
import logging
from typing import List

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def build_args(prefix, items):
    """Repete ``prefix`` para cada item não vazio."""
    return [arg for i in items for arg in (prefix, i.strip()) if i.strip()]


def run_backup():
    """Executa o backup com base nas variáveis do .env e aplica política de retenção se ativada.
    
    Utiliza o ResticClient para executar o backup com retry automático e tratamento de erros.
    """
    with ResticScript("backup") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        # Carregar variáveis de ambiente
        source_dirs = os.getenv("BACKUP_SOURCE_DIRS", "").split(",")
        source_dirs = [d.strip() for d in source_dirs if d.strip()]
        excludes = os.getenv("RESTIC_EXCLUDES", "").split(",")
        excludes = [e.strip() for e in excludes if e.strip()]
        tags = os.getenv("RESTIC_TAGS", "").split(",")
        tags = [t.strip() for t in tags if t.strip()]

        retention_enabled = os.getenv("RETENTION_ENABLED", "true").lower() == "true"
        keep_hourly = int(os.getenv("RETENTION_KEEP_HOURLY", "0"))
        keep_daily = int(os.getenv("RETENTION_KEEP_DAILY", "7"))
        keep_weekly = int(os.getenv("RETENTION_KEEP_WEEKLY", "4"))
        keep_monthly = int(os.getenv("RETENTION_KEEP_MONTHLY", "6"))

        if not source_dirs:
            ctx.log("[FATAL] Variáveis obrigatórias ausentes no .env")
            sys.exit(1)

        ctx.log("=== Iniciando backup com Restic ===")

        # Criar cliente Restic com retry
        client = ResticClient(max_attempts=3)
        
        try:
            # Verificar acesso ao repositório
            ctx.log("🔍 Verificando acesso ao repositório...")
            if not client.check_repository_access():
                ctx.log("Não foi possível acessar o repositório. Abortando.")
                return
            ctx.log("✅ Repositório acessível.")
            
            # Executar backup
            ctx.log(f"Executando backup de: {', '.join(source_dirs)}")
            snapshot_id = client.backup(
                paths=source_dirs,
                excludes=excludes,
                tags=tags,
            )
            ctx.log(f"Backup concluído com sucesso. ID do snapshot: {snapshot_id}")
            
            # Aplicar política de retenção se ativada
            if retention_enabled:
                ctx.log("Aplicando política de retenção...")
                client.apply_retention_policy(
                    keep_hourly=keep_hourly,
                    keep_daily=keep_daily,
                    keep_weekly=keep_weekly,
                    keep_monthly=keep_monthly,
                    prune=True,
                )
                ctx.log("Política de retenção aplicada.")
            else:
                ctx.log("Retenção desativada via .env.")
                
        except ResticError as e:
            ctx.log(f"[ERRO] {e}")
            sys.exit(1)
        except Exception as e:
            ctx.log(f"[FATAL] Erro inesperado: {e}")
            sys.exit(1)
            
        ctx.log("=== Fim do backup ===")


if __name__ == "__main__":
    run_backup()
