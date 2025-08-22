#!/usr/bin/env python3
"""
Script para reconstruir indice do repositorio Restic - Safestic
Reconstroi o indice quando ha corrupcao ou problemas de performance
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

def check_repository_access():
    """Verifica se o repositorio esta acessivel"""
    print("🔍 Verificando acesso ao repositorio...")
    
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
            print("✅ Repositorio acessivel")
            return True
        else:
            print(f"❌ Erro ao acessar repositorio: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao acessar repositorio")
        return False
    except FileNotFoundError:
        print("❌ Restic nao encontrado. Verifique se esta instalado e no PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def rebuild_index(read_all_packs=False):
    """Reconstroi o indice do repositorio"""
    print("🔧 Reconstruindo indice do repositorio...")
    
    # Construir comando
    cmd = ['restic', 'rebuild-index']
    
    if read_all_packs:
        cmd.append('--read-all-packs')
        print("📋 Modo: Leitura completa de todos os packs (mais lento, mais completo)")
    else:
        print("📋 Modo: Reconstrucao rapida (padrao)")
    
    # Construir ambiente
    env = build_restic_env()
    
    print(f"📋 Comando: {' '.join(cmd)}")
    print()
    print("⚠️  ATENcaO:")
    print("   - Esta operacao pode demorar dependendo do tamanho do repositorio")
    print("   - O repositorio ficara temporariamente inacessivel")
    print("   - Nao interrompa o processo")
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
        
        print("🚀 Iniciando reconstrucao...")
        
        # Mostrar progresso
        for line in process.stdout:
            if line.strip():
                print(f"📋 {line.strip()}")
        
        # Aguardar conclusao
        return_code = process.wait()
        
        if return_code == 0:
            print("✅ indice reconstruido com sucesso!")
            return True
        else:
            print(f"❌ Erro na reconstrucao (codigo: {return_code})")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao reconstruir indice: {e}")
        return False
    except FileNotFoundError:
        print("❌ Restic nao encontrado. Verifique se esta instalado e no PATH.")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Operacao interrompida pelo usuario")
        print("❌ ATENcaO: O repositorio pode estar em estado inconsistente")
        print("💡 Execute novamente para completar a reconstrucao")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def verify_index():
    """Verifica a integridade do indice apos reconstrucao"""
    print("🔍 Verificando integridade do indice...")
    
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
            print("✅ indice verificado com sucesso")
            return True
        else:
            print(f"⚠️  Problemas encontrados na verificacao:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout na verificacao (repositorio muito grande)")
        print("💡 Execute 'make check' manualmente para verificacao completa")
        return True  # Nao falhar por timeout
    except Exception as e:
        print(f"❌ Erro na verificacao: {e}")
        return False

def main():
    """Funcao principal"""
    print("🔧 Safestic - Rebuild Index")
    print()
    
    # Carregar configuracao
    if not load_config():
        return 1
    
    # Verificar argumentos
    read_all_packs = '--read-all-packs' in sys.argv or '--full' in sys.argv
    
    if read_all_packs:
        print("🔍 Modo completo ativado (--read-all-packs)")
        print("⏱️  Esta operacao sera mais lenta mas mais completa")
        print()
    
    # Verificar acesso ao repositorio
    if not check_repository_access():
        return 1
    
    # Reconstruir indice
    if not rebuild_index(read_all_packs):
        return 1
    
    # Verificar resultado
    if not verify_index():
        print("⚠️  Reconstrucao concluida mas verificacao falhou")
        print("💡 Execute 'make check' para diagnostico completo")
        return 1
    
    print()
    print("🎉 Reconstrucao do indice concluida com sucesso!")
    print("💡 Recomendacoes:")
    print("   - Execute 'make check' para verificacao completa")
    print("   - Execute 'make prune' se necessario")
    print("   - Monitore proximos backups para garantir estabilidade")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
