#!/usr/bin/env python3
"""
Exemplo de uso do ResticClientAsync para realizar backups em paralelo.

Este script demonstra como utilizar o cliente assíncrono para executar
operações de backup em paralelo, melhorando o desempenho quando há
múltiplos diretórios para backup.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Adicionar diretório pai ao path para importar o pacote safestic
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.credentials import load_credentials
from services.logger import setup_logger
from services.restic_client_async import ResticClientAsync


async def backup_directory(client: ResticClientAsync, path: str, tags: Optional[List[str]] = None) -> str:
    """Realiza backup de um diretório específico.
    
    Parameters
    ----------
    client : ResticClientAsync
        Cliente Restic assíncrono
    path : str
        Caminho do diretório para backup
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
        
        logger.info(f"Backup de {path} concluído com sucesso. Snapshot ID: {snapshot_id}")
        return snapshot_id
    except Exception as e:
        logger.error(f"Erro ao realizar backup de {path}: {str(e)}")
        raise


async def main():
    """Função principal assíncrona."""
    # Configurar logger
    logger = setup_logger(
        name="safestic.async_backup",
        log_level="INFO",
        log_file="logs/async_backup.log",
    )
    
    # Carregar credenciais
    try:
        credentials = load_credentials(source="env")
        repository = credentials.get("RESTIC_REPOSITORY")
        password = credentials.get("RESTIC_PASSWORD")
        
        if not repository or not password:
            logger.error("Credenciais incompletas. Verifique as variáveis RESTIC_REPOSITORY e RESTIC_PASSWORD.")
            return 1
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais: {str(e)}")
        return 1
    
    # Obter diretórios para backup
    backup_dirs_str = os.getenv("BACKUP_SOURCE_DIRS", "")
    if not backup_dirs_str:
        logger.error("Nenhum diretório para backup especificado. Defina a variável BACKUP_SOURCE_DIRS.")
        return 1
    
    backup_dirs = [d.strip() for d in backup_dirs_str.split(",")]
    logger.info(f"Diretórios para backup: {backup_dirs}")
    
    # Criar cliente Restic assíncrono
    client = ResticClientAsync(repository=repository, password=password)
    
    # Verificar repositório
    try:
        logger.info("Verificando repositório...")
        repo_ok = await client.check_repository()
        if not repo_ok:
            logger.error("Repositório não está íntegro.")
            return 1
        logger.info("Repositório verificado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao verificar repositório: {str(e)}")
        return 1
    
    # Realizar backups em paralelo
    try:
        logger.info("Iniciando backups em paralelo...")
        tasks = [backup_directory(client, path) for path in backup_dirs]
        snapshot_ids = await asyncio.gather(*tasks)
        
        logger.info(f"Todos os backups concluídos. Snapshots: {snapshot_ids}")
        
        # Aplicar política de retenção
        keep_daily = int(os.getenv("KEEP_DAILY", "7"))
        logger.info(f"Aplicando política de retenção (keep-daily={keep_daily})...")
        await client.apply_retention_policy(keep_daily=keep_daily)
        logger.info("Política de retenção aplicada com sucesso.")
        
        # Obter estatísticas
        logger.info("Obtendo estatísticas do repositório...")
        stats = await client.get_stats()
        logger.info(f"Estatísticas: {stats}")
        
        return 0
    except Exception as e:
        logger.error(f"Erro durante o processo de backup: {str(e)}")
        return 1


if __name__ == "__main__":
    # Criar diretório de logs se não existir
    Path("logs").mkdir(exist_ok=True)
    
    # Executar função principal assíncrona
    exit_code = asyncio.run(main())
    sys.exit(exit_code)