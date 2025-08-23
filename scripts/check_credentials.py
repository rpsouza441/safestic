#!/usr/bin/env python3
"""
Script para verificar se as credenciais necessarias estao configuradas.

Este script verifica se RESTIC_PASSWORD e outras credenciais necessarias
estao configuradas antes de executar operacoes que requerem acesso ao repositorio.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Adiciona o diretorio raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.credentials import get_credential
except ImportError:
    get_credential = None

from services.restic_client import load_env_and_get_credential_source

credential_source = load_env_and_get_credential_source().lower()


def check_restic_password() -> Tuple[bool, str]:
    """Verifica se RESTIC_PASSWORD esta configurado.
    
    Returns:
        Tuple[bool, str]: (configurado, mensagem)
    """
    # Tentar obter da fonte configurada
    if get_credential:
        try:
            password = get_credential('RESTIC_PASSWORD', credential_source)
            if password:
                if credential_source == 'keyring':
                    return True, "RESTIC_PASSWORD configurado no keyring do sistema"
                elif credential_source in ['aws_secrets', 'azure_keyvault', 'gcp_secrets']:
                    return True, f"RESTIC_PASSWORD configurado no {credential_source}"
                elif credential_source == 'sops':
                    return True, "RESTIC_PASSWORD configurado no arquivo SOPS"
                else:
                    return True, "RESTIC_PASSWORD configurado no arquivo .env"
        except Exception:
            pass
    
    # Fallback para ambiente (sempre verifica .env como fallback)
    password = os.getenv('RESTIC_PASSWORD')
    if password and password.strip():
        return True, "RESTIC_PASSWORD configurado no arquivo .env"
    
    return False, "RESTIC_PASSWORD nao configurado"


def check_cloud_credentials() -> Tuple[bool, List[str]]:
    """Verifica credenciais especificas do provedor de nuvem.
    
    Returns:
        Tuple[bool, List[str]]: (todas_configuradas, lista_de_mensagens)
    """
    provider = os.getenv('STORAGE_PROVIDER', '').lower()
    messages = []
    all_configured = True
    
    if provider == 'aws':
        # Tentar obter da fonte configurada primeiro
        aws_key = None
        aws_secret = None
        
        if get_credential:
            try:
                aws_key = get_credential('AWS_ACCESS_KEY_ID', credential_source)
                aws_secret = get_credential('AWS_SECRET_ACCESS_KEY', credential_source)
            except Exception:
                pass
        
        # Fallback para variáveis de ambiente
        if not aws_key:
            aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        if not aws_secret:
            aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not aws_key:
            messages.append("AWS_ACCESS_KEY_ID nao configurado")
            all_configured = False
        else:
            if credential_source == 'keyring':
                messages.append("AWS_ACCESS_KEY_ID configurado no keyring")
            else:
                messages.append("AWS_ACCESS_KEY_ID configurado")
            
        if not aws_secret:
            messages.append("AWS_SECRET_ACCESS_KEY nao configurado")
            all_configured = False
        else:
            if credential_source == 'keyring':
                messages.append("AWS_SECRET_ACCESS_KEY configurado no keyring")
            else:
                messages.append("AWS_SECRET_ACCESS_KEY configurado")
            
    elif provider == 'azure':
        azure_name = None
        azure_key = None

        if get_credential:
            try:
                azure_name = get_credential('AZURE_ACCOUNT_NAME', credential_source)
                azure_key = get_credential('AZURE_ACCOUNT_KEY', credential_source)
            except Exception:
                pass

        if not azure_name:
            azure_name = os.getenv('AZURE_ACCOUNT_NAME')
        if not azure_key:
            azure_key = os.getenv('AZURE_ACCOUNT_KEY')

        if not azure_name:
            messages.append("AZURE_ACCOUNT_NAME nao configurado")
            all_configured = False
        else:
            messages.append("AZURE_ACCOUNT_NAME configurado")

        if not azure_key:
            messages.append("AZURE_ACCOUNT_KEY nao configurado")
            all_configured = False
        else:
            messages.append("AZURE_ACCOUNT_KEY configurado")

    elif provider == 'gcp':
        gcp_project = None
        gcp_creds = None

        if get_credential:
            try:
                gcp_project = get_credential('GOOGLE_PROJECT_ID', credential_source)
                gcp_creds = get_credential('GOOGLE_APPLICATION_CREDENTIALS', credential_source)
            except Exception:
                pass

        if not gcp_project:
            gcp_project = os.getenv('GOOGLE_PROJECT_ID')
        if not gcp_creds:
            gcp_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        if not gcp_project:
            messages.append("GOOGLE_PROJECT_ID nao configurado")
            all_configured = False
        else:
            messages.append("GOOGLE_PROJECT_ID configurado")

        if not gcp_creds or not Path(gcp_creds).exists():
            messages.append("GOOGLE_APPLICATION_CREDENTIALS nao configurado ou arquivo nao encontrado")
            all_configured = False
        else:
            messages.append("GOOGLE_APPLICATION_CREDENTIALS configurado")
            
    elif provider == 'local':
        messages.append("Provedor local - credenciais de nuvem nao necessarias")
        # Para provedor local, consideramos as credenciais como configuradas
        # pois não precisamos de credenciais de nuvem
    else:
        messages.append(f"Provedor desconhecido: {provider}")
        all_configured = False
    
    return all_configured, messages


def check_all_credentials(verbose: bool = True) -> bool:
    """Verifica todas as credenciais necessarias.
    
    Args:
        verbose: Se True, imprime mensagens detalhadas
        
    Returns:
        bool: True se todas as credenciais estao configuradas
    """
    all_ok = True
    
    # Verificar RESTIC_PASSWORD
    password_ok, password_msg = check_restic_password()
    if verbose:
        status = "[OK]" if password_ok else "[ERRO]"
        print(f"{status} {password_msg}")
    
    if not password_ok:
        all_ok = False
        if verbose:
            print("   DICA: Configure com: make setup-restic-password")
    
    # Verificar credenciais de nuvem
    cloud_ok, cloud_messages = check_cloud_credentials()
    if verbose:
        for msg in cloud_messages:
            # Para provedor local, mostrar como OK
            if "Provedor local" in msg:
                status = "[OK]"
            else:
                status = "[OK]" if "configurado" in msg and "nao configurado" not in msg else "[ERRO]"
            print(f"{status} {msg}")
    
    if not cloud_ok:
        all_ok = False
        if verbose:
            print("   DICA: Configure com uma das opcoes:")
            print("     make setup-credentials        - Configuracao interativa")
            print("     make setup-credentials-keyring - Keyring (mais seguro)")
            print("     make setup-credentials-env    - Arquivo .env (menos seguro)")
    
    return all_ok


def main():
    """Funcao principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verifica se as credenciais necessarias estao configuradas"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true", 
        help="Modo silencioso - apenas codigo de saida"
    )
    parser.add_argument(
        "--restic-only", 
        action="store_true", 
        help="Verificar apenas RESTIC_PASSWORD"
    )
    
    args = parser.parse_args()
    
    if args.restic_only:
        password_ok, password_msg = check_restic_password()
        if not args.quiet:
            status = "[OK]" if password_ok else "[ERRO]"
            print(f"{status} {password_msg}")
            if not password_ok:
                print("   DICA: Configure com: make setup-restic-password")
        sys.exit(0 if password_ok else 1)
    else:
        all_ok = check_all_credentials(verbose=not args.quiet)
        if not args.quiet and not all_ok:
            print("\n[ERRO] Algumas credenciais nao estao configuradas.")
            print("   Execute uma das opcoes para configurar:")
            print("     make setup-credentials        - Configuracao interativa")
            print("     make setup-credentials-keyring - Keyring (mais seguro)")
            print("     make setup-credentials-env    - Arquivo .env (menos seguro)")
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()