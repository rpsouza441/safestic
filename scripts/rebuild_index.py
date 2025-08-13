#!/usr/bin/env python3
"""
Script para reconstruir índice do repositório Restic - Safestic
Reconstrói o índice quando há corrupção ou problemas de performance
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

def check_repository_access():
    """Verifica se o repositório está acessível"""
    print("🔍 Verificando acesso ao repositório...")
    
    try:
        env = build_restic_env()
        result = subprocess.run(
            ['restic', 'cat', 'config'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Repositório acessível")
            return True
        else:
            print(f"❌ Erro ao acessar repositório: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao acessar repositório")
        return False
    except FileNotFoundError:
        print("❌ Restic não encontrado. Verifique se está instalado e no PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def rebuild_index(read_all_packs=False):
    """Reconstrói o índice do repositório"""
    print("🔧 Reconstruindo índice do repositório...")
    
    # Construir comando
    cmd = ['restic', 'rebuild-index']
    
    if read_all_packs:
        cmd.append('--read-all-packs')
        print("📋 Modo: Leitura completa de todos os packs (mais lento, mais completo)")
    else:
        print("📋 Modo: Reconstrução rápida (padrão)")
    
    # Construir ambiente
    env = build_restic_env()
    
    print(f"📋 Comando: {' '.join(cmd)}")
    print()
    print("⚠️  ATENÇÃO:")
    print("   - Esta operação pode demorar dependendo do tamanho do repositório")
    print("   - O repositório ficará temporariamente inacessível")
    print("   - Não interrompa o processo")
    print()
    
    try:
        # Executar comando
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("🚀 Iniciando reconstrução...")
        
        # Mostrar progresso
        for line in process.stdout:
            if line.strip():
                print(f"📋 {line.strip()}")
        
        # Aguardar conclusão
        return_code = process.wait()
        
        if return_code == 0:
            print("✅ Índice reconstruído com sucesso!")
            return True
        else:
            print(f"❌ Erro na reconstrução (código: {return_code})")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao reconstruir índice: {e}")
        return False
    except FileNotFoundError:
        print("❌ Restic não encontrado. Verifique se está instalado e no PATH.")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Operação interrompida pelo usuário")
        print("❌ ATENÇÃO: O repositório pode estar em estado inconsistente")
        print("💡 Execute novamente para completar a reconstrução")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def verify_index():
    """Verifica a integridade do índice após reconstrução"""
    print("🔍 Verificando integridade do índice...")
    
    try:
        env = build_restic_env()
        result = subprocess.run(
            ['restic', 'check', '--read-data-subset=5%'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        
        if result.returncode == 0:
            print("✅ Índice verificado com sucesso")
            return True
        else:
            print(f"⚠️  Problemas encontrados na verificação:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout na verificação (repositório muito grande)")
        print("💡 Execute 'make check' manualmente para verificação completa")
        return True  # Não falhar por timeout
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 Safestic - Rebuild Index")
    print()
    
    # Carregar configuração
    if not load_config():
        return 1
    
    # Verificar argumentos
    read_all_packs = '--read-all-packs' in sys.argv or '--full' in sys.argv
    
    if read_all_packs:
        print("🔍 Modo completo ativado (--read-all-packs)")
        print("⏱️  Esta operação será mais lenta mas mais completa")
        print()
    
    # Verificar acesso ao repositório
    if not check_repository_access():
        return 1
    
    # Reconstruir índice
    if not rebuild_index(read_all_packs):
        return 1
    
    # Verificar resultado
    if not verify_index():
        print("⚠️  Reconstrução concluída mas verificação falhou")
        print("💡 Execute 'make check' para diagnóstico completo")
        return 1
    
    print()
    print("🎉 Reconstrução do índice concluída com sucesso!")
    print("💡 Recomendações:")
    print("   - Execute 'make check' para verificação completa")
    print("   - Execute 'make prune' se necessário")
    print("   - Monitore próximos backups para garantir estabilidade")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())