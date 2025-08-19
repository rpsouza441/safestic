#!/usr/bin/env python3
"""
Script para configuração interativa de credenciais do Safestic.

Este script permite configurar de forma segura:
- RESTIC_PASSWORD (obrigatório para criptografia)
- Credenciais específicas do provedor de nuvem (AWS, Azure, GCP)

Suporta diferentes fontes de credenciais:
- keyring: Armazenamento seguro no sistema
- env: Arquivo .env (menos seguro, mas prático para desenvolvimento)

Uso:
    python scripts/setup_credentials.py                    # Configuração interativa completa
    python scripts/setup_credentials.py --restic-only      # Apenas RESTIC_PASSWORD
    python scripts/setup_credentials.py --source keyring   # Forçar uso do keyring
    python scripts/setup_credentials.py --source env       # Forçar uso do .env
"""

import os
import sys
import getpass
import re
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import keyring
except ImportError:
    print("  Aviso: keyring não está instalado. Instale com: pip install keyring")
    keyring = None

try:
    from dotenv import load_dotenv
except ImportError:
    print("  Aviso: python-dotenv não está instalado. Instale com: pip install python-dotenv")
    load_dotenv = None


def load_env_config() -> Dict[str, str]:
    """Carrega configurações do arquivo .env."""
    env_file = project_root / '.env'
    config = {}
    
    if env_file.exists():
        if load_dotenv:
            load_dotenv(env_file)
        
        # Ler manualmente se dotenv não estiver disponível
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
    
    return config


def detect_required_credentials() -> List[str]:
    """Detecta quais credenciais são necessárias baseado na configuração."""
    config = load_env_config()
    required = ['RESTIC_PASSWORD']  # Sempre necessário
    
    storage_provider = config.get('STORAGE_PROVIDER', '').lower()
    
    if storage_provider == 'aws' or storage_provider == 's3':
        required.extend(['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'])
        if config.get('AWS_SESSION_TOKEN'):
            required.append('AWS_SESSION_TOKEN')
    
    elif storage_provider == 'azure':
        required.extend(['AZURE_ACCOUNT_NAME', 'AZURE_ACCOUNT_KEY'])
    
    elif storage_provider == 'gcp' or storage_provider == 'gs':
        if config.get('GOOGLE_APPLICATION_CREDENTIALS'):
            required.append('GOOGLE_APPLICATION_CREDENTIALS')
        else:
            required.extend(['GOOGLE_PROJECT_ID', 'GOOGLE_APPLICATION_CREDENTIALS'])
    
    return required


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Valida a força da senha do Restic."""
    if len(password) < 12:
        return False, "Senha deve ter pelo menos 12 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, "Senha forte"


def choose_credential_source(non_interactive: bool = False) -> Optional[str]:
    """Permite ao usuário escolher a fonte de credenciais."""
    if non_interactive:
        return 'keyring' if keyring else 'env'
    
    print("\n Escolha a fonte para armazenar as credenciais:")
    print("\n1.  Keyring do Sistema (Recomendado)")
    print("   - Mais seguro")
    print("   - Credenciais criptografadas pelo SO")
    print("   - Não ficam em arquivos de texto")
    
    print("\n2.  Arquivo .env")
    print("   - Menos seguro")
    print("   - Prático para desenvolvimento")
    print("   -   Não commitar no git!")
    
    while True:
        choice = input("\nEscolha (1-2): ").strip()
        
        if choice == '1':
            if not keyring:
                print(" Keyring não está disponível. Instale com: pip install keyring")
                continue
            return 'keyring'
        elif choice == '2':
            return 'env'
        else:
            print(" Opção inválida. Digite 1 ou 2.")


def setup_restic_password(source: str, non_interactive: bool = False) -> bool:
    """Configura o RESTIC_PASSWORD."""
    print("\n🔑 Configuração do RESTIC_PASSWORD")
    print("-" * 40)
    
    print("\n  IMPORTANTE: Esta senha é usada para criptografar seus backups!")
    print("   - Escolha uma senha FORTE e ÚNICA")
    print("   - GUARDE esta senha em local seguro")
    print("   - SEM esta senha, você NÃO conseguirá restaurar seus backups")
    
    # Obter APP_NAME do .env
    if load_dotenv:
        load_dotenv()
    app_name = os.getenv('APP_NAME', 'safestic')
    
    # Aviso sobre APP_NAME para keyring
    if source == 'keyring':
        print(f"\n  📝 NOTA: Usando identificador '{app_name}' no keyring do sistema")
        if app_name == 'safestic':
            print("     ⚠️  ATENÇÃO: Se você tem múltiplos projetos Safestic, configure")
            print("        APP_NAME=nome-unico no arquivo .env para evitar conflitos!")
        print("     Exemplo: APP_NAME=safestic-projeto-aws")
    
    if not non_interactive:
        input("\nPressione Enter para continuar...")
    
    # Verificar se já existe
    existing_password = None
    if source == 'keyring' and keyring:
        try:
            existing_password = keyring.get_password(app_name, 'RESTIC_PASSWORD')
        except Exception:
            pass
    elif source == 'env':
        config = load_env_config()
        existing_password = config.get('RESTIC_PASSWORD')
    
    if existing_password and not non_interactive:
        print(f"\n✅ RESTIC_PASSWORD já está configurado para '{app_name}'.")
        overwrite = input("Deseja sobrescrever? (s/N): ").strip().lower()
        if overwrite not in ['s', 'sim', 'y', 'yes']:
            return True
    
    # Solicitar nova senha
    while True:
        if non_interactive:
            print(" Modo não interativo requer senha pré-configurada")
            return False
        
        password = getpass.getpass("\nDigite o RESTIC_PASSWORD: ")
        
        if not password:
            print(" Senha não pode estar vazia")
            continue
        
        # Validar força da senha
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            print(f" {message}")
            print("\n Exemplo de senha forte: MinhaSenh@Muito$egura123!")
            continue
        
        # Confirmar senha
        confirm = getpass.getpass("Confirme o RESTIC_PASSWORD: ")
        if password != confirm:
            print(" Senhas não coincidem")
            continue
        
        break
    
    # Salvar senha
    try:
        if source == 'keyring' and keyring:
            keyring.set_password(app_name, 'RESTIC_PASSWORD', password)
            print(f" RESTIC_PASSWORD salvo no keyring do sistema para '{app_name}'")
        
        elif source == 'env':
            env_file = project_root / '.env'
            
            # Ler arquivo existente
            lines = []
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Atualizar ou adicionar RESTIC_PASSWORD
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith('RESTIC_PASSWORD='):
                    lines[i] = f'RESTIC_PASSWORD="{password}"\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'RESTIC_PASSWORD="{password}"\n')
            
            # Salvar arquivo
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f" RESTIC_PASSWORD salvo em {env_file}")
            print("  LEMBRE-SE: Não commite o arquivo .env no git!")
        
        return True
    
    except Exception as e:
        print(f" Erro ao salvar RESTIC_PASSWORD: {e}")
        return False


def setup_cloud_credentials(required_creds: List[str], source: str, non_interactive: bool = False) -> bool:
    """Configura credenciais específicas do provedor de nuvem."""
    config = load_env_config()
    storage_provider = config.get('STORAGE_PROVIDER', '').lower()
    
    print(f"\n  Configuração de credenciais para {storage_provider.upper()}")
    print("-" * 50)
    
    if storage_provider in ['aws', 's3']:
        return setup_aws_credentials(required_creds, source, non_interactive)
    elif storage_provider == 'azure':
        return setup_azure_credentials(required_creds, source, non_interactive)
    elif storage_provider in ['gcp', 'gs']:
        return setup_gcp_credentials(required_creds, source, non_interactive)
    else:
        print(f" Provedor não suportado: {storage_provider}")
        return False


def setup_aws_credentials(required_creds: List[str], source: str, non_interactive: bool = False) -> bool:
    """Configura credenciais AWS."""
    print("\n📚 Para obter credenciais AWS:")
    print("   1. Acesse: https://console.aws.amazon.com/iam/")
    print("   2. Vá em 'Users' > seu usuário > 'Security credentials'")
    print("   3. Clique em 'Create access key'")
    
    if non_interactive:
        print(" Modo não interativo não suportado para credenciais AWS")
        return False
    
    credentials = {}
    
    for cred in required_creds:
        if cred == 'RESTIC_PASSWORD':
            continue
        
        if cred == 'AWS_ACCESS_KEY_ID':
            value = input(f"\nDigite {cred}: ").strip()
        elif cred == 'AWS_SECRET_ACCESS_KEY':
            value = getpass.getpass(f"Digite {cred}: ")
        else:
            value = input(f"Digite {cred} (opcional): ").strip()
        
        if value:
            credentials[cred] = value
    
    return save_credentials(credentials, source)


def setup_azure_credentials(required_creds: List[str], source: str, non_interactive: bool = False) -> bool:
    """Configura credenciais Azure."""
    print("\n Para obter credenciais Azure:")
    print("   1. Acesse: https://portal.azure.com/")
    print("   2. Vá em 'Storage accounts' > sua conta")
    print("   3. Em 'Access keys', copie o nome da conta e uma das chaves")
    
    if non_interactive:
        print(" Modo não interativo não suportado para credenciais Azure")
        return False
    
    credentials = {}
    
    for cred in required_creds:
        if cred == 'RESTIC_PASSWORD':
            continue
        
        if cred == 'AZURE_ACCOUNT_NAME':
            value = input(f"\nDigite {cred}: ").strip()
        elif cred == 'AZURE_ACCOUNT_KEY':
            value = getpass.getpass(f"Digite {cred}: ")
        else:
            value = input(f"Digite {cred}: ").strip()
        
        if value:
            credentials[cred] = value
    
    return save_credentials(credentials, source)


def setup_gcp_credentials(required_creds: List[str], source: str, non_interactive: bool = False) -> bool:
    """Configura credenciais GCP."""
    print("\n Para obter credenciais GCP:")
    print("   1. Acesse: https://console.cloud.google.com/")
    print("   2. Vá em 'IAM & Admin' > 'Service Accounts'")
    print("   3. Crie uma service account e baixe o arquivo JSON")
    
    if non_interactive:
        print(" Modo não interativo não suportado para credenciais GCP")
        return False
    
    credentials = {}
    
    for cred in required_creds:
        if cred == 'RESTIC_PASSWORD':
            continue
        
        if cred == 'GOOGLE_APPLICATION_CREDENTIALS':
            value = input(f"\nDigite o caminho para {cred}: ").strip()
            if value and not Path(value).exists():
                print(f"  Arquivo não encontrado: {value}")
        else:
            value = input(f"Digite {cred}: ").strip()
        
        if value:
            credentials[cred] = value
    
    return save_credentials(credentials, source)


def save_credentials(credentials: Dict[str, str], source: str) -> bool:
    """Salva credenciais na fonte especificada."""
    try:
        if source == 'keyring' and keyring:
            # Obter APP_NAME do .env
            if load_dotenv:
                load_dotenv()
            app_name = os.getenv('APP_NAME', 'safestic')
            
            for key, value in credentials.items():
                keyring.set_password(app_name, key, value)
            print(f" Credenciais salvas no keyring do sistema para '{app_name}'")
        
        elif source == 'env':
            env_file = project_root / '.env'
            
            # Ler arquivo existente
            lines = []
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Atualizar ou adicionar credenciais
            for key, value in credentials.items():
                updated = False
                for i, line in enumerate(lines):
                    if line.strip().startswith(f'{key}='):
                        lines[i] = f'{key}="{value}"\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'{key}="{value}"\n')
            
            # Salvar arquivo
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f" Credenciais salvas em {env_file}")
        
        return True
    
    except Exception as e:
        print(f" Erro ao salvar credenciais: {e}")
        return False


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Configuração interativa de credenciais do Safestic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                    # Configuração interativa completa
  %(prog)s --restic-only      # Apenas RESTIC_PASSWORD
  %(prog)s --source keyring   # Forçar uso do keyring
  %(prog)s --source env       # Forçar uso do .env

Fontes de credenciais suportadas:
  keyring - Armazenamento seguro no sistema (recomendado)
  env     - Arquivo .env (menos seguro, mas prático)
"""
    )
    
    parser.add_argument(
        '--restic-only',
        action='store_true',
        help='Configurar apenas o RESTIC_PASSWORD'
    )
    
    parser.add_argument(
        '--source',
        choices=['keyring', 'env'],
        help='Forçar uma fonte específica de credenciais'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Modo não interativo (para scripts)'
    )
    
    return parser.parse_args()


def main():
    """Função principal do script de configuração de credenciais."""
    args = parse_arguments()
    
    print(" Configuração de Credenciais do Safestic")
    print("=" * 50)
    
    # Verificar se keyring está disponível
    if not keyring and (not args.source or args.source == 'keyring'):
        print("  Keyring não está disponível. Usando arquivo .env como fallback.")
        if not args.source:
            args.source = 'env'
    
    # Detectar credenciais necessárias
    required_creds = detect_required_credentials()
    
    if not required_creds:
        print(" Não foi possível detectar as credenciais necessárias.")
        print("   Verifique se o arquivo .env está configurado corretamente.")
        return 1
    
    if args.restic_only:
        required_creds = ['RESTIC_PASSWORD']
        print("\n Configurando apenas RESTIC_PASSWORD")
    else:
        print(f"\n Credenciais detectadas como necessárias: {', '.join(required_creds)}")
    
    # Determinar fonte de credenciais
    credential_source = args.source or choose_credential_source(args.non_interactive)
    
    if not credential_source:
        print(" Nenhuma fonte de credenciais selecionada")
        return 1
    
    print(f"\n Usando fonte de credenciais: {credential_source}")
    
    # Configurar RESTIC_PASSWORD
    if not setup_restic_password(credential_source, args.non_interactive):
        print(" Falha ao configurar RESTIC_PASSWORD")
        return 1
    
    # Configurar credenciais do provedor de nuvem (se não for restic-only)
    if not args.restic_only and len(required_creds) > 1:
        cloud_creds = [cred for cred in required_creds if cred != 'RESTIC_PASSWORD']
        if not setup_cloud_credentials(cloud_creds, credential_source, args.non_interactive):
            print(" Falha ao configurar credenciais da nuvem")
            return 1
    
    print("\n Configuração de credenciais concluída com sucesso!")
    print("\n Próximos passos:")
    print("   1. Execute 'make check' para verificar a configuração")
    print("   2. Execute 'make init' para inicializar o repositório Restic")
    print("   3. Execute 'make backup' para fazer seu primeiro backup")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())