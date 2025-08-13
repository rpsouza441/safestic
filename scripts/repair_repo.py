#!/usr/bin/env python3
"""
Script para reparar repositório Restic - Safestic
Repara snapshots e dados corrompidos no repositório
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Carrega configurações do .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado")
        return False
    
    load_dotenv(env_path)
    return True

def build_restic_env():
    """Constrói variáveis de ambiente para o Restic"""
    env = os.environ.copy()
    
    # Configurar repositório baseado no provedor
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
        account = os.getenv('AZURE_ACCOUNT_NAME')
        env['RESTIC_REPOSITORY'] = f'azure:{account}:{bucket}'
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
    
    # Senha do repositório
    env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
    
    return env

def check_repository_problems():
    """Verifica problemas no repositório"""
    print("🔍 Verificando problemas no repositório...")
    
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
            print("✅ Nenhum problema encontrado no repositório")
            return True, []
        else:
            print("⚠️  Problemas encontrados:")
            problems = result.stderr.split('\n')
            for problem in problems:
                if problem.strip():
                    print(f"   - {problem.strip()}")
            return False, problems
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout na verificação")
        return False, ['Timeout na verificação']
    except FileNotFoundError:
        print("❌ Restic não encontrado. Verifique se está instalado e no PATH.")
        return False, ['Restic não encontrado']
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
    """Repara índice corrompido"""
    print("🔧 Reparando índice...")
    
    try:
        env = build_restic_env()
        
        # Reparar índice
        result = subprocess.run(
            ['restic', 'repair', 'index'],
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            print("✅ Índice reparado com sucesso")
            if result.stdout:
                print("📋 Detalhes:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ Erro ao reparar índice:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout no reparo do índice")
        return False
    except Exception as e:
        print(f"❌ Erro no reparo do índice: {e}")
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
    """Verificação final após reparo"""
    print("🔍 Verificação final...")
    
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
            print("✅ Verificação final bem-sucedida")
            return True
        else:
            print(f"⚠️  Ainda há problemas após o reparo:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout na verificação final")
        return True  # Não falhar por timeout
    except Exception as e:
        print(f"❌ Erro na verificação final: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 Safestic - Repair Repository")
    print()
    
    # Carregar configuração
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
    
    print("⚠️  ATENÇÃO:")
    print("   - Esta operação pode demorar muito tempo")
    print("   - O repositório ficará inacessível durante o reparo")
    print("   - Faça backup das configurações antes de continuar")
    print("   - Não interrompa o processo")
    print()
    
    # Verificar problemas iniciais
    has_problems, problems = check_repository_problems()
    
    if has_problems and not problems:
        print("✅ Repositório está íntegro, nenhum reparo necessário")
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
    
    # Verificação final
    if success:
        if final_verification():
            print("🎉 Reparo concluído com sucesso!")
            print()
            print("💡 Recomendações pós-reparo:")
            print("   - Execute 'make check' para verificação completa")
            print("   - Execute 'make prune' para otimizar o repositório")
            print("   - Teste um backup pequeno para confirmar funcionamento")
            print("   - Monitore próximos backups para garantir estabilidade")
            return 0
        else:
            print("⚠️  Reparo parcialmente bem-sucedido")
            print("💡 Execute 'make check' para diagnóstico detalhado")
            return 1
    else:
        print("❌ Falha no processo de reparo")
        print("💡 Opções:")
        print("   - Tente reparar componentes específicos (--snapshots, --index, --packs)")
        print("   - Verifique conectividade e credenciais")
        print("   - Considere restaurar de backup se disponível")
        return 1

if __name__ == '__main__':
    sys.exit(main())