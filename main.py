#!/usr/bin/env python3
"""
Exemplo de uso do ResticClient para operacoes de backup e restore.

Este script demonstra como utilizar o wrapper ResticClient para realizar
operacoes comuns do Restic como backup, listagem de snapshots e restauracao.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from services.restic_client import ResticClient, ResticError


def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/restic_example_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ],
    )


def main():
    """Funcao principal que demonstra o uso do ResticClient."""
    # Configurar logging
    os.makedirs("logs", exist_ok=True)
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== Exemplo de uso do ResticClient ===")
    
    try:
        # Criar cliente Restic com retry
        client = ResticClient(max_attempts=3)
        
        # Verificar acesso ao repositorio
        logger.info("Verificando acesso ao repositorio...")
        if not client.check_repository_access():
            logger.info("Repositorio nao encontrado, tentando inicializar...")
            if client.init_repository():
                logger.info("Repositorio inicializado com sucesso.")
            else:
                logger.error("Falha ao inicializar o repositorio.")
                return 1
        
        # Realizar backup
        logger.info("Realizando backup...")
        source_dirs = os.getenv("BACKUP_SOURCE_DIRS", "").split(";") if os.getenv("BACKUP_SOURCE_DIRS") else []
        excludes = os.getenv("RESTIC_EXCLUDES", "").split(";") if os.getenv("RESTIC_EXCLUDES") else []
        tags = os.getenv("RESTIC_TAGS", "").split(",") if os.getenv("RESTIC_TAGS") else []
        
        if not source_dirs:
            logger.error("Nenhum diretorio de origem definido para backup.")
            return 1
        
        logger.info(f"Diretorios de origem: {source_dirs}")
        logger.info(f"Padroes de exclusao: {excludes}")
        logger.info(f"Tags: {tags}")
        
        success = client.backup(
            source_dirs=source_dirs,
            excludes=excludes,
            tags=tags
        )
        
        if success:
            logger.info("Backup concluido com sucesso.")
        else:
            logger.error("Falha ao realizar backup.")
            return 1
        
        # Listar snapshots
        logger.info("Listando snapshots disponiveis...")
        snapshots = client.list_snapshots()
        
        if not snapshots:
            logger.info("Nenhum snapshot encontrado no repositorio.")
        else:
            logger.info(f"Encontrados {len(snapshots)} snapshots:")
            for snapshot in snapshots:
                snapshot_time = datetime.fromisoformat(
                    snapshot["time"].replace("Z", "+00:00")
                )
                formatted_time = snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"ID: {snapshot['short_id']}, Data: {formatted_time}, Host: {snapshot['hostname']}")
        
        # Restaurar ultimo snapshot (apenas para demonstracao)
        if snapshots:
            latest_snapshot = snapshots[-1]["short_id"]
            restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
            Path(restore_target).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Restaurando ultimo snapshot ({latest_snapshot}) para {restore_target}...")
            # Comentado para evitar restauracao acidental
            # success = client.restore_snapshot(
            #     target_dir=restore_target,
            #     snapshot_id=latest_snapshot
            # )
            # 
            # if success:
            #     logger.info("Restauracao concluida com sucesso.")
            # else:
            #     logger.error("Falha ao restaurar snapshot.")
            #     return 1
            
            logger.info("Restauracao comentada para evitar execucao acidental.")
            logger.info("Para restaurar, descomente as linhas relevantes no codigo.")
        
        # Aplicar politica de retencao (apenas para demonstracao)
        logger.info("Aplicando politica de retencao (simulacao)...")
        retention_enabled = os.getenv("RETENTION_ENABLED", "false").lower() == "true"
        
        if retention_enabled:
            keep_daily = int(os.getenv("RETENTION_KEEP_DAILY", "7"))
            keep_weekly = int(os.getenv("RETENTION_KEEP_WEEKLY", "4"))
            keep_monthly = int(os.getenv("RETENTION_KEEP_MONTHLY", "6"))
            
            logger.info(f"Politica de retencao: diario={keep_daily}, semanal={keep_weekly}, mensal={keep_monthly}")
            # Comentado para evitar exclusao acidental de snapshots
            # success = client.apply_retention_policy(
            #     keep_daily=keep_daily,
            #     keep_weekly=keep_weekly,
            #     keep_monthly=keep_monthly
            # )
            # 
            # if success:
            #     logger.info("Politica de retencao aplicada com sucesso.")
            # else:
            #     logger.error("Falha ao aplicar politica de retencao.")
            #     return 1
            
            logger.info("Aplicacao de politica comentada para evitar execucao acidental.")
            logger.info("Para aplicar, descomente as linhas relevantes no codigo.")
        else:
            logger.info("Politica de retencao desativada.")
        
        logger.info("=== Exemplo concluido com sucesso ===")
        return 0
        
    except ResticError as exc:
        logger.error(f"Erro do Restic: {exc}")
        return 1
    except Exception as exc:
        logger.error(f"Erro inesperado: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
