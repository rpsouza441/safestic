#!/usr/bin/env python3
"""
Script para verificar suporte ao comando mount do Restic - SafeStic
Verifica se WinFsp esta instalado e se o comando mount esta disponivel
"""

import os
import sys
import subprocess
from pathlib import Path

def check_winfsp():
    """Verifica se WinFsp esta instalado"""
    winfsp_paths = [
        "C:\\Program Files\\WinFsp\\bin\\launchctl-x64.exe",
        "C:\\Program Files (x86)\\WinFsp\\bin\\launchctl-x64.exe"
    ]
    
    for path in winfsp_paths:
        if Path(path).exists():
            print(f"✅ WinFsp encontrado: {path}")
            return True
    
    print("❌ WinFsp nao encontrado")
    print("💡 Instale WinFsp de: https://winfsp.dev/rel/")
    return False

def check_restic_mount():
    """Verifica se o comando mount esta disponivel no restic"""
    try:
        result = subprocess.run(
            ["restic", "help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            if "mount" in result.stdout:
                print("✅ Comando 'restic mount' esta disponivel")
                return True
            else:
                print("❌ Comando 'restic mount' nao esta disponivel")
                print("ℹ️  Nota: Algumas versoes do restic nao incluem o comando mount")
                return False
        else:
            print(f"❌ Erro ao executar 'restic help': {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao executar 'restic help'")
        return False
    except FileNotFoundError:
        print("❌ Restic nao encontrado no PATH")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def check_mount_prerequisites():
    """Verifica todos os pre-requisitos para o comando mount"""
    print("🔍 Verificando suporte ao comando mount...\n")
    
    # Verificar sistema operacional
    if os.name != 'nt':
        print("ℹ️  Este script e especifico para Windows")
        return False
    
    print("✅ Sistema operacional: Windows")
    
    # Verificar WinFsp
    winfsp_ok = check_winfsp()
    
    # Verificar Restic
    restic_ok = check_restic_mount()
    
    print("\n" + "="*50)
    
    if winfsp_ok and restic_ok:
        print("🎉 SUCESSO: Comando 'restic mount' deve funcionar!")
        print("\n💡 Exemplo de uso:")
        print("   make mount")
        print("   # ou")
        print("   python scripts/mount_repo.py")
        return True
    else:
        print("⚠️  AVISO: Comando 'restic mount' pode nao funcionar")
        print("\n🔧 Para corrigir:")
        
        if not winfsp_ok:
            print("   1. Instale WinFsp: https://winfsp.dev/rel/")
            print("   2. Reinicie o sistema apos a instalacao")
        
        if not restic_ok:
            print("   3. Instale uma versao do Restic com suporte ao mount:")
            print("      - Download direto: https://github.com/restic/restic/releases")
            print("      - Ou compile com: go install github.com/restic/restic/cmd/restic@latest")
            print("   4. Verifique: restic version (deve mostrar versao completa)")
        
        print("\n🔄 Alternativa: Use 'make restore' ao inves de 'mount'")
        return False

def main():
    """Funcao principal"""
    try:
        success = check_mount_prerequisites()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Verificacao interrompida pelo usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
