#!/usr/bin/env python3
"""
Exemplo de uso do sistema de gerenciamento seguro de credenciais.

Este script demonstra como utilizar diferentes fontes de credenciais
para operacoes do Restic, incluindo keyring do sistema, servicos de
nuvem e arquivos criptografados.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# Adicionar diretorio pai ao path para importar o pacote safestic
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.credentials import load_credentials, set_credential, get_credential
from services.logger import setup_logger
from services.restic_client import ResticClient


def setup_credentials(source: str, key: str, value: str) -> bool:
    """Configura uma credencial em uma fonte especifica.
    
    Parameters
    ----------
    source : str
        Fonte para armazenamento (keyring, env)
    key : str
        Chave da credencial
    value : str
        Valor da credencial
        
    Returns
    -------
    bool
        True se a credencial foi configurada com sucesso
    """
    logger = logging.getLogger("safestic.secure_credentials")
    
    try:
        set_credential(key, value, source=source)
        logger.info(f"Credencial {key} configurada com sucesso na fonte {source}")
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar credencial {key} na fonte {source}: {str(e)}")
        return False


def test_credentials(source: str) -> bool:
    """Testa o carregamento de credenciais de uma fonte especifica.
    
    Parameters
    ----------
    source : str
        Fonte para carregamento (keyring, env, aws_secrets, azure_keyvault, gcp_secrets, sops)
        
    Returns
    -------
    bool
        True se as credenciais foram carregadas com sucesso
    """
    logger = logging.getLogger("safestic.secure_credentials")
    
    try:
        logger.info(f"Carregando credenciais da fonte: {source}")
        credentials = load_credentials(source=source)
        
        # Verificar credenciais essenciais
        required_keys = ["RESTIC_REPOSITORY", "RESTIC_PASSWORD"]
        missing_keys = [key for key in required_keys if key not in credentials]
        
        if missing_keys:
            logger.warning(f"Credenciais ausentes: {', '.join(missing_keys)}")
            return False
        
        # Exibir informacoes (com redacao de segredos)
        logger.info(f"Credenciais carregadas com sucesso da fonte {source}")
        for key in credentials:
            value = credentials[key]
            if key == "RESTIC_PASSWORD" or "SECRET" in key or "KEY" in key:
                value = "*****"
            logger.info(f"  {key}: {value}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais da fonte {source}: {str(e)}")
        return False


def test_restic_with_credentials(source: str) -> bool:
    """Testa o cliente Restic com credenciais de uma fonte especifica.
    
    Parameters
    ----------
    source : str
        Fonte para carregamento (keyring, env, aws_secrets, azure_keyvault, gcp_secrets, sops)
        
    Returns
    -------
    bool
        True se o teste foi bem-sucedido
    """
    logger = logging.getLogger("safestic.secure_credentials")
    
    try:
        # Carregar credenciais
        credentials = load_credentials(source=source)
        repository = credentials.get("RESTIC_REPOSITORY")
        password = credentials.get("RESTIC_PASSWORD")
        
        if not repository or not password:
            logger.error("Credenciais incompletas. Verifique as variaveis RESTIC_REPOSITORY e RESTIC_PASSWORD.")
            return False
        
        # Criar cliente Restic
        client = ResticClient(repository=repository, password=password)
        
        # Verificar repositorio
        logger.info("Verificando repositorio...")
        repo_ok = client.check_repository()
        
        if repo_ok:
            logger.info("Repositorio verificado com sucesso.")
            
            # Listar snapshots
            logger.info("Listando snapshots...")
            snapshots = client.list_snapshots()
            logger.info(f"Total de snapshots: {len(snapshots)}")
            
            return True
        else:
            logger.error("Repositorio nao esta integro.")
            return False
    except Exception as e:
        logger.error(f"Erro ao testar Restic com credenciais da fonte {source}: {str(e)}")
        return False


def main():
    """Funcao principal."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Exemplo de uso do sistema de gerenciamento seguro de credenciais")
    parser.add_argument(
        "--source", 
        choices=["env", "keyring", "aws_secrets", "azure_keyvault", "gcp_secrets", "sops"],
        default="env",
        help="Fonte para carregamento/armazenamento de credenciais"
    )
    parser.add_argument(
        "--action",
        choices=["setup", "test", "restic"],
        default="test",
        help="Acao a ser executada"
    )
    parser.add_argument(
        "--key",
        help="Chave da credencial (para acao 'setup')"
    )
    parser.add_argument(
        "--value",
        help="Valor da credencial (para acao 'setup')"
    )
    
    args = parser.parse_args()
    
    # Criar diretorio de logs se nao existir
    Path("logs").mkdir(exist_ok=True)
    
    # Configurar logger
    logger = setup_logger(
        name="safestic.secure_credentials",
        log_level="INFO",
        log_file="logs/secure_credentials.log",
    )
    
    # Executar acao solicitada
    if args.action == "setup":
        if not args.key or not args.value:
            logger.error("Para a acao 'setup', e necessario fornecer --key e --value")
            return 1
        
        success = setup_credentials(args.source, args.key, args.value)
        return 0 if success else 1
    
    elif args.action == "test":
        success = test_credentials(args.source)
        return 0 if success else 1
    
    elif args.action == "restic":
        success = test_restic_with_credentials(args.source)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
