#!/usr/bin/env python3
"""
Exemplo de uso do ResticClientAsync para realizar backups em paralelo.

Este script demonstra como utilizar o cliente assincrono para executar
operacoes de backup em paralelo, melhorando o desempenho quando ha
multiplos diretorios para backup.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Adicionar diretorio pai ao path para importar o pacote safestic
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.logger import setup_logger
from services.restic_client_async import ResticClientAsync
from services.env import get_credential_source


async def backup_directory(client: ResticClientAsync, path: str, tags: Optional[List[str]] = None) -> str:
    """Realiza backup de um diretorio especifico.
    
    Parameters
    ----------
    client : ResticClientAsync
        Cliente Restic assincrono
    path : str
        Caminho do diretorio para backup
    tags : Optional[List[str]]
        Tags a serem associadas ao snapshot
        
    Returns
    -------
    str
        ID do snapshot criado
    """
    logger = logging.getLogger("safestic.async_backup")
    logger.info(f"Iniciando backup de {path}")
    
    try:
        # Realizar backup
        snapshot_id = await client.backup(
            paths=[path],
            tags=tags or ["async_backup", Path(path).name],
        )
        
        logger.info(f"Backup de {path} concluido com sucesso. Snapshot ID: {snapshot_id}")
        return snapshot_id
    except Exception as e:
        logger.error(f"Erro ao realizar backup de {path}: {str(e)}")
        raise


async def main():
    """Funcao principal assincrona."""
    # Configurar logger
    logger = setup_logger(
        name="safestic.async_backup",
        log_level="INFO",
        log_file="logs/async_backup.log",
    )
    
    # Determinar fonte de credenciais e criar cliente
    credential_source = get_credential_source()
    client = ResticClientAsync(credential_source=credential_source)

    # Obter diretorios para backup
    backup_dirs_str = os.getenv("BACKUP_SOURCE_DIRS", "")
    if not backup_dirs_str:
        logger.error("Nenhum diretorio para backup especificado. Defina a variavel BACKUP_SOURCE_DIRS.")
        return 1

    backup_dirs = [d.strip() for d in backup_dirs_str.split(",")]
    logger.info(f"Diretorios para backup: {backup_dirs}")
    
    # Verificar repositorio
    try:
        logger.info("Verificando repositorio...")
        repo_ok = await client.check_repository_access()
        if not repo_ok:
            logger.error("Repositorio nao esta integro.")
            return 1
        logger.info("Repositorio verificado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao verificar repositorio: {str(e)}")
        return 1
    
    # Realizar backups em paralelo
    try:
        logger.info("Iniciando backups em paralelo...")
        tasks = [backup_directory(client, path) for path in backup_dirs]
        snapshot_ids = await asyncio.gather(*tasks)
        
        logger.info(f"Todos os backups concluidos. Snapshots: {snapshot_ids}")
        
        # Aplicar politica de retencao
        keep_daily = int(os.getenv("KEEP_DAILY", "7"))
        logger.info(f"Aplicando politica de retencao (keep-daily={keep_daily})...")
        await client.apply_retention_policy(keep_daily=keep_daily)
        logger.info("Politica de retencao aplicada com sucesso.")
        
        # Obter estatisticas
        logger.info("Obtendo estatisticas do repositorio...")
        stats = await client.get_stats()
        logger.info(f"Estatisticas: {stats}")
        
        return 0
    except Exception as e:
        logger.error(f"Erro durante o processo de backup: {str(e)}")
        return 1


if __name__ == "__main__":
    # Criar diretorio de logs se nao existir
    Path("logs").mkdir(exist_ok=True)
    
    # Executar funcao principal assincrona
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
