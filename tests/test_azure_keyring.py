#!/usr/bin/env python3
"""
Script para testar carregamento de credenciais Azure do keyring no Linux
Este script ajuda a diagnosticar problemas específicos com keyring no Linux
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv não instalado. Execute: pip install python-dotenv")
    sys.exit(1)

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    print("❌ keyring não instalado. Execute: pip install keyring")
    KEYRING_AVAILABLE = False

try:
    from services.credentials import get_credential, CredentialManager
    from services.restic import load_restic_config
except ImportError as e:
    print(f"❌ Erro ao importar módulos SafeStic: {e}")
    sys.exit(1)

def test_environment():
    """Testa o ambiente básico"""
    print("🔍 TESTE DE AMBIENTE")
    print("=" * 50)
    
    # Sistema operacional
    print(f"Sistema: {os.name} - {sys.platform}")
    print(f"Python: {sys.version}")
    
    # Keyring disponível
    if KEYRING_AVAILABLE:
        print("✅ Keyring: Disponível")
        try:
            backend = keyring.get_keyring()
            print(f"   Backend: {backend.__class__.__name__}")
        except Exception as e:
            print(f"⚠️  Backend keyring: {e}")
    else:
        print("❌ Keyring: Não disponível")
        return False
    
    return True

def test_env_loading():
    """Testa carregamento do arquivo .env"""
    print("\n🔍 TESTE DE CARREGAMENTO .ENV")
    print("=" * 50)
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado")
        return False
    
    print("✅ Arquivo .env encontrado")
    
    # Carregar .env
    load_dotenv()
    
    # Verificar variáveis importantes
    important_vars = [
        'STORAGE_PROVIDER',
        'STORAGE_BUCKET', 
        'CREDENTIAL_SOURCE'
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Não definida")
    
    credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
    return credential_source

def test_keyring_access():
    """Testa acesso ao keyring"""
    print("\n🔍 TESTE DE ACESSO AO KEYRING")
    print("=" * 50)
    
    if not KEYRING_AVAILABLE:
        print("❌ Keyring não disponível")
        return False
    
    app_name = os.getenv('APP_NAME', 'safestic')
    print(f"App name: {app_name}")
    
    # Testar escrita e leitura
    test_key = "TEST_AZURE_KEYRING"
    test_value = "test_value_123"
    
    try:
        # Escrever
        keyring.set_password(app_name, test_key, test_value)
        print(f"✅ Escrita no keyring: OK")
        
        # Ler
        retrieved = keyring.get_password(app_name, test_key)
        if retrieved == test_value:
            print(f"✅ Leitura do keyring: OK")
        else:
            print(f"❌ Leitura do keyring: Valor incorreto")
            return False
        
        # Limpar
        keyring.delete_password(app_name, test_key)
        print(f"✅ Limpeza do keyring: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no keyring: {e}")
        return False

def test_azure_credentials():
    """Testa carregamento de credenciais Azure"""
    print("\n🔍 TESTE DE CREDENCIAIS AZURE")
    print("=" * 50)
    
    credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
    print(f"Fonte de credenciais: {credential_source}")
    
    azure_creds = [
        'AZURE_ACCOUNT_NAME',
        'AZURE_ACCOUNT_KEY',
        'RESTIC_PASSWORD'
    ]
    
    success = True
    for cred in azure_creds:
        try:
            value = get_credential(cred, credential_source)
            if value:
                print(f"✅ {cred}: Carregada (***mascarada***)")
            else:
                print(f"❌ {cred}: Não encontrada")
                success = False
        except Exception as e:
            print(f"❌ {cred}: Erro - {e}")
            success = False
    
    return success

def test_restic_config():
    """Testa carregamento da configuração Restic"""
    print("\n🔍 TESTE DE CONFIGURAÇÃO RESTIC")
    print("=" * 50)
    
    credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
    
    try:
        config = load_restic_config(credential_source)
        print(f"✅ Configuração carregada com sucesso")
        print(f"   Storage Provider: {config.storage_provider}")
        print(f"   Storage Bucket: {config.storage_bucket}")
        print(f"   Credential Source: {config.credential_source}")
        print(f"   Password: {'***definida***' if config.restic_password else 'NÃO DEFINIDA'}")
        
        return config.restic_password is not None
        
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO AZURE KEYRING - SafeStic")
    print("Este script testa o carregamento de credenciais Azure do keyring no Linux")
    print()
    
    all_tests_passed = True
    
    # Executar testes
    tests = [
        ("Ambiente", test_environment),
        ("Carregamento .env", test_env_loading),
        ("Acesso ao Keyring", test_keyring_access),
        ("Credenciais Azure", test_azure_credentials),
        ("Configuração Restic", test_restic_config)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_tests_passed = False
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("As credenciais Azure devem estar funcionando corretamente.")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("Verifique os erros acima e consulte a documentação.")
        return 1

if __name__ == '__main__':
    sys.exit(main())