#!/usr/bin/env python3
"""
Script para esquecer snapshots baseado na politica de retencao - Safestic
Implementa o comando 'restic forget' com as configuracoes do .env
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Carrega configuracoes do .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Arquivo .env nao encontrado")
        return False
    
    load_dotenv(env_path)
    return True

def build_restic_env():
    """Constroi variaveis de ambiente para o Restic"""
    env = os.environ.copy()
    
    # Configurar repositorio baseado no provedor
    provider = os.getenv('STORAGE_PROVIDER', '').lower()
    bucket = os.getenv('STORAGE_BUCKET', '')
    
    if provider == 'local':
        env['RESTIC_REPOSITORY'] = bucket
    elif provider == 'aws':
        env['RESTIC_REPOSITORY'] = f's3:{bucket}'
    elif provider == 'azure':
        env['RESTIC_REPOSITORY'] = f'azure:{bucket}:restic'
    elif provider == 'gcp':
        env['RESTIC_REPOSITORY'] = f'gs:{bucket}'
    
    # Senha do repositorio
    env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
    
    return env

def build_forget_command():
    """Constroi comando restic forget com politica de retencao"""
    cmd = ['restic', 'forget']
    
    # Verificar se retencao esta habilitada
    if os.getenv('RETENTION_ENABLED', 'true').lower() != 'true':
        print("⚠️  Retencao desabilitada. Nenhum snapshot sera esquecido.")
        return None
    
    # Adicionar politicas de retencao
    retention_policies = {
        '--keep-hourly': os.getenv('KEEP_HOURLY', '24'),
        '--keep-daily': os.getenv('KEEP_DAILY', '7'),
        '--keep-weekly': os.getenv('KEEP_WEEKLY', '4'),
        '--keep-monthly': os.getenv('KEEP_MONTHLY', '12')
    }
    
    for flag, value in retention_policies.items():
        if value and int(value) > 0:
            cmd.extend([flag, value])
    
    # Adicionar tags se configuradas
    tags = os.getenv('RESTIC_TAGS', '')
    if tags:
        for tag in tags.split(','):
            tag = tag.strip()
            if tag:
                cmd.extend(['--tag', tag])
    
    # Adicionar flags adicionais
    cmd.append('--prune')  # Remove dados nao referenciados
    cmd.append('--verbose')
    
    return cmd

def run_forget():
    """Executa o comando forget"""
    print("🗑️  Esquecendo snapshots baseado na politica de retencao...")
    
    # Construir comando
    cmd = build_forget_command()
    if not cmd:
        return True
    
    # Construir ambiente
    env = build_restic_env()
    
    print(f"📋 Comando: {' '.join(cmd)}")
    print()
    
    try:
        # Executar comando
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=False,
            text=True,
            check=True
        )
        
        print()
        print("✅ Snapshots esquecidos com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao esquecer snapshots: {e}")
        return False
    except FileNotFoundError:
        print("❌ Restic nao encontrado. Verifique se esta instalado e no PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def show_retention_policy():
    """Mostra a politica de retencao atual"""
    print("📋 Politica de Retencao Atual:")
    
    if os.getenv('RETENTION_ENABLED', 'true').lower() != 'true':
        print("   ⚠️  Retencao DESABILITADA")
        return
    
    policies = {
        'Manter por horas': os.getenv('KEEP_HOURLY', '24'),
        'Manter por dias': os.getenv('KEEP_DAILY', '7'),
        'Manter por semanas': os.getenv('KEEP_WEEKLY', '4'),
        'Manter por meses': os.getenv('KEEP_MONTHLY', '12')
    }
    
    for description, value in policies.items():
        if value and int(value) > 0:
            print(f"   📅 {description}: {value}")
    
    tags = os.getenv('RESTIC_TAGS', '')
    if tags:
        print(f"   🏷️  Tags: {tags}")
    
    print()

def main():
    """Funcao principal"""
    print("🗑️  Safestic - Forget Snapshots")
    print()
    
    # Carregar configuracao
    if not load_config():
        return 1
    
    # Mostrar politica atual
    show_retention_policy()
    
    # Executar forget
    if run_forget():
        print("🎉 Operacao concluida com sucesso!")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
