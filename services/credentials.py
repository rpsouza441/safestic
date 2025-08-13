"""Gerenciamento seguro de credenciais para o Restic.

Este módulo fornece funções para carregar credenciais de forma segura de várias fontes:
- Keyring do sistema operacional
- Gerenciadores de segredos em nuvem (AWS, Azure, GCP)
- Arquivo .env criptografado com SOPS
- Arquivo .env padrão (fallback)

Todas as funções garantem que segredos não sejam expostos em logs ou saídas.
"""

from __future__ import annotations

import os
import json
import logging
import subprocess
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any, Union, cast

import keyring
from dotenv import load_dotenv

# Configuração de logging
logger = logging.getLogger(__name__)


class CredentialSource(str, Enum):
    """Fontes possíveis para obtenção de credenciais."""

    ENV = "env"  # Variáveis de ambiente ou .env
    KEYRING = "keyring"  # Keyring do sistema
    AWS_SECRETS = "aws_secrets"  # AWS Secrets Manager
    AZURE_KEYVAULT = "azure_keyvault"  # Azure Key Vault
    GCP_SECRETS = "gcp_secrets"  # GCP Secret Manager
    SOPS = "sops"  # .env criptografado com SOPS


class CredentialManager:
    """Gerenciador de credenciais para o Restic.
    
    Fornece métodos para obter credenciais de várias fontes de forma segura.
    
    Parameters
    ----------
    app_name : str
        Nome da aplicação para uso com keyring
    credential_source : CredentialSource
        Fonte primária para obtenção de credenciais
    fallback_to_env : bool
        Se deve usar variáveis de ambiente como fallback
    sops_file : Optional[str]
        Caminho para arquivo .env criptografado com SOPS
    """

    def __init__(
        self,
        app_name: str = "safestic",
        credential_source: Union[CredentialSource, str] = CredentialSource.ENV,
        fallback_to_env: bool = True,
        sops_file: Optional[str] = None,
    ) -> None:
        self.app_name = app_name
        
        if isinstance(credential_source, str):
            try:
                self.credential_source = CredentialSource(credential_source.lower())
            except ValueError:
                logger.warning(
                    f"Fonte de credenciais '{credential_source}' inválida. Usando ENV como padrão."
                )
                self.credential_source = CredentialSource.ENV
        else:
            self.credential_source = credential_source
            
        self.fallback_to_env = fallback_to_env
        self.sops_file = sops_file
        self._loaded_env = False
        
        # Carregar variáveis de ambiente se necessário
        if self.credential_source == CredentialSource.ENV or self.fallback_to_env:
            self._ensure_env_loaded()

    def _ensure_env_loaded(self) -> None:
        """Garante que as variáveis de ambiente foram carregadas."""
        if not self._loaded_env:
            load_dotenv()
            self._loaded_env = True

    def get_credential(self, key: str) -> Optional[str]:
        """Obtém uma credencial da fonte configurada.
        
        Parameters
        ----------
        key : str
            Nome da credencial a ser obtida
            
        Returns
        -------
        Optional[str]
            Valor da credencial ou None se não encontrada
        """
        value = None
        
        # Tentar obter da fonte primária
        try:
            if self.credential_source == CredentialSource.KEYRING:
                value = self._get_from_keyring(key)
            elif self.credential_source == CredentialSource.AWS_SECRETS:
                value = self._get_from_aws_secrets(key)
            elif self.credential_source == CredentialSource.AZURE_KEYVAULT:
                value = self._get_from_azure_keyvault(key)
            elif self.credential_source == CredentialSource.GCP_SECRETS:
                value = self._get_from_gcp_secrets(key)
            elif self.credential_source == CredentialSource.SOPS:
                value = self._get_from_sops(key)
            else:  # CredentialSource.ENV
                value = os.getenv(key)
        except Exception as e:
            logger.error(f"Erro ao obter credencial {key}: {str(e)}")
            
        # Fallback para variáveis de ambiente se necessário
        if value is None and self.fallback_to_env and self.credential_source != CredentialSource.ENV:
            self._ensure_env_loaded()
            value = os.getenv(key)
            if value is not None:
                logger.debug(f"Usando fallback de variável de ambiente para {key}")
                
        return value

    def _get_from_keyring(self, key: str) -> Optional[str]:
        """Obtém credencial do keyring do sistema."""
        try:
            return keyring.get_password(self.app_name, key)
        except Exception as e:
            logger.error(f"Erro ao acessar keyring: {str(e)}")
            return None

    def _get_from_aws_secrets(self, key: str) -> Optional[str]:
        """Obtém credencial do AWS Secrets Manager."""
        try:
            import boto3
            
            # Obter nome do segredo baseado na chave
            secret_name = f"{self.app_name}/{key}"
            
            # Criar cliente do Secrets Manager
            client = boto3.client('secretsmanager')
            
            # Obter o segredo
            response = client.get_secret_value(SecretId=secret_name)
            
            # O segredo pode estar em SecretString ou SecretBinary
            if 'SecretString' in response:
                secret = response['SecretString']
                # O segredo pode ser um JSON ou uma string simples
                try:
                    secret_dict = json.loads(secret)
                    return secret_dict.get(key)
                except json.JSONDecodeError:
                    return secret
            
            return None
        except ImportError:
            logger.error("Módulo boto3 não instalado. Instale com 'pip install boto3'")
            return None
        except Exception as e:
            logger.error(f"Erro ao acessar AWS Secrets Manager: {str(e)}")
            return None

    def _get_from_azure_keyvault(self, key: str) -> Optional[str]:
        """Obtém credencial do Azure Key Vault."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            # Obter URL do Key Vault
            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            if not vault_url:
                logger.error("AZURE_KEYVAULT_URL não definida")
                return None
            
            # Criar cliente do Key Vault
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            
            # Obter o segredo
            secret = client.get_secret(key)
            return secret.value
        except ImportError:
            logger.error("Módulos Azure não instalados. Instale com 'pip install azure-keyvault-secrets azure-identity'")
            return None
        except Exception as e:
            logger.error(f"Erro ao acessar Azure Key Vault: {str(e)}")
            return None

    def _get_from_gcp_secrets(self, key: str) -> Optional[str]:
        """Obtém credencial do Google Cloud Secret Manager."""
        try:
            from google.cloud import secretmanager
            
            # Obter ID do projeto
            project_id = os.getenv("GCP_PROJECT_ID")
            if not project_id:
                logger.error("GCP_PROJECT_ID não definida")
                return None
            
            # Criar cliente do Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            
            # Construir nome do segredo
            name = f"projects/{project_id}/secrets/{key}/versions/latest"
            
            # Acessar o segredo
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except ImportError:
            logger.error("Módulo google-cloud-secret-manager não instalado. Instale com 'pip install google-cloud-secret-manager'")
            return None
        except Exception as e:
            logger.error(f"Erro ao acessar GCP Secret Manager: {str(e)}")
            return None

    def _get_from_sops(self, key: str) -> Optional[str]:
        """Obtém credencial de arquivo .env criptografado com SOPS."""
        if not self.sops_file:
            logger.error("Arquivo SOPS não configurado")
            return None
            
        if not Path(self.sops_file).exists():
            logger.error(f"Arquivo SOPS não encontrado: {self.sops_file}")
            return None
            
        try:
            # Executar SOPS para descriptografar o arquivo
            result = subprocess.run(
                ["sops", "-d", self.sops_file],
                capture_output=True,
                text=True,
                check=True,
            )
            
            # Processar saída como .env
            for line in result.stdout.splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip()
            
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar SOPS: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Erro ao processar arquivo SOPS: {str(e)}")
            return None

    def set_credential(self, key: str, value: str) -> bool:
        """Define uma credencial na fonte configurada.
        
        Parameters
        ----------
        key : str
            Nome da credencial a ser definida
        value : str
            Valor da credencial
            
        Returns
        -------
        bool
            True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            if self.credential_source == CredentialSource.KEYRING:
                keyring.set_password(self.app_name, key, value)
                return True
            elif self.credential_source == CredentialSource.ENV:
                # Não é possível definir variáveis de ambiente permanentemente
                logger.warning("Não é possível definir credenciais permanentemente em variáveis de ambiente")
                os.environ[key] = value
                return True
            else:
                logger.warning(f"Definição de credenciais não implementada para {self.credential_source}")
                return False
        except Exception as e:
            logger.error(f"Erro ao definir credencial {key}: {str(e)}")
            return False


def load_credentials(credential_source: str = "env") -> Dict[str, str]:
    """Carrega todas as credenciais necessárias para o Restic.
    
    Parameters
    ----------
    credential_source : str
        Fonte para obtenção de credenciais (env, keyring, aws_secrets, azure_keyvault, gcp_secrets, sops)
        
    Returns
    -------
    Dict[str, str]
        Dicionário com as credenciais carregadas
    """
    # Credenciais necessárias para o Restic
    required_keys = [
        "RESTIC_PASSWORD",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AZURE_ACCOUNT_NAME",
        "AZURE_ACCOUNT_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_PROJECT_ID",
    ]
    
    # Inicializar gerenciador de credenciais
    manager = CredentialManager(
        credential_source=credential_source,
        fallback_to_env=True,
        sops_file=os.getenv("SOPS_FILE"),
    )
    
    # Carregar credenciais
    credentials = {}
    for key in required_keys:
        value = manager.get_credential(key)
        if value:
            credentials[key] = value
    
    return credentials


def get_credential(key: str, credential_source: str = "env") -> Optional[str]:
    """Obtém uma credencial específica de forma segura.
    
    Parameters
    ----------
    key : str
        Nome da credencial a ser obtida
    credential_source : str
        Fonte para obtenção de credenciais
        
    Returns
    -------
    Optional[str]
        Valor da credencial ou None se não encontrada
    """
    manager = CredentialManager(credential_source=credential_source)
    return manager.get_credential(key)