#!/usr/bin/env python3
"""
Script para montar repositorio Restic como sistema de arquivos - Safestic
Permite navegar pelos snapshots como diretorios normais
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Carrega configuracoes do .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("Arquivo .env nao encontrado")
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
        account = os.getenv('AZURE_ACCOUNT_NAME')
        env['RESTIC_REPOSITORY'] = f'azure:{account}:{bucket}'
    elif provider == 'gcp':
        env['RESTIC_REPOSITORY'] = f'gs:{bucket}'
    
    # Senha do repositorio
    env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
    
    return env

def check_fuse_support():
    """Verifica se FUSE esta disponivel"""
    system = os.name
    
    if system == 'posix':  # Linux/macOS
        # Verificar se FUSE esta instalado
        try:
            subprocess.run(['fusermount', '--version'], 
                         capture_output=True, check=True)
            return True, './mount'
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("FUSE nao encontrado.")
            print("Instale FUSE:")
            print("   Ubuntu/Debian: sudo apt install fuse")
            print("   Fedora: sudo dnf install fuse")
            print("   macOS: brew install macfuse")
            return False, None
    
    elif system == 'nt':  # Windows
        # Verificar se WinFsp esta instalado
        winfsp_paths = [
            r'C:\Program Files\WinFsp\bin\launchctl-x64.exe',
            r'C:\Program Files (x86)\WinFsp\bin\launchctl-x86.exe'
        ]
        
        for path in winfsp_paths:
            if Path(path).exists():
                return True, '.\\mount'
        
        print("WinFsp nao encontrado.")
        print("Instale WinFsp de: https://winfsp.dev/rel/")
        return False, None
    
    else:
        print(f"Sistema nao suportado: {system}")
        return False, None

def create_mount_point(mount_path):
    """Cria ponto de montagem se nao existir"""
    try:
        Path(mount_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Erro ao criar ponto de montagem: {e}")
        return False

def mount_repository(mount_path):
    """Monta o repositorio"""
    print(f"Montando repositorio em: {mount_path}")
    
    # Construir comando
    cmd = ['restic', 'mount', mount_path]
    
    # Construir ambiente
    env = build_restic_env()
    
    print(f"Comando: {' '.join(cmd)}")
    print()
    print("ATENCAO:")
    print("   - O repositorio sera montado em modo somente leitura")
    print("   - Use Ctrl+C para desmontar")
    print("   - Nao feche este terminal enquanto estiver montado")
    print()
    print("Iniciando montagem...")
    
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
        
        # Configurar handler para Ctrl+C
        def signal_handler(sig, frame):
            print("\nDesmontando repositorio...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        print("Repositorio montado com sucesso!")
        print(f"Acesse os snapshots em: {Path(mount_path).absolute()}")
        print("Cada snapshot aparecera como um diretorio")
        print()
        print("Pressione Ctrl+C para desmontar")
        
        # Aguardar processo
        for line in process.stdout:
            if line.strip():
                print(f"Log: {line.strip()}")
        
        process.wait()
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao montar repositorio: {e}")
        return False
    except FileNotFoundError:
        print("Restic nao encontrado. Verifique se esta instalado e no PATH.")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False
    
    return True

def main():
    """Funcao principal"""
    print("Safestic - Mount Repository")
    print()
    
    # Carregar configuracao
    if not load_config():
        return 1
    
    # Verificar suporte FUSE
    fuse_ok, default_mount = check_fuse_support()
    if not fuse_ok:
        return 1
    
    # Definir ponto de montagem
    mount_path = os.getenv('MOUNT_POINT', default_mount)
    
    # Criar ponto de montagem
    if not create_mount_point(mount_path):
        return 1
    
    # Montar repositorio
    if mount_repository(mount_path):
        print("Operacao concluida!")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
