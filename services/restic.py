"""Funções para carregamento e validação da configuração do Restic.

Este módulo fornece funções para carregar variáveis de ambiente,
construir a string de repositório do Restic e validar a configuração.
"""

from __future__ import annotations

import logging
import os
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, cast

from pydantic import BaseModel, Field, ValidationError, validator
from dotenv import load_dotenv

from .credentials import get_credential

# Configuração de logger
logger = logging.getLogger(__name__)


class StorageProvider(str, Enum):
    """Provedores de armazenamento suportados."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"


class ResticConfig(BaseModel):
    """Modelo para validação da configuração do Restic."""
    storage_provider: StorageProvider
    storage_bucket: str = Field(..., min_length=1)
    restic_password: str = Field(..., min_length=1)
    backup_source_dirs: List[str] = Field(default_factory=list)
    restic_excludes: List[str] = Field(default_factory=list)
    restore_target_dir: Optional[str] = None
    log_dir: str = Field(default="logs")
    restic_tags: List[str] = Field(default_factory=list)
    retention_enabled: bool = Field(default=False)
    keep_daily: int = Field(default=7, ge=1)
    keep_weekly: int = Field(default=4, ge=1)
    keep_monthly: int = Field(default=6, ge=1)
    keep_yearly: int = Field(default=1, ge=1)
    credential_source: str = Field(default="env")
    
    @validator('backup_source_dirs')
    def validate_backup_dirs(cls, v):
        """Valida se os diretórios de backup existem."""
        for dir_path in v:
            if not Path(dir_path).exists():
                logger.warning(f"Diretório de backup não encontrado: {dir_path}")
        return v
    
    @validator('restore_target_dir')
    def validate_restore_dir(cls, v):
        """Valida se o diretório de restauração existe."""
        if v and not Path(v).exists():
            logger.warning(f"Diretório de restauração não encontrado: {v}")
        return v
    
    def get_repository_url(self) -> str:
        """Constrói a URL do repositório Restic."""
        if self.storage_provider == StorageProvider.AWS:
            return f"s3:s3.amazonaws.com/{self.storage_bucket}"
        elif self.storage_provider == StorageProvider.AZURE:
            return f"azure:{self.storage_bucket}:restic"
        elif self.storage_provider == StorageProvider.GCP:
            return f"gs:{self.storage_bucket}"
        elif self.storage_provider == StorageProvider.LOCAL:
            return str(Path(self.storage_bucket).absolute())
        else:
            # Nunca deve chegar aqui devido à validação do Pydantic
            raise ValueError(f"Provedor de armazenamento inválido: {self.storage_provider}")


def load_restic_env(credential_source: str = "env") -> tuple[str, dict[str, str], str]:
    """Carrega variáveis de ambiente e constrói a string de repositório do Restic.

    Parameters
    ----------
    credential_source : str
        Fonte para obtenção de credenciais (env, keyring, aws_secrets, azure_keyvault, gcp_secrets, sops)

    Returns
    -------
    tuple[str, dict[str, str], str]
        Uma tupla contendo a URL do repositório, uma cópia das variáveis
        de ambiente e o nome do provedor.

    Raises
    ------
    ValueError
        Se variáveis obrigatórias estiverem ausentes ou o provedor for inválido.
    """
    # Carregar variáveis de ambiente
    load_dotenv()

    # Obter variáveis básicas
    provider = os.getenv("STORAGE_PROVIDER", "").lower()
    bucket = os.getenv("STORAGE_BUCKET", "")
    
    # Obter senha de forma segura
    password = get_credential("RESTIC_PASSWORD", credential_source)

    # Validar provedor
    try:
        provider_enum = StorageProvider(provider)
    except ValueError:
        raise ValueError(f"STORAGE_PROVIDER inválido: {provider}. Use 'aws', 'azure', 'gcp' ou 'local'")

    # Validar bucket
    if not bucket:
        raise ValueError("STORAGE_BUCKET não definido")

    # Validar senha
    if not password:
        raise ValueError("RESTIC_PASSWORD não definido ou não encontrado")

    # Construir URL do repositório
    if provider_enum == StorageProvider.AWS:
        repository = f"s3:s3.amazonaws.com/{bucket}"
    elif provider_enum == StorageProvider.AZURE:
        repository = f"azure:{bucket}:restic"
    elif provider_enum == StorageProvider.GCP:
        repository = f"gs:{bucket}"
    elif provider_enum == StorageProvider.LOCAL:
        repository = str(Path(bucket).absolute())
    else:
        # Nunca deve chegar aqui devido à validação anterior
        raise ValueError(f"Provedor de armazenamento inválido: {provider}")

    # Preparar variáveis de ambiente
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password
    
    return repository, env, provider


def load_restic_config(credential_source: str = "env") -> ResticConfig:
    """Carrega e valida a configuração completa do Restic.
    
    Parameters
    ----------
    credential_source : str
        Fonte para obtenção de credenciais
        
    Returns
    -------
    ResticConfig
        Configuração validada do Restic
        
    Raises
    ------
    ValidationError
        Se a configuração for inválida
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter senha de forma segura
    password = get_credential("RESTIC_PASSWORD", credential_source)
    
    # Preparar configuração
    config_dict = {
        "storage_provider": os.getenv("STORAGE_PROVIDER", "").lower(),
        "storage_bucket": os.getenv("STORAGE_BUCKET", ""),
        "restic_password": password,
        "backup_source_dirs": os.getenv("BACKUP_SOURCE_DIRS", "").split(";") if os.getenv("BACKUP_SOURCE_DIRS") else [],
        "restic_excludes": os.getenv("RESTIC_EXCLUDES", "").split(";") if os.getenv("RESTIC_EXCLUDES") else [],
        "restore_target_dir": os.getenv("RESTORE_TARGET_DIR", "") or None,
        "log_dir": os.getenv("LOG_DIR", "logs"),
        "restic_tags": os.getenv("RESTIC_TAGS", "").split(";") if os.getenv("RESTIC_TAGS") else [],
        "retention_enabled": os.getenv("RETENTION_ENABLED", "false").lower() in ("true", "1", "yes"),
        "keep_daily": int(os.getenv("KEEP_DAILY", "7")),
        "keep_weekly": int(os.getenv("KEEP_WEEKLY", "4")),
        "keep_monthly": int(os.getenv("KEEP_MONTHLY", "6")),
        "keep_yearly": int(os.getenv("KEEP_YEARLY", "1")),
        "credential_source": credential_source,
    }
    
    # Validar configuração
    try:
        return ResticConfig(**config_dict)
    except ValidationError as e:
        logger.error(f"Erro de validação na configuração do Restic: {e}")
        raise

