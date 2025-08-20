#!/usr/bin/env python3
"""Script para detectar automaticamente a melhor fonte de credenciais."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def detect_best_credential_source():
    """Detecta a melhor fonte de credenciais para o ambiente atual."""
    
    # Verificar se keyring está disponível
    try:
        import keyring
        keyring_available = True
        
        # Testar se o keyring funciona
        try:
            backend = keyring.get_keyring()
            # Testar com uma chave temporária
            test_key = "__test_key__"
            test_value = "test"
            keyring.set_password("test_app", test_key, test_value)
            retrieved = keyring.get_password("test_app", test_key)
            keyring.delete_password("test_app", test_key)
            
            keyring_functional = (retrieved == test_value)
        except Exception:
            keyring_functional = False
            
    except ImportError:
        keyring_available = False
        keyring_functional = False
    
    # Verificar se há interface gráfica (importante para keyring no Linux)
    gui_available = os.getenv('DISPLAY') is not None or os.name == 'nt'
    
    # Verificar se estamos em um ambiente de CI/CD
    ci_environment = any([
        os.getenv('CI'),
        os.getenv('GITHUB_ACTIONS'),
        os.getenv('GITLAB_CI'),
        os.getenv('JENKINS_URL'),
        os.getenv('TRAVIS'),
        os.getenv('CIRCLECI')
    ])
    
    # Verificar se estamos em um container
    in_container = (
        os.path.exists('/.dockerenv') or
        os.getenv('container') is not None
    )
    
    # Lógica de detecção
    if ci_environment or in_container:
        return "env", "Ambiente CI/CD ou container detectado"
    
    if keyring_available and keyring_functional and gui_available:
        return "keyring", "Keyring funcional com GUI disponível"
    
    if keyring_available and not keyring_functional:
        return "env", "Keyring disponível mas não funcional"
    
    if not keyring_available:
        return "env", "Keyring não disponível"
    
    if not gui_available:
        return "env", "Sem interface gráfica (keyring pode não funcionar)"
    
    # Fallback
    return "env", "Usando fallback padrão"

def update_env_file(credential_source, reason):
    """Atualiza o arquivo .env com a fonte de credenciais detectada."""
    env_file = Path(".env")
    
    if not env_file.exists():
        # Copiar do exemplo se não existir
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print(f"✅ Arquivo .env criado a partir de .env.example")
        else:
            # Criar arquivo básico
            env_file.touch()
            print(f"✅ Arquivo .env criado")
    
    # Atualizar CREDENTIAL_SOURCE
    set_key(str(env_file), "CREDENTIAL_SOURCE", credential_source)
    print(f"✅ CREDENTIAL_SOURCE definido como '{credential_source}' no .env")
    print(f"   Razão: {reason}")

def main():
    print("=== Detecção Automática de Fonte de Credenciais ===")
    print()
    
    # Carregar .env atual
    load_dotenv()
    current_source = os.getenv('CREDENTIAL_SOURCE')
    
    if current_source:
        print(f"CREDENTIAL_SOURCE atual: {current_source}")
    else:
        print("CREDENTIAL_SOURCE não definido")
    
    print()
    print("=== Analisando ambiente ===")
    
    # Detectar melhor fonte
    detected_source, reason = detect_best_credential_source()
    
    print(f"Fonte recomendada: {detected_source}")
    print(f"Razão: {reason}")
    
    # Verificar se precisa atualizar
    if current_source != detected_source:
        print()
        response = input(f"Deseja atualizar CREDENTIAL_SOURCE para '{detected_source}'? (s/N): ")
        
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            update_env_file(detected_source, reason)
        else:
            print("Mantendo configuração atual")
    else:
        print("✅ Configuração atual já está otimizada")
    
    # Mostrar próximos passos
    print()
    print("=== Próximos passos ===")
    
    if detected_source == "keyring":
        print("1. Configure suas credenciais no keyring:")
        print("   make setup-credentials-keyring")
        print("2. Teste a configuração:")
        print("   python debug_keyring_linux.py")
    else:
        print("1. Configure suas credenciais no arquivo .env:")
        print("   make setup-credentials-env")
        print("2. Ou configure interativamente:")
        print("   make setup-credentials")
    
    print("3. Valide a configuração:")
    print("   make check")

if __name__ == "__main__":
    main()