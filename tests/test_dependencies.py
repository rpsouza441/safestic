#!/usr/bin/env python3
"""Script para verificar se todas as dependências estão instaladas corretamente."""

import sys
import importlib
import subprocess
from pathlib import Path

def check_import(module_name, package_name=None):
    """Testa se um módulo pode ser importado."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}: OK")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: FALTANDO - {e}")
        if package_name:
            print(f"   Instale com: pip install {package_name}")
        return False

def check_pip_list():
    """Verifica pacotes instalados via pip."""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📦 Pacotes instalados:")
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Skip header
                if line.strip():
                    print(f"   {line}")
        return result.stdout
    except Exception as e:
        print(f"❌ Erro ao verificar pip list: {e}")
        return ""

def main():
    print("=== VERIFICAÇÃO DE DEPENDÊNCIAS ===")
    print(f"Python: {sys.version}")
    print(f"Executável: {sys.executable}")
    print(f"Diretório atual: {Path.cwd()}")
    
    # Verificar se está em ambiente virtual
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Ambiente virtual detectado")
    else:
        print("⚠️ Não está em ambiente virtual")
    
    print("\n=== TESTANDO IMPORTAÇÕES ===")
    
    # Dependências principais
    dependencies = [
        ('pydantic', 'pydantic>=2.0.0'),
        ('dotenv', 'python-dotenv>=1.0.0'),
        ('colorama', 'colorama>=0.4.6'),
        ('requests', 'requests>=2.31.0'),
        ('psutil', 'psutil>=5.9.0'),
        ('pythonjsonlogger', 'python-json-logger>=2.0.0'),
    ]
    
    # Dependências opcionais
    optional_dependencies = [
        ('keyring', 'keyring>=24.0.0'),
        ('secretstorage', 'secretstorage>=3.0.0'),
        ('dbus', 'dbus-python>=1.2.0'),
    ]
    
    # Testar dependências principais
    failed_main = []
    for module, package in dependencies:
        if not check_import(module, package):
            failed_main.append((module, package))
    
    print("\n=== TESTANDO DEPENDÊNCIAS OPCIONAIS ===")
    failed_optional = []
    for module, package in optional_dependencies:
        if not check_import(module, package):
            failed_optional.append((module, package))
    
    # Testar importações específicas do projeto
    print("\n=== TESTANDO MÓDULOS DO PROJETO ===")
    project_modules = [
        'services.logger',
        'services.credentials',
        'services.restic_client',
        'services.script',
    ]
    
    failed_project = []
    for module in project_modules:
        if not check_import(module):
            failed_project.append(module)
    
    # Verificar pip list
    pip_output = check_pip_list()
    
    # Resumo
    print("\n=== RESUMO ===")
    print(f"Dependências principais: {len(dependencies) - len(failed_main)}/{len(dependencies)} OK")
    print(f"Dependências opcionais: {len(optional_dependencies) - len(failed_optional)}/{len(optional_dependencies)} OK")
    print(f"Módulos do projeto: {len(project_modules) - len(failed_project)}/{len(project_modules)} OK")
    
    if failed_main:
        print("\n❌ DEPENDÊNCIAS PRINCIPAIS FALTANDO:")
        for module, package in failed_main:
            print(f"   pip install {package}")
    
    if failed_optional:
        print("\n⚠️ DEPENDÊNCIAS OPCIONAIS FALTANDO:")
        for module, package in failed_optional:
            print(f"   pip install {package}")
    
    if failed_project:
        print("\n❌ MÓDULOS DO PROJETO COM PROBLEMA:")
        for module in failed_project:
            print(f"   {module}")
    
    # Sugestões de correção
    if failed_main or failed_project:
        print("\n🔧 SUGESTÕES DE CORREÇÃO:")
        print("1. Reinstalar dependências: pip install -e .")
        print("2. Atualizar pip: python -m pip install --upgrade pip")
        print("3. Verificar ambiente virtual: source .venv/bin/activate")
        return 1
    else:
        print("\n🎉 Todas as dependências principais estão OK!")
        return 0

if __name__ == "__main__":
    sys.exit(main())