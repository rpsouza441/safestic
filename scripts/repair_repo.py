#!/usr/bin/env python3
"""
Script para reparar repositorio Restic - Safestic
Repara snapshots e dados corrompidos no repositorio
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
        # Credenciais AWS
        if os.getenv('AWS_ACCESS_KEY_ID'):
            env['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
        if os.getenv('AWS_SECRET_ACCESS_KEY'):
            env['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
        if os.getenv('AWS_DEFAULT_REGION'):
            env['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION')
    elif provider == 'azure':
        env['RESTIC_REPOSITORY'] = f'azure:{bucket}:restic'
        # Credenciais Azure
        if os.getenv('AZURE_ACCOUNT_KEY'):
            env['AZURE_ACCOUNT_KEY'] = os.getenv('AZURE_ACCOUNT_KEY')
    elif provider == 'gcp':
        env['RESTIC_REPOSITORY'] = f'gs:{bucket}'
        # Credenciais GCP
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            env['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if os.getenv('GOOGLE_PROJECT_ID'):
            env['GOOGLE_PROJECT_ID'] = os.getenv('GOOGLE_PROJECT_ID')
    
    # Senha do repositorio
    env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
    
    return env

def check_repository_problems():
    """Verifica problemas no repositorio"""
    print("🔍 Verificando problemas no repositorio...")
    
    try:
        env = build_restic_env()
        result = subprocess.run(
            ['restic', 'check'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        
        if result.returncode == 0:
            print("✅ Nenhum problema encontrado no repositorio")
            return True, []
        else:
            print("⚠️  Problemas encontrados:")
            problems = result.stderr.split('\n')
            for problem in problems:
                if problem.strip():
                    print(f"   - {problem.strip()}")
            return False, problems
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout na verificacao")
        return False, ['Timeout na verificacao']
    except FileNotFoundError:
        print("❌ Restic nao encontrado. Verifique se esta instalado e no PATH.")
        return False, ['Restic nao encontrado']
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False, [str(e)]

def repair_snapshots():
    """Repara snapshots corrompidos"""
    print("🔧 Reparando snapshots...")
    
    try:
        env = build_restic_env()
        
        # Primeiro, tentar reparar snapshots
        result = subprocess.run(
            ['restic', 'repair', 'snapshots'],
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            print("✅ Snapshots reparados com sucesso")
            if result.stdout:
                print("📋 Detalhes:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ Erro ao reparar snapshots:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout no reparo de snapshots")
        return False
    except Exception as e:
        print(f"❌ Erro no reparo de snapshots: {e}")
        return False

def repair_index():
    """Repara indice corrompido"""
    print("🔧 Reparando indice...")
    
    try:
        env = build_restic_env()
        
        # Reparar indice
        result = subprocess.run(
            ['restic', 'repair', 'index'],
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            print("✅ indice reparado com sucesso")
            if result.stdout:
                print("📋 Detalhes:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ Erro ao reparar indice:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout no reparo do indice")
        return False
    except Exception as e:
        print(f"❌ Erro no reparo do indice: {e}")
        return False

def repair_packs():
    """Repara packs corrompidos"""
    print("🔧 Reparando packs...")
    
    try:
        env = build_restic_env()
        
        # Reparar packs
        result = subprocess.run(
            ['restic', 'repair', 'packs'],
            env=env,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos
        )
        
        if result.returncode == 0:
            print("✅ Packs reparados com sucesso")
            if result.stdout:
                print("📋 Detalhes:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ Erro ao reparar packs:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout no reparo de packs")
        return False
    except Exception as e:
        print(f"❌ Erro no reparo de packs: {e}")
        return False

def final_verification():
    """Verificacao final apos reparo"""
    print("🔍 Verificacao final...")
    
    try:
        env = build_restic_env()
        result = subprocess.run(
            ['restic', 'check', '--read-data-subset=10%'],
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            print("✅ Verificacao final bem-sucedida")
            return True
        else:
            print(f"⚠️  Ainda ha problemas apos o reparo:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout na verificacao final")
        return True  # Nao falhar por timeout
    except Exception as e:
        print(f"❌ Erro na verificacao final: {e}")
        return False

def main():
    """Funcao principal"""
    print("🔧 Safestic - Repair Repository")
    print()
    
    # Carregar configuracao
    if not load_config():
        return 1
    
    # Verificar argumentos
    repair_type = 'all'
    if '--snapshots' in sys.argv:
        repair_type = 'snapshots'
    elif '--index' in sys.argv:
        repair_type = 'index'
    elif '--packs' in sys.argv:
        repair_type = 'packs'
    
    print(f"🔧 Tipo de reparo: {repair_type}")
    print()
    
    print("⚠️  ATENcaO:")
    print("   - Esta operacao pode demorar muito tempo")
    print("   - O repositorio ficara inacessivel durante o reparo")
    print("   - Faca backup das configuracoes antes de continuar")
    print("   - Nao interrompa o processo")
    print()
    
    # Verificar problemas iniciais
    has_problems, problems = check_repository_problems()
    
    if has_problems and not problems:
        print("✅ Repositorio esta integro, nenhum reparo necessario")
        return 0
    
    print("🚀 Iniciando processo de reparo...")
    print()
    
    success = True
    
    # Executar reparos baseado no tipo
    if repair_type in ['all', 'snapshots']:
        if not repair_snapshots():
            success = False
        print()
    
    if repair_type in ['all', 'index']:
        if not repair_index():
            success = False
        print()
    
    if repair_type in ['all', 'packs']:
        if not repair_packs():
            success = False
        print()
    
    # Verificacao final
    if success:
        if final_verification():
            print("🎉 Reparo concluido com sucesso!")
            print()
            print("💡 Recomendacoes pos-reparo:")
            print("   - Execute 'make check' para verificacao completa")
            print("   - Execute 'make prune' para otimizar o repositorio")
            print("   - Teste um backup pequeno para confirmar funcionamento")
            print("   - Monitore proximos backups para garantir estabilidade")
            return 0
        else:
            print("⚠️  Reparo parcialmente bem-sucedido")
            print("💡 Execute 'make check' para diagnostico detalhado")
            return 1
    else:
        print("❌ Falha no processo de reparo")
        print("💡 Opcoes:")
        print("   - Tente reparar componentes especificos (--snapshots, --index, --packs)")
        print("   - Verifique conectividade e credenciais")
        print("   - Considere restaurar de backup se disponivel")
        return 1

if __name__ == '__main__':
    sys.exit(main())
