#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de credenciais no Safestic
Uso: python diagnose_credentials.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_status(item, status, details=""):
    """Imprime status formatado"""
    icon = "✓" if status else "✗"
    print(f"{icon} {item}: {'OK' if status else 'ERRO'}")
    if details:
        print(f"   {details}")

def check_file_exists(filepath):
    """Verifica se arquivo existe"""
    path = Path(filepath)
    return path.exists(), str(path.absolute())

def check_env_file():
    """Verifica arquivo .env"""
    print_header("VERIFICAÇÃO DO ARQUIVO .env")
    
    env_exists, env_path = check_file_exists(".env")
    print_status(".env existe", env_exists, env_path)
    
    if not env_exists:
        example_exists, example_path = check_file_exists(".env.example")
        print_status(".env.example existe", example_exists, example_path)
        if example_exists:
            print("\n💡 SOLUÇÃO: Copie o arquivo exemplo:")
            print("   cp .env.example .env")
        return False
    
    # Verificar permissões
    try:
        stat = os.stat(".env")
        permissions = oct(stat.st_mode)[-3:]
        secure = permissions in ['600', '640']
        print_status("Permissões seguras", secure, f"Atual: {permissions}, Recomendado: 600")
        if not secure:
            print("\n💡 SOLUÇÃO: Ajustar permissões:")
            print("   chmod 600 .env")
    except Exception as e:
        print_status("Verificação de permissões", False, str(e))
    
    return True

def check_environment_variables():
    """Verifica variáveis de ambiente"""
    print_header("VARIÁVEIS DE AMBIENTE")
    
    # Carregar .env
    try:
        load_dotenv()
        print_status("Carregamento do .env", True)
    except Exception as e:
        print_status("Carregamento do .env", False, str(e))
        return False
    
    # Verificar CREDENTIAL_SOURCE
    credential_source = os.getenv('CREDENTIAL_SOURCE')
    has_credential_source = credential_source is not None
    print_status("CREDENTIAL_SOURCE definido", has_credential_source, 
                f"Valor: {credential_source or 'Não definido'}")
    
    # Verificar RESTIC_REPOSITORY
    restic_repo = os.getenv('RESTIC_REPOSITORY')
    has_repo = restic_repo is not None
    print_status("RESTIC_REPOSITORY definido", has_repo,
                f"Valor: {restic_repo or 'Não definido'}")
    
    # Verificar BACKUP_SOURCE_DIRS
    backup_dirs = os.getenv('BACKUP_SOURCE_DIRS')
    has_backup_dirs = backup_dirs is not None
    print_status("BACKUP_SOURCE_DIRS definido", has_backup_dirs,
                f"Valor: {backup_dirs or 'Não definido'}")
    
    return has_credential_source and has_repo and has_backup_dirs

def check_credential_source():
    """Verifica configuração da fonte de credenciais"""
    print_header("FONTE DE CREDENCIAIS")
    
    credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
    valid_sources = ['env', 'keyring', 'aws_secrets', 'azure_keyvault', 'gcp_secrets', 'sops']
    is_valid = credential_source in valid_sources
    
    print_status("CREDENTIAL_SOURCE válido", is_valid,
                f"Atual: {credential_source}, Válidos: {', '.join(valid_sources)}")
    
    return is_valid, credential_source

def check_restic_password(credential_source):
    """Verifica RESTIC_PASSWORD"""
    print_header("RESTIC_PASSWORD")
    
    try:
        from services.credentials import get_credential
        
        password = get_credential('RESTIC_PASSWORD', credential_source)
        has_password = password is not None and len(password) > 0
        
        print_status(f"RESTIC_PASSWORD em {credential_source}", has_password,
                    "Senha encontrada" if has_password else "Senha não encontrada")
        
        if not has_password:
            print("\n💡 SOLUÇÕES:")
            if credential_source == 'env':
                print("   1. Adicionar no .env: RESTIC_PASSWORD=sua_senha")
                print("   2. Ou executar: make setup-credentials-env")
            elif credential_source == 'keyring':
                print("   1. Executar: make setup-restic-password")
                print("   2. Ou executar: make setup-credentials-keyring")
            else:
                print(f"   1. Configurar credenciais no {credential_source}")
                print("   2. Ou alterar CREDENTIAL_SOURCE=env no .env")
        
        return has_password
        
    except ImportError as e:
        print_status("Importação do módulo credentials", False, str(e))
        return False
    except Exception as e:
        print_status("Verificação da senha", False, str(e))
        return False

def check_backup_directories():
    """Verifica diretórios de backup"""
    print_header("DIRETÓRIOS DE BACKUP")
    
    backup_dirs = os.getenv('BACKUP_SOURCE_DIRS', '')
    if not backup_dirs:
        print_status("BACKUP_SOURCE_DIRS configurado", False, "Variável não definida")
        return False
    
    dirs = [d.strip() for d in backup_dirs.split(',') if d.strip()]
    all_exist = True
    
    for directory in dirs:
        exists = Path(directory).exists()
        print_status(f"Diretório {directory}", exists)
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n💡 SOLUÇÕES:")
        print("   1. Criar os diretórios faltantes")
        print("   2. Ou ajustar BACKUP_SOURCE_DIRS no .env com diretórios existentes")
        print("   Exemplo: BACKUP_SOURCE_DIRS=/home/user/Documents,/home/user/Pictures")
    
    return all_exist

def check_restic_config():
    """Verifica carregamento da configuração do Restic"""
    print_header("CONFIGURAÇÃO DO RESTIC")
    
    try:
        from services.restic import load_restic_config
        
        credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
        config = load_restic_config(credential_source)
        
        print_status("Carregamento da configuração", True)
        print(f"   Repositório: {config.restic_repository}")
        print(f"   Diretórios: {len(config.backup_source_dirs)} configurados")
        print(f"   Fonte de credenciais: {config.credential_source}")
        
        return True
        
    except Exception as e:
        print_status("Carregamento da configuração", False, str(e))
        
        # Sugestões baseadas no tipo de erro
        error_str = str(e).lower()
        print("\n💡 SOLUÇÕES:")
        if "string_type" in error_str and "restic_password" in error_str:
            print("   1. Configurar RESTIC_PASSWORD (ver seção anterior)")
        if "validation error" in error_str:
            print("   2. Verificar todas as variáveis obrigatórias no .env")
        print("   3. Executar: make setup-credentials")
        print("   4. Verificar arquivo .env.example para referência")
        
        return False

def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO DE CREDENCIAIS DO SAFESTIC")
    print("Este script verifica a configuração de credenciais e identifica problemas.")
    
    # Lista de verificações
    checks = [
        ("Arquivo .env", check_env_file),
        ("Variáveis de ambiente", check_environment_variables),
        ("Fonte de credenciais", lambda: check_credential_source()[0]),
        ("RESTIC_PASSWORD", lambda: check_restic_password(check_credential_source()[1])),
        ("Diretórios de backup", check_backup_directories),
        ("Configuração do Restic", check_restic_config)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Erro na verificação: {name}", False, str(e))
            results.append((name, False))
    
    # Resumo final
    print_header("RESUMO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        print_status(name, result)
    
    print(f"\n📊 RESULTADO: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("\n🎉 Todas as verificações passaram! Sua configuração está correta.")
        print("\n✅ Próximos passos:")
        print("   make init    # Inicializar repositório")
        print("   make check   # Verificar acesso ao repositório")
        print("   make dry-run # Testar configuração de backup")
    else:
        print(f"\n⚠️  {total - passed} problema(s) encontrado(s). Siga as soluções sugeridas acima.")
        print("\n📚 Documentação adicional:")
        print("   - LINUX_CREDENTIAL_TROUBLESHOOTING.md")
        print("   - CREDENTIAL_SETUP_GUIDE.md")
        print("   - README.md")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)