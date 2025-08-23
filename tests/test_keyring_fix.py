#!/usr/bin/env python3
"""Script de teste para verificar se o keyring está funcionando corretamente após as correções."""

import sys
import logging
from services.credentials import CredentialManager, get_manager

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_keyring_import():
    """Testa se o keyring pode ser importado."""
    try:
        import keyring
        version = getattr(keyring, "__version__", "unknown")
        logger.info(f"✅ Keyring importado com sucesso: {version}")
        return True
    except ImportError as e:
        logger.error(f"❌ Falha ao importar keyring: {e}")
        return False

def test_keyring_backend():
    """Testa qual backend do keyring está sendo usado."""
    try:
        import keyring
        backend = keyring.get_keyring()
        logger.info(f"✅ Backend do keyring: {backend}")
        
        # Verificar se é um backend funcional
        if 'fail' in str(backend).lower():
            logger.warning("⚠️ Backend de falha detectado - keyring pode não funcionar")
            return False
        else:
            logger.info("✅ Backend funcional detectado")
            return True
    except Exception as e:
        logger.error(f"❌ Erro ao verificar backend: {e}")
        return False

def test_credential_manager():
    """Testa o CredentialManager com diferentes fontes."""
    logger.info("Testando CredentialManager...")
    
    # Teste com fonte ENV (deve sempre funcionar)
    try:
        manager_env = CredentialManager(credential_source="env")
        logger.info("✅ CredentialManager com fonte ENV criado")
    except Exception as e:
        logger.error(f"❌ Erro ao criar CredentialManager ENV: {e}")
        return False
    
    # Teste com fonte KEYRING
    try:
        manager_keyring = CredentialManager(credential_source="keyring")
        logger.info("✅ CredentialManager com fonte KEYRING criado")
        
        # Tentar obter uma credencial (deve retornar None graciosamente)
        test_cred = manager_keyring.get_credential("TEST_KEY")
        logger.info(f"✅ Teste de obtenção de credencial: {test_cred is None}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao testar CredentialManager KEYRING: {e}")
        return False

def test_get_manager_function():
    """Testa a obtenção de credenciais via get_manager."""
    try:
        # Teste com fonte ENV
        cred = get_manager("env").get_credential("PATH")  # PATH deve existir
        logger.info(f"✅ get_manager ENV funciona: {cred is not None}")

        # Teste com fonte KEYRING
        cred = get_manager("keyring").get_credential("TEST_KEY")
        logger.info(f"✅ get_manager KEYRING funciona: {cred is None}")

        return True
    except Exception as e:
        logger.error(f"❌ Erro ao testar get_manager/get_credential: {e}")
        return False

def main():
    """Executa todos os testes."""
    logger.info("=== TESTE DE CORREÇÃO DO KEYRING ===")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Plataforma: {sys.platform}")
    
    tests = [
        ("Importação do keyring", test_keyring_import),
        ("Backend do keyring", test_keyring_backend),
        ("CredentialManager", test_credential_manager),
        ("Função get_manager", test_get_manager_function),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    logger.info("\n=== RESUMO DOS TESTES ===")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 Todos os testes passaram! O keyring está funcionando corretamente.")
        return 0
    else:
        logger.warning("\n⚠️ Alguns testes falharam, mas o sistema deve funcionar com fallback para .env")
        return 1

if __name__ == "__main__":
    sys.exit(main())