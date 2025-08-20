#!/usr/bin/env python3
"""Script de diagnóstico para verificar o funcionamento do keyring no Linux."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import keyring
    KEYRING_AVAILABLE = True
    print("✅ Keyring disponível")
except ImportError:
    KEYRING_AVAILABLE = False
    print("❌ Keyring não disponível. Instale com: pip install keyring")
    sys.exit(1)

def main():
    print("=== Diagnóstico do Keyring no Linux ===")
    print()
    
    # Carregar .env
    load_dotenv()
    
    # Verificar CREDENTIAL_SOURCE
    credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
    print(f"CREDENTIAL_SOURCE detectado: {credential_source}")
    
    # Verificar APP_NAME
    app_name = os.getenv('APP_NAME', 'safestic')
    print(f"APP_NAME: {app_name}")
    
    # Verificar backend do keyring
    try:
        backend = keyring.get_keyring()
        print(f"Backend do keyring: {backend}")
        print(f"Tipo do backend: {type(backend).__name__}")
    except Exception as e:
        print(f"❌ Erro ao obter backend do keyring: {e}")
        return
    
    # Verificar se a senha está armazenada
    print()
    print("=== Verificando senhas armazenadas ===")
    
    keys_to_check = [
        'RESTIC_PASSWORD',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]
    
    for key in keys_to_check:
        try:
            password = keyring.get_password(app_name, key)
            if password:
                print(f"✅ {key}: *** (senha encontrada, {len(password)} caracteres)")
            else:
                print(f"❌ {key}: não encontrado")
        except Exception as e:
            print(f"❌ {key}: erro ao acessar - {e}")
    
    # Testar armazenamento e recuperação
    print()
    print("=== Teste de armazenamento/recuperação ===")
    
    test_key = "TEST_KEY"
    test_value = "test_password_123"
    
    try:
        # Armazenar
        keyring.set_password(app_name, test_key, test_value)
        print(f"✅ Senha de teste armazenada para {test_key}")
        
        # Recuperar
        retrieved = keyring.get_password(app_name, test_key)
        if retrieved == test_value:
            print(f"✅ Senha de teste recuperada corretamente")
        else:
            print(f"❌ Senha de teste não corresponde: esperado '{test_value}', obtido '{retrieved}'")
        
        # Limpar
        keyring.delete_password(app_name, test_key)
        print(f"✅ Senha de teste removida")
        
    except Exception as e:
        print(f"❌ Erro no teste de armazenamento/recuperação: {e}")
    
    # Verificar se o problema é de permissões ou configuração
    print()
    print("=== Informações do sistema ===")
    print(f"Sistema operacional: {os.name}")
    print(f"Usuário atual: {os.getenv('USER', 'desconhecido')}")
    print(f"HOME: {os.getenv('HOME', 'não definido')}")
    print(f"XDG_DATA_HOME: {os.getenv('XDG_DATA_HOME', 'não definido')}")
    print(f"DISPLAY: {os.getenv('DISPLAY', 'não definido')}")
    
    # Verificar se há keyring GUI disponível
    gui_available = os.getenv('DISPLAY') is not None
    print(f"Interface gráfica disponível: {'Sim' if gui_available else 'Não'}")
    
    if not gui_available:
        print()
        print("⚠️  AVISO: Sem interface gráfica detectada.")
        print("   No Linux, alguns backends de keyring requerem GUI.")
        print("   Considere usar CREDENTIAL_SOURCE=env em ambientes sem GUI.")

if __name__ == "__main__":
    main()