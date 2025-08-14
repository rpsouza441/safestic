#!/usr/bin/env python3
"""
Script para desmontar repositorio Restic - Safestic
Desmonta sistema de arquivos montado pelo mount_repo.py
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
        print("Arquivo .env nao encontrado")
        return False
    
    load_dotenv(env_path)
    return True

def unmount_linux(mount_path):
    """Desmonta no Linux usando fusermount"""
    try:
        cmd = ['fusermount', '-u', mount_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao desmontar (fusermount): {e.stderr}")
        return False
    except FileNotFoundError:
        # Tentar com umount
        try:
            cmd = ['umount', mount_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erro ao desmontar (umount): {e.stderr}")
            return False
        except FileNotFoundError:
            print("Nem fusermount nem umount encontrados")
            return False

def unmount_windows(mount_path):
    """Desmonta no Windows"""
    # No Windows, o processo restic mount geralmente e interrompido com Ctrl+C
    # Mas podemos tentar forcar a desmontagem
    try:
        # Tentar usar net use para desconectar
        cmd = ['net', 'use', mount_path, '/delete', '/y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verificar se ainda esta montado
        if Path(mount_path).exists() and any(Path(mount_path).iterdir()):
            print("Ponto de montagem ainda parece ativo")
            print("Tente interromper o processo 'restic mount' manualmente")
            return False
        
        return True
        
    except Exception as e:
        print(f"Erro ao desmontar no Windows: {e}")
        return False

def check_mount_status(mount_path):
    """Verifica se o ponto esta montado"""
    if not Path(mount_path).exists():
        print(f"Ponto de montagem nao existe: {mount_path}")
        return False
    
    # Verificar se ha conteudo (indicativo de montagem)
    try:
        contents = list(Path(mount_path).iterdir())
        if contents:
            print(f"Ponto de montagem ativo: {len(contents)} itens encontrados")
            return True
        else:
            print(f"Ponto de montagem vazio: {mount_path}")
            return False
    except PermissionError:
        print(f"Sem permissao para acessar: {mount_path}")
        return True  # Provavelmente montado
    except Exception as e:
        print(f"Erro ao verificar montagem: {e}")
        return False

def force_cleanup(mount_path):
    """Forca limpeza do ponto de montagem"""
    print("Tentando limpeza forcada...")
    
    system = os.name
    
    if system == 'posix':  # Linux/macOS
        # Tentar matar processos relacionados
        try:
            subprocess.run(['pkill', '-f', f'restic.*mount.*{mount_path}'], 
                         capture_output=True)
            print("Processos restic mount finalizados")
        except:
            pass
        
        # Tentar desmontagem forcada
        try:
            subprocess.run(['fusermount', '-uz', mount_path], 
                         capture_output=True)
            print("Desmontagem forcada executada")
        except:
            pass
    
    elif system == 'nt':  # Windows
        # Tentar finalizar processos restic
        try:
            subprocess.run(['taskkill', '/f', '/im', 'restic.exe'], 
                         capture_output=True)
            print("Processos restic finalizados")
        except:
            pass

def main():
    """Funcao principal"""
    print("Safestic - Unmount Repository")
    print()
    
    # Carregar configuracao
    if not load_config():
        return 1
    
    # Definir ponto de montagem
    default_mount = './mount' if os.name == 'posix' else '.\\mount'
    mount_path = os.getenv('MOUNT_POINT', default_mount)
    
    print(f"Ponto de montagem: {mount_path}")
    
    # Verificar status atual
    is_mounted = check_mount_status(mount_path)
    
    if not is_mounted:
        print("Repositorio nao esta montado")
        return 0
    
    print("Desmontando repositorio...")
    
    # Desmontar baseado no sistema
    success = False
    system = os.name
    
    if system == 'posix':  # Linux/macOS
        success = unmount_linux(mount_path)
    elif system == 'nt':  # Windows
        success = unmount_windows(mount_path)
    else:
        print(f"Sistema nao suportado: {system}")
        return 1
    
    if success:
        print("Repositorio desmontado com sucesso!")
        return 0
    else:
        print("Falha na desmontagem normal. Tentando limpeza forcada...")
        force_cleanup(mount_path)
        
        # Verificar novamente
        if not check_mount_status(mount_path):
            print("Limpeza forcada bem-sucedida!")
            return 0
        else:
            print("Falha na desmontagem. Intervencao manual necessaria.")
            print("Dicas:")
            print("   - Feche todos os programas que estao acessando o ponto de montagem")
            print("   - Reinicie o terminal ou sistema se necessario")
            print(f"   - Remova manualmente o diretorio: {mount_path}")
            return 1

if __name__ == '__main__':
    sys.exit(main())
