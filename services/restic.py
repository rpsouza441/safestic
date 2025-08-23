"""Funcoes para carregamento e validacao da configuracao do Restic.

Este modulo fornece funcoes para carregar variaveis de ambiente,
construir a string de repositorio do Restic e validar a configuracao.
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

# Configuracao de logger
logger = logging.getLogger(__name__)


class StorageProvider(str, Enum):
    """Provedores de armazenamento suportados."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"


class ResticConfig(BaseModel):
    """Modelo para validacao da configuracao do Restic."""
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
        """Valida se os diretorios de backup existem."""
        for dir_path in v:
            if not Path(dir_path).exists():
                logger.warning(f"Diretorio de backup nao encontrado: {dir_path}")
        return v
    
    @validator('restore_target_dir')
    def validate_restore_dir(cls, v):
        """Valida se o diretorio de restauracao existe."""
        if v and not Path(v).exists():
            logger.warning(f"Diretorio de restauracao nao encontrado: {v}")
        return v
    
    def get_repository_url(self) -> str:
        """Constroi a URL do repositorio Restic."""
        if self.storage_provider == StorageProvider.AWS:
            return f"s3:s3.amazonaws.com/{self.storage_bucket}"
        elif self.storage_provider == StorageProvider.AZURE:
            return f"azure:{self.storage_bucket}:restic"
        elif self.storage_provider == StorageProvider.GCP:
            return f"gs:{self.storage_bucket}"
        elif self.storage_provider == StorageProvider.LOCAL:
            return str(Path(self.storage_bucket).absolute())
        else:
            # Nunca deve chegar aqui devido a validacao do Pydantic
            raise ValueError(f"Provedor de armazenamento invalido: {self.storage_provider}")
    
    @property
    def repository_url(self) -> str:
        """Propriedade para compatibilidade - retorna a URL do repositorio."""
        return self.get_repository_url()
    
    @property
    def environment(self) -> dict[str, str]:
        """Propriedade para compatibilidade - retorna as variaveis de ambiente."""
        _, env, _ = load_restic_env()
        return env


def load_restic_env(credential_source: str = "env") -> tuple[str, dict[str, str], str]:
    """Carrega variaveis de ambiente e constroi a string de repositorio do Restic.

    Parameters
    ----------
    credential_source : str
        Fonte para obtencao de credenciais (env, keyring, aws_secrets, azure_keyvault, gcp_secrets, sops)

    Returns
    -------
    tuple[str, dict[str, str], str]
        Uma tupla contendo a URL do repositorio, uma copia das variaveis
        de ambiente e o nome do provedor.

    Raises
    ------
    ValueError
        Se variaveis obrigatorias estiverem ausentes ou o provedor for invalido.
    """
    # Carregar variaveis de ambiente
    load_dotenv()

    # Obter variaveis basicas
    provider = os.getenv("STORAGE_PROVIDER", "").lower()
    bucket = os.getenv("STORAGE_BUCKET", "")
    
    # Obter senha de forma segura
    password = get_credential("RESTIC_PASSWORD", credential_source)

    # Validar provedor
    try:
        provider_enum = StorageProvider(provider)
    except ValueError:
        raise ValueError(f"STORAGE_PROVIDER invalido: {provider}. Use 'aws', 'azure', 'gcp' ou 'local'")

    # Validar bucket
    if not bucket:
        raise ValueError("STORAGE_BUCKET nao definido")

    # Validar senha
    if not password:
        raise ValueError("RESTIC_REPOSITORY e RESTIC_PASSWORD sao obrigatorios")

    # Construir URL do repositorio
    if provider_enum == StorageProvider.AWS:
        repository = f"s3:s3.amazonaws.com/{bucket}"
    elif provider_enum == StorageProvider.AZURE:
        repository = f"azure:{bucket}:restic"
    elif provider_enum == StorageProvider.GCP:
        repository = f"gs:{bucket}"
    elif provider_enum == StorageProvider.LOCAL:
        repository = str(Path(bucket).absolute())
    else:
        # Nunca deve chegar aqui devido a validacao anterior
        raise ValueError(f"Provedor de armazenamento invalido: {provider}")

    # Preparar variaveis de ambiente
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password
    
    # Carregar credenciais especificas do provedor
    if provider_enum == StorageProvider.AWS:
        aws_access_key = get_credential("AWS_ACCESS_KEY_ID", credential_source)
        aws_secret_key = get_credential("AWS_SECRET_ACCESS_KEY", credential_source)
        if aws_access_key:
            env["AWS_ACCESS_KEY_ID"] = aws_access_key
        if aws_secret_key:
            env["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
    elif provider_enum == StorageProvider.AZURE:
        azure_account_name = get_credential("AZURE_ACCOUNT_NAME", credential_source)
        azure_account_key = get_credential("AZURE_ACCOUNT_KEY", credential_source)
        if azure_account_name:
            env["AZURE_ACCOUNT_NAME"] = azure_account_name
        if azure_account_key:
            env["AZURE_ACCOUNT_KEY"] = azure_account_key
    elif provider_enum == StorageProvider.GCP:
        google_project_id = get_credential("GOOGLE_PROJECT_ID", credential_source)
        google_app_credentials = get_credential("GOOGLE_APPLICATION_CREDENTIALS", credential_source)
        if google_project_id:
            env["GOOGLE_PROJECT_ID"] = google_project_id
        if google_app_credentials:
            env["GOOGLE_APPLICATION_CREDENTIALS"] = google_app_credentials
    
    return repository, env, provider


def load_restic_config(credential_source: str = "env") -> ResticConfig:
    """Carrega e valida a configuracao completa do Restic.
    
    Parameters
    ----------
    credential_source : str
        Fonte para obtencao de credenciais
        
    Returns
    -------
    ResticConfig
        Configuracao validada do Restic
        
    Raises
    ------
    ValidationError
        Se a configuracao for invalida
    """
    # Carregar variaveis de ambiente
    load_dotenv()
    
    # Obter senha de forma segura
    password = get_credential("RESTIC_PASSWORD", credential_source)
    
    # Preparar configuracao
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
    
    # Validar configuracao
    try:
        return ResticConfig(**config_dict)
    except ValidationError as e:
        logger.error(f"Erro de validacao na configuracao do Restic: {e}")
        raise


