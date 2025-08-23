#!/usr/bin/env python3
"""
Script de diagnóstico para problemas Azure no Linux

Este script ajuda a identificar diferenças de configuração entre Windows e Linux
que podem causar falhas na inicialização do repositório Azure.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

from services.env import get_credential_source
from services.restic_client import ResticClient

# Importar load_restic_env para carregar configurações como no Windows
try:
    from services.restic import load_restic_env
    HAS_RESTIC_SERVICE = True
except ImportError:
    HAS_RESTIC_SERVICE = False

def print_section(title: str):
    """Imprime uma seção com formatação."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def run_command(cmd: str, capture_output: bool = True) -> tuple[int, str, str]:
    """Executa um comando e retorna código de saída, stdout e stderr."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture_output, text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_environment():
    """Verifica o ambiente Linux."""
    print_section("DIAGNÓSTICO DO AMBIENTE LINUX")
    
    # Informações do sistema
    print("Sistema Operacional:")
    code, out, err = run_command("uname -a")
    print(f"  {out.strip()}")
    
    # Versão do Python
    print(f"\nVersão do Python: {sys.version}")
    
    # Verificar se está em container
    if Path("/.dockerenv").exists():
        print("\n⚠️  DETECTADO: Executando em container Docker")
        print("   Isso pode afetar a conectividade de rede")
    
    # Verificar conectividade de rede
    print("\nTestando conectividade de rede:")
    test_hosts = [
        "8.8.8.8",  # Google DNS
        "azure.microsoft.com",  # Azure
        "login.microsoftonline.com"  # Azure Auth
    ]
    
    for host in test_hosts:
        code, out, err = run_command(f"ping -c 1 -W 3 {host}")
        status = "✅ OK" if code == 0 else "❌ FALHA"
        print(f"  {host}: {status}")

def check_restic_installation():
    """Verifica a instalação do Restic."""
    print_section("VERIFICAÇÃO DO RESTIC")
    
    # Verificar se restic está no PATH
    code, out, err = run_command("which restic")
    if code == 0:
        print(f"✅ Restic encontrado em: {out.strip()}")
    else:
        print("❌ Restic não encontrado no PATH")
        return

    client = ResticClient(repository="dummy", env=dict(os.environ), provider="dummy")

    # Versão do Restic
    try:
        version = client.get_version()
        print(f"✅ Versão: {version.strip()}")
    except Exception as err:
        print(f"❌ Erro ao obter versão: {err}")

    # Testar comando básico
    success, result, _ = client.run_raw(["help"], check=False)
    if success:
        print("✅ Comando restic funciona corretamente")
    else:
        stderr = result.stderr if result else ""
        print(f"❌ Erro ao executar restic: {stderr}")

def check_azure_credentials():
    """Verifica as credenciais Azure."""
    print_section("VERIFICAÇÃO DAS CREDENCIAIS AZURE")
    
    # Tentar usar load_restic_env como no Windows, com fallback para load_dotenv
    repository = None
    env_vars = {}
    provider = None
    
    if HAS_RESTIC_SERVICE:
        try:
            credential_source = get_credential_source()
            
            print(f"🔧 Usando load_restic_env com credential_source='{credential_source}' (como no Windows)")
            repository, env_vars, provider = load_restic_env(credential_source)
            print(f"✅ Configurações carregadas via load_restic_env: provider={provider}")
        except Exception as e:
            print(f"⚠️  Falha ao usar load_restic_env: {e}")
            print("🔄 Fallback para carregamento manual...")
            HAS_RESTIC_SERVICE = False
    
    if not HAS_RESTIC_SERVICE or not repository:
        # Fallback para carregamento manual
        get_credential_source()
        env_vars = dict(os.environ)
        repository = os.getenv("RESTIC_REPOSITORY")
        provider = os.getenv("STORAGE_PROVIDER")
        print("🔧 Usando carregamento manual de .env (modo Linux antigo)")
    
    # Verificar variáveis essenciais
    required_vars = {
        "RESTIC_REPOSITORY": repository or env_vars.get("RESTIC_REPOSITORY"),
        "RESTIC_PASSWORD": env_vars.get("RESTIC_PASSWORD"),
        "AZURE_ACCOUNT_NAME": env_vars.get("AZURE_ACCOUNT_NAME"),
        "AZURE_ACCOUNT_KEY": env_vars.get("AZURE_ACCOUNT_KEY"),
        "STORAGE_PROVIDER": provider or env_vars.get("STORAGE_PROVIDER"),
        "STORAGE_BUCKET": env_vars.get("STORAGE_BUCKET"),
        "CREDENTIAL_SOURCE": env_vars.get("CREDENTIAL_SOURCE", get_credential_source())
    }
    
    print("Variáveis de ambiente:")
    for var, value in required_vars.items():
        if value:
            if "PASSWORD" in var or "KEY" in var:
                print(f"  ✅ {var}: {'*' * min(len(value), 20)} ({len(value)} chars)")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NÃO DEFINIDA")
    
    # Verificar se o repositório está sendo construído corretamente
    if required_vars["STORAGE_PROVIDER"] == "azure" and required_vars["STORAGE_BUCKET"]:
        expected_repo = f"azure:{required_vars['STORAGE_BUCKET']}:restic"
        actual_repo = required_vars["RESTIC_REPOSITORY"]
        
        print(f"\nRepositório esperado: {expected_repo}")
        print(f"Repositório atual: {actual_repo}")
        
        if expected_repo == actual_repo:
            print("✅ Formato do repositório correto")
        else:
            print("❌ Formato do repositório incorreto")

def test_azure_connectivity():
    """Testa conectividade específica com Azure."""
    print_section("TESTE DE CONECTIVIDADE AZURE")
    
    # Usar a mesma lógica de carregamento da função anterior
    repository = None
    env_vars = {}
    provider = None
    
    if HAS_RESTIC_SERVICE:
        try:
            credential_source = get_credential_source()
            repository, env_vars, provider = load_restic_env(credential_source)
        except Exception:
            get_credential_source()
            env_vars = dict(os.environ)
            repository = os.getenv("RESTIC_REPOSITORY")
    else:
        get_credential_source()
        env_vars = dict(os.environ)
        repository = os.getenv("RESTIC_REPOSITORY")
    
    account_name = env_vars.get("AZURE_ACCOUNT_NAME")
    account_key = env_vars.get("AZURE_ACCOUNT_KEY")
    storage_bucket = env_vars.get("STORAGE_BUCKET")
    
    if not all([account_name, account_key, storage_bucket]):
        print("❌ Credenciais Azure incompletas")
        return
    
    # Testar com restic diretamente
    print("Testando acesso direto com restic...")
    
    # Configurar ambiente para o teste
    env = os.environ.copy()
    env["AZURE_ACCOUNT_NAME"] = account_name
    env["AZURE_ACCOUNT_KEY"] = account_key
    env["RESTIC_PASSWORD"] = env_vars.get("RESTIC_PASSWORD", "test")
    
    # Usar o repositório construído pelo load_restic_env se disponível
    repo = repository if repository else f"azure:{storage_bucket}:restic"
    print(f"📍 Repositório a ser testado: {repo}")
    if repository:
        print("✅ Repositório construído via load_restic_env (como Windows)")
    else:
        print("⚠️  Repositório construído manualmente (modo Linux antigo)")
    
    # Teste 1: Listar snapshots (deve falhar se repo não existe)
    print(f"\nTeste 1: Tentando listar snapshots em {repo}")
    cmd = f"restic -r {repo} snapshots"
    
    try:
        result = subprocess.run(
            cmd, shell=True, env=env, capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Repositório existe e é acessível")
            print(f"Snapshots encontrados:\n{result.stdout}")
        else:
            print(f"❌ Erro ao acessar repositório: {result.stderr}")
            
            # Teste 2: Tentar inicializar
            print(f"\nTeste 2: Tentando inicializar repositório")
            init_cmd = f"restic -r {repo} init"
            
            init_result = subprocess.run(
                init_cmd, shell=True, env=env, capture_output=True, text=True, timeout=30
            )
            
            if init_result.returncode == 0:
                print("✅ Repositório inicializado com sucesso")
            else:
                print(f"❌ Erro na inicialização: {init_result.stderr}")
                
                # Análise detalhada do erro
                analyze_error(init_result.stderr)
                
    except subprocess.TimeoutExpired:
        print("❌ Timeout na operação (>30s)")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def analyze_error(error_output: str):
    """Analisa a saída de erro e sugere soluções."""
    print("\n🔍 ANÁLISE DO ERRO:")
    
    error_lower = error_output.lower()
    
    if "connection refused" in error_lower:
        print("  • Problema de conectividade de rede")
        print("  • Verifique firewall e proxy")
    
    elif "authentication" in error_lower or "unauthorized" in error_lower:
        print("  • Problema de autenticação")
        print("  • Verifique AZURE_ACCOUNT_NAME e AZURE_ACCOUNT_KEY")
    
    elif "not found" in error_lower or "does not exist" in error_lower:
        print("  • Container não existe")
        print("  • Verifique STORAGE_BUCKET no portal Azure")
    
    elif "timeout" in error_lower:
        print("  • Timeout de rede")
        print("  • Problema de conectividade ou proxy")
    
    elif "permission" in error_lower or "forbidden" in error_lower:
        print("  • Problema de permissões")
        print("  • Verifique se a chave tem acesso ao container")
    
    else:
        print("  • Erro não reconhecido")
        print(f"  • Erro completo: {error_output}")

def check_python_dependencies():
    """Verifica dependências Python."""
    print_section("VERIFICAÇÃO DAS DEPENDÊNCIAS PYTHON")
    
    # Verificar python-dotenv
    try:
        from dotenv import load_dotenv
        print("[OK] python-dotenv: OK")
    except ImportError:
        print("[X] python-dotenv: NÃO INSTALADO")
    
    # Verificar keyring
    try:
        import keyring
        print("[OK] keyring: OK")
    except ImportError:
        print("[X] keyring: NÃO INSTALADO")
    
    # Verificar pythonjsonlogger
    try:
        import pythonjsonlogger
        print("[OK] pythonjsonlogger: OK")
    except ImportError:
        print("[X] pythonjsonlogger: NÃO INSTALADO")

def main():
    """Função principal."""
    print("🔍 DIAGNÓSTICO AZURE LINUX - SafeStic")
    print("Este script ajuda a identificar problemas específicos do Linux")
    
    check_environment()
    check_python_dependencies()
    check_restic_installation()
    check_azure_credentials()
    test_azure_connectivity()
    
    print_section("RESUMO E PRÓXIMOS PASSOS")
    print("1. Verifique se todas as verificações passaram")
    print("2. Se houver erros de rede, verifique firewall/proxy")
    print("3. Se houver erros de credenciais, reconfigure com 'make setup-credentials'")
    print("4. Se o container não existir, crie-o no portal Azure")
    print("5. Compare com a configuração do Windows que funciona")
    
if __name__ == "__main__":
    main()