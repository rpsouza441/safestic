#!/usr/bin/env python3
"""Script para verificar e corrigir o ambiente antes de executar make check."""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Executa um comando e retorna o resultado."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_virtual_env():
    """Verifica se está em ambiente virtual."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    venv_path = Path('.venv')
    
    print(f"Python executável: {sys.executable}")
    print(f"Ambiente virtual ativo: {'Sim' if in_venv else 'Não'}")
    print(f"Diretório .venv existe: {'Sim' if venv_path.exists() else 'Não'}")
    
    return in_venv, venv_path.exists()

def check_dependencies():
    """Verifica se as dependências críticas estão instaladas."""
    critical_deps = [
        'pydantic',
        'dotenv', 
        'colorama',
        'requests',
        'psutil',
        'pythonjsonlogger'
    ]
    
    missing = []
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}: OK")
        except ImportError:
            print(f"❌ {dep}: FALTANDO")
            missing.append(dep)
    
    return missing

def check_project_modules():
    """Verifica se os módulos do projeto podem ser importados."""
    project_modules = [
        'services.logger',
        'services.credentials', 
        'services.restic_client',
        'services.script'
    ]
    
    failed = []
    for module in project_modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except ImportError as e:
            print(f"❌ {module}: ERRO - {e}")
            failed.append(module)
    
    return failed

def reinstall_dependencies():
    """Reinstala as dependências do projeto."""
    print("\n🔧 Reinstalando dependências...")
    
    # Tentar instalar via pyproject.toml
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -e .")
    if success:
        print("✅ Dependências principais instaladas via pyproject.toml")
    else:
        print(f"❌ Erro ao instalar via pyproject.toml: {stderr}")
        
        # Fallback para requirements.txt
        if Path('requirements.txt').exists():
            print("Tentando instalar via requirements.txt...")
            success, stdout, stderr = run_command(f"{sys.executable} -m pip install -r requirements.txt")
            if success:
                print("✅ Dependências instaladas via requirements.txt")
            else:
                print(f"❌ Erro ao instalar via requirements.txt: {stderr}")
                return False
    
    return True

def main():
    print("=== VERIFICAÇÃO DO AMBIENTE SAFESTIC ===")
    print(f"Diretório atual: {Path.cwd()}")
    print(f"Sistema operacional: {os.name}")
    
    # Verificar ambiente virtual
    print("\n=== AMBIENTE VIRTUAL ===")
    in_venv, venv_exists = check_virtual_env()
    
    if not in_venv and venv_exists:
        print("\n⚠️ AVISO: Ambiente virtual existe mas não está ativo!")
        if os.name != 'nt':  # Linux/Unix
            print("Execute: source .venv/bin/activate")
        else:  # Windows
            print("Execute: .venv\\Scripts\\Activate.ps1")
        print("Depois execute novamente este script.\n")
    
    # Verificar dependências
    print("\n=== DEPENDÊNCIAS CRÍTICAS ===")
    missing_deps = check_dependencies()
    
    # Verificar módulos do projeto
    print("\n=== MÓDULOS DO PROJETO ===")
    failed_modules = check_project_modules()
    
    # Análise e correção
    if missing_deps or failed_modules:
        print("\n❌ PROBLEMAS DETECTADOS:")
        if missing_deps:
            print(f"   Dependências faltando: {', '.join(missing_deps)}")
        if failed_modules:
            print(f"   Módulos com erro: {', '.join(failed_modules)}")
        
        print("\n🔧 TENTANDO CORRIGIR...")
        if reinstall_dependencies():
            print("\n✅ Correção aplicada. Execute novamente para verificar.")
            return 0
        else:
            print("\n❌ Falha na correção automática.")
            print("\nSOLUÇÕES MANUAIS:")
            print("1. Ativar ambiente virtual:")
            if os.name != 'nt':
                print("   source .venv/bin/activate")
            else:
                print("   .venv\\Scripts\\Activate.ps1")
            print("2. Reinstalar dependências:")
            print("   pip install -e .")
            print("3. Verificar novamente:")
            print("   python scripts/verify_environment.py")
            return 1
    else:
        print("\n🎉 AMBIENTE OK! Pode executar make check com segurança.")
        return 0

if __name__ == "__main__":
    sys.exit(main())