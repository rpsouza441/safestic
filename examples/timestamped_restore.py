#!/usr/bin/env python3
"""
Exemplo de uso da funcionalidade de restore com estrutura de pastas baseada em timestamp - Safestic

Este exemplo demonstra como a nova funcionalidade cria automaticamente
estrutura de pastas organizadas por data/hora do snapshot.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Adicionar o diretório pai ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.restic_client import ResticClient, ResticError, load_env_and_get_credential_source
from services.restore_utils import (
    create_timestamped_restore_path,
    create_full_restore_structure,
    format_restore_info,
    get_snapshot_paths_from_data
)


def demonstrate_timestamped_restore():
    """
    Demonstra a funcionalidade de restore com estrutura baseada em timestamp.
    """
    print("🔄 Demonstração: Restore com Estrutura de Pastas Baseada em Timestamp")
    print("=" * 70)
    
    try:
        credential_source = load_env_and_get_credential_source()

        # Criar cliente Restic
        client = ResticClient(credential_source=credential_source)
        
        # Listar snapshots disponíveis
        print("\n📋 Listando snapshots disponíveis...")
        snapshots = client.list_snapshots()
        
        if not snapshots:
            print("❌ Nenhum snapshot encontrado. Execute um backup primeiro.")
            return
        
        # Usar o snapshot mais recente para demonstração
        latest_snapshot = snapshots[0]
        snapshot_id = latest_snapshot.get('short_id', latest_snapshot.get('id', 'latest'))
        
        print(f"\n🎯 Usando snapshot: {snapshot_id}")
        print(f"   Data: {latest_snapshot.get('time', 'N/A')}")
        print(f"   Hostname: {latest_snapshot.get('hostname', 'N/A')}")
        
        # Demonstrar criação de estrutura básica (para restore completo)
        print("\n🏗️  Estrutura para Restore Completo:")
        base_restore_dir = "C:\\Restore"
        
        timestamped_path = create_timestamped_restore_path(
            base_restore_dir, 
            latest_snapshot
        )
        
        print(f"   Base: {base_restore_dir}")
        print(f"   Estrutura criada: {timestamped_path}")
        
        # Demonstrar criação de estrutura completa (para restore de arquivo específico)
        print("\n🗂️  Estrutura para Restore de Arquivo Específico:")
        
        # Simular diferentes caminhos originais
        example_paths = [
            "C:\\Users\\Administrator\\Documents\\Docker",
            "C:\\Program Files\\MyApp\\config.json",
            "/home/user/documents/important.txt",
            "D:\\Backup\\Photos\\2024"
        ]
        
        for original_path in example_paths:
            full_restore_path = create_full_restore_structure(
                base_restore_dir,
                latest_snapshot,
                original_path
            )
            
            print(f"   Original: {original_path}")
            print(f"   Restore:  {full_restore_path}")
            print()
        
        # Demonstrar formatação de informações
        print("📊 Informações Formatadas do Snapshot:")
        info = format_restore_info(
            latest_snapshot, 
            timestamped_path, 
            "C:\\Users\\Administrator\\Documents"
        )
        
        for key, value in info.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        print("\n✅ Demonstração concluída!")
        print("\n💡 Como usar:")
        print("   make restore              # Restore completo com timestamp")
        print("   make restore-id ID=abc123 # Restore específico com timestamp")
        print('   make restore-file ID=abc123 FILE="C:\\Users\\Admin\\Docs" # Arquivo com estrutura completa')
        
    except ResticError as e:
        print(f"❌ Erro do Restic: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


def show_structure_examples():
    """
    Mostra exemplos de estruturas que serão criadas.
    """
    print("\n📁 Exemplos de Estruturas Criadas:")
    print("=" * 50)
    
    # Simular dados de snapshot
    mock_snapshot = {
        "time": "2025-08-19T10:03:20Z",
        "short_id": "17124d3c",
        "hostname": "WIN-KPFK358LIMR",
        "paths": ["C:\\Users\\Administrator\\Documents\\Docker"]
    }
    
    base_dir = "C:\\Restore"
    
    print(f"\n🕐 Snapshot de: 2025-08-19 10:03:20")
    print(f"📂 Diretório base: {base_dir}")
    print()
    
    # Exemplo 1: Restore completo
    timestamped = create_timestamped_restore_path(base_dir, mock_snapshot)
    print(f"1️⃣  Restore Completo:")
    print(f"   {timestamped}")
    print()
    
    # Exemplo 2: Restore de arquivo específico
    examples = [
        "C:\\Users\\Administrator\\Documents\\Docker",
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
        "D:\\Projects\\MyApp\\src\\main.py"
    ]
    
    print(f"2️⃣  Restore de Arquivos Específicos:")
    for i, path in enumerate(examples, 1):
        full_path = create_full_restore_structure(base_dir, mock_snapshot, path)
        print(f"   {i}. Original: {path}")
        print(f"      Restore:  {full_path}")
        print()


if __name__ == "__main__":
    print("🚀 Safestic - Exemplo de Restore com Timestamp")
    print()
    
    # Verificar se há argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--examples-only":
        show_structure_examples()
    else:
        demonstrate_timestamped_restore()
        show_structure_examples()