#!/usr/bin/env python3
"""
Script de validação de configuração - Safestic
Verifica se todas as configurações necessárias estão presentes e válidas
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_env_file():
    """Carrega arquivo .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado")
        print("💡 Execute: cp .env.example .env")
        return False
    
    load_dotenv(env_path)
    print("✅ Arquivo .env carregado")
    return True

def validate_required_vars():
    """Valida variáveis obrigatórias"""
    required_vars = [
        'STORAGE_PROVIDER',
        'STORAGE_BUCKET', 
        'RESTIC_PASSWORD',
        'BACKUP_SOURCE_DIRS'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variáveis obrigatórias não configuradas:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Todas as variáveis obrigatórias estão configuradas")
    return True

def validate_storage_config():
    """Valida configuração de armazenamento"""
    provider = os.getenv('STORAGE_PROVIDER', '').lower()
    bucket = os.getenv('STORAGE_BUCKET', '')
    
    if provider == 'local':
        # Verificar se o diretório existe ou pode ser criado
        try:
            Path(bucket).mkdir(parents=True, exist_ok=True)
            print(f"✅ Diretório de backup local: {bucket}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar diretório de backup: {e}")
            return False
    
    elif provider == 'aws':
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        missing = [var for var in aws_vars if not os.getenv(var)]
        if missing:
            print(f"❌ Variáveis AWS faltando: {missing}")
            return False
        print("✅ Configuração AWS válida")
        return True
    
    elif provider == 'azure':
        azure_vars = ['AZURE_ACCOUNT_NAME', 'AZURE_ACCOUNT_KEY']
        missing = [var for var in azure_vars if not os.getenv(var)]
        if missing:
            print(f"❌ Variáveis Azure faltando: {missing}")
            return False
        print("✅ Configuração Azure válida")
        return True
    
    elif provider == 'gcp':
        gcp_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not gcp_creds or not Path(gcp_creds).exists():
            print("❌ Credenciais GCP não encontradas")
            return False
        print("✅ Configuração GCP válida")
        return True
    
    else:
        print(f"❌ Provedor de armazenamento inválido: {provider}")
        print("💡 Valores válidos: local, aws, azure, gcp")
        return False

def validate_backup_dirs():
    """Valida diretórios de backup"""
    dirs_str = os.getenv('BACKUP_SOURCE_DIRS', '')
    if not dirs_str:
        print("❌ BACKUP_SOURCE_DIRS não configurado")
        return False
    
    dirs = [d.strip() for d in dirs_str.split(',')]
    missing_dirs = []
    
    for dir_path in dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("⚠️  Diretórios de backup não encontrados:")
        for dir_path in missing_dirs:
            print(f"   - {dir_path}")
        print("💡 Verifique se os caminhos estão corretos")
        return False
    
    print(f"✅ Diretórios de backup válidos: {len(dirs)} diretórios")
    return True

def validate_log_config():
    """Valida configuração de logs"""
    log_dir = os.getenv('LOG_DIR', './logs')
    
    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório de logs: {log_dir}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar diretório de logs: {e}")
        return False

def validate_retention_config():
    """Valida configuração de retenção"""
    if os.getenv('RETENTION_ENABLED', 'true').lower() != 'true':
        print("⚠️  Retenção desabilitada")
        return True
    
    retention_vars = {
        'KEEP_HOURLY': 24,
        'KEEP_DAILY': 7, 
        'KEEP_WEEKLY': 4,
        'KEEP_MONTHLY': 12
    }
    
    for var, default in retention_vars.items():
        value = os.getenv(var, str(default))
        try:
            int_value = int(value)
            if int_value < 0:
                print(f"❌ {var} deve ser >= 0, encontrado: {value}")
                return False
        except ValueError:
            print(f"❌ {var} deve ser um número, encontrado: {value}")
            return False
    
    print("✅ Configuração de retenção válida")
    return True

def main():
    """Função principal"""
    print("🔍 Validando configuração do Safestic...")
    print()
    
    all_valid = True
    
    # Carregar .env
    if not load_env_file():
        return 1
    
    # Validações
    validations = [
        validate_required_vars,
        validate_storage_config,
        validate_backup_dirs,
        validate_log_config,
        validate_retention_config
    ]
    
    for validation in validations:
        if not validation():
            all_valid = False
        print()
    
    if all_valid:
        print("🎉 Configuração válida! Pronto para usar o Safestic.")
        return 0
    else:
        print("❌ Configuração inválida. Corrija os erros acima.")
        return 1

if __name__ == '__main__':
    sys.exit(main())