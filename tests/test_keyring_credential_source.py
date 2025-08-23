#!/usr/bin/env python3
"""
Script para testar se o CREDENTIAL_SOURCE está sendo lido corretamente
e se a RESTIC_PASSWORD está sendo carregada do keyring.
"""

import os
from dotenv import load_dotenv
from services.restic import load_restic_config
from services.credentials import get_credential
from services.env import get_credential_source

def test_credential_source():
    """Testa se o CREDENTIAL_SOURCE está sendo lido corretamente"""
    print("=== Teste de CREDENTIAL_SOURCE ===")
    
    # Carregar .env
    load_dotenv()
    
    # Verificar CREDENTIAL_SOURCE
    credential_source = get_credential_source()
    print(f"✓ CREDENTIAL_SOURCE detectado: {credential_source}")
    
    # Testar carregamento da senha
    try:
        password = get_credential('RESTIC_PASSWORD', credential_source)
        if password:
            print(f"✓ RESTIC_PASSWORD carregada com sucesso do {credential_source}")
            print(f"  Senha: {'*' * len(password)} (mascarada)")
        else:
            print(f"✗ RESTIC_PASSWORD não encontrada no {credential_source}")
            return False
    except Exception as e:
        print(f"✗ Erro ao carregar RESTIC_PASSWORD: {e}")
        return False
    
    # Testar carregamento da configuração completa
    try:
        config = load_restic_config(credential_source)
        print(f"✓ Configuração Restic carregada com sucesso")
        print(f"  Storage Provider: {config.storage_provider}")
        print(f"  Storage Bucket: {config.storage_bucket}")
        print(f"  Credential Source: {config.credential_source}")
        return True
    except Exception as e:
        print(f"✗ Erro ao carregar configuração Restic: {e}")
        return False

if __name__ == "__main__":
    success = test_credential_source()
    if success:
        print("\n🎉 Todos os testes passaram! O CREDENTIAL_SOURCE está funcionando corretamente.")
        exit(0)
    else:
        print("\n❌ Alguns testes falharam. Verifique a configuração.")
        exit(1)