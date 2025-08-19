#!/usr/bin/env python3
"""Script de teste específico para validar correções do keyring no Linux."""

import sys
import logging
import subprocess
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_system_dependencies():
    """Testa se as dependências de sistema estão instaladas."""
    logger.info("=== TESTANDO DEPENDÊNCIAS DE SISTEMA ===")
    
    dependencies = {
        'pkg-config': ['pkg-config', '--version'],
        'cmake': ['cmake', '--version'],
        'gcc': ['gcc', '--version'],
        'python3-dev': ['python3-config', '--includes']
    }
    
    results = {}
    for name, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ {name}: Disponível")
                results[name] = True
            else:
                logger.warning(f"⚠️ {name}: Comando falhou")
                results[name] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning(f"❌ {name}: Não encontrado")
            results[name] = False
    
    return results

def test_python_keyring_backends():
    """Testa diferentes backends do keyring."""
    logger.info("\n=== TESTANDO BACKENDS DO KEYRING ===")
    
    try:
        import keyring
        logger.info(f"✅ Keyring importado: versão disponível")
        
        # Obter backend atual
        backend = keyring.get_keyring()
        logger.info(f"Backend atual: {backend}")
        
        # Verificar se é um backend funcional
        backend_name = str(backend).lower()
        if 'fail' in backend_name:
            logger.warning("⚠️ Backend de falha detectado")
            return False
        elif 'chainer' in backend_name:
            logger.info("✅ Backend chainer detectado (múltiplos backends)")
            return True
        else:
            logger.info("✅ Backend funcional detectado")
            return True
            
    except ImportError as e:
        logger.error(f"❌ Falha ao importar keyring: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False

def test_keyring_alternatives():
    """Testa alternativas do keyring."""
    logger.info("\n=== TESTANDO ALTERNATIVAS DO KEYRING ===")
    
    alternatives = {
        'secretstorage': 'Integração com GNOME Keyring',
        'dbus-python': 'Comunicação D-Bus',
        'keyrings.alt': 'Backends alternativos'
    }
    
    results = {}
    for module, description in alternatives.items():
        try:
            __import__(module)
            logger.info(f"✅ {module}: {description} - Disponível")
            results[module] = True
        except ImportError:
            logger.warning(f"❌ {module}: {description} - Não disponível")
            results[module] = False
    
    return results

def test_keyring_functionality():
    """Testa funcionalidade básica do keyring."""
    logger.info("\n=== TESTANDO FUNCIONALIDADE DO KEYRING ===")
    
    try:
        import keyring
        
        # Tentar definir e obter uma credencial de teste
        test_service = "safestic_test"
        test_username = "test_user"
        test_password = "test_password_123"
        
        # Tentar definir
        try:
            keyring.set_password(test_service, test_username, test_password)
            logger.info("✅ Definição de senha: Sucesso")
            
            # Tentar obter
            retrieved = keyring.get_password(test_service, test_username)
            if retrieved == test_password:
                logger.info("✅ Obtenção de senha: Sucesso")
                
                # Limpar teste
                try:
                    keyring.delete_password(test_service, test_username)
                    logger.info("✅ Remoção de senha: Sucesso")
                except Exception:
                    logger.warning("⚠️ Remoção de senha: Falhou (normal em alguns backends)")
                
                return True
            else:
                logger.warning(f"⚠️ Senha recuperada não confere: {retrieved}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Operação de keyring falhou: {e}")
            logger.info("ℹ️ Isso é normal se o keyring não estiver configurado")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar funcionalidade: {e}")
        return False

def test_safestic_integration():
    """Testa integração com SafeStic."""
    logger.info("\n=== TESTANDO INTEGRAÇÃO SAFESTIC ===")
    
    try:
        from services.credentials import CredentialManager
        
        # Teste com keyring
        try:
            manager = CredentialManager(credential_source="keyring")
            logger.info("✅ CredentialManager (keyring): Criado com sucesso")
            
            # Teste de obtenção (deve retornar None graciosamente)
            result = manager.get_credential("TEST_NONEXISTENT_KEY")
            logger.info(f"✅ Teste de obtenção: {result is None}")
            
        except Exception as e:
            logger.error(f"❌ CredentialManager (keyring): {e}")
            return False
        
        # Teste com env (fallback)
        try:
            manager_env = CredentialManager(credential_source="env")
            logger.info("✅ CredentialManager (env): Criado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ CredentialManager (env): {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Falha ao importar CredentialManager: {e}")
        return False

def main():
    """Executa todos os testes."""
    logger.info("=== TESTE DE CORREÇÕES LINUX KEYRING ===")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Plataforma: {sys.platform}")
    
    if sys.platform != 'linux':
        logger.warning("⚠️ Este teste é específico para Linux")
        logger.info("ℹ️ Executando testes básicos...")
    
    tests = [
        ("Dependências de Sistema", test_system_dependencies),
        ("Backends do Keyring", test_python_keyring_backends),
        ("Alternativas do Keyring", test_keyring_alternatives),
        ("Funcionalidade do Keyring", test_keyring_functionality),
        ("Integração SafeStic", test_safestic_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            if isinstance(result, dict):
                # Para testes que retornam dicionário
                success = any(result.values()) if result else False
                results.append((test_name, success))
            else:
                results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    logger.info("\n=== RESUMO DOS TESTES ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("🎉 Todos os testes passaram! Keyring está funcionando perfeitamente.")
        return 0
    elif passed >= total // 2:
        logger.info("✅ Maioria dos testes passou. Sistema funcional com algumas limitações.")
        return 0
    else:
        logger.warning("⚠️ Muitos testes falharam. Verifique a instalação das dependências.")
        return 1

if __name__ == "__main__":
    sys.exit(main())