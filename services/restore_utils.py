#!/usr/bin/env python3
"""
Utilitários para operações de restore - Safestic
Funções auxiliares para criação de estrutura de pastas baseada em timestamp
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def create_timestamped_restore_path(
    base_restore_dir: str,
    snapshot_data: Dict[str, Any],
    original_paths: list = None
) -> str:
    """
    Cria estrutura de pastas para restore baseada na data/hora do snapshot.
    
    Formato: C:\\Restore\\2025-08-19-100320\\C\\Users\\Administrator\\Documents\\Docker
    
    Parameters
    ----------
    base_restore_dir : str
        Diretório base para restore (ex: "C:\\Restore")
    snapshot_data : Dict[str, Any]
        Dados do snapshot contendo informações de data/hora
    original_paths : list, optional
        Caminhos originais do backup para recriar estrutura
        
    Returns
    -------
    str
        Caminho completo da estrutura de restore criada
    """
    # Extrair e formatar timestamp do snapshot
    snapshot_time = datetime.fromisoformat(
        snapshot_data["time"].replace("Z", "+00:00")
    )
    
    # Formato: AAAA-MM-DD-HHMMSS
    timestamp_str = snapshot_time.strftime("%Y-%m-%d-%H%M%S")
    
    # Criar pasta com timestamp
    timestamped_dir = Path(base_restore_dir) / timestamp_str
    timestamped_dir.mkdir(parents=True, exist_ok=True)
    
    return str(timestamped_dir)


def create_full_restore_structure(
    base_restore_dir: str,
    snapshot_data: Dict[str, Any],
    original_path: str = None
) -> str:
    """
    Cria estrutura completa de restore incluindo recriação da estrutura de diretórios original.
    
    Exemplo:
    - Input: original_path = "C:\\Users\\Administrator\\Documents\\Docker"
    - Output: "C:\\Restore\\2025-08-19-100320\\C\\Users\\Administrator\\Documents\\Docker"
    
    Parameters
    ----------
    base_restore_dir : str
        Diretório base para restore
    snapshot_data : Dict[str, Any]
        Dados do snapshot
    original_path : str, optional
        Caminho original para recriar estrutura
        
    Returns
    -------
    str
        Caminho completo incluindo estrutura de diretórios original
    """
    # Criar pasta com timestamp
    timestamped_dir = create_timestamped_restore_path(base_restore_dir, snapshot_data)
    
    if not original_path:
        return timestamped_dir
    
    # Normalizar caminho original removendo caracteres especiais do Windows
    # Converter C:\ para C\ para evitar problemas com dois pontos
    normalized_path = original_path.replace(":", "")
    
    # Remover barras iniciais se existirem
    if normalized_path.startswith(("\\", "/")):
        normalized_path = normalized_path[1:]
    
    # Criar estrutura completa
    full_restore_path = Path(timestamped_dir) / normalized_path
    full_restore_path.mkdir(parents=True, exist_ok=True)
    
    return str(full_restore_path)


def get_snapshot_paths_from_data(snapshot_data: Dict[str, Any]) -> list:
    """
    Extrai os caminhos originais dos dados do snapshot.
    
    Parameters
    ----------
    snapshot_data : Dict[str, Any]
        Dados do snapshot
        
    Returns
    -------
    list
        Lista de caminhos originais do backup
    """
    paths = snapshot_data.get("paths", [])
    if isinstance(paths, list):
        return paths
    elif isinstance(paths, str):
        return [paths]
    else:
        return []


def format_restore_info(
    snapshot_data: Dict[str, Any],
    restore_path: str,
    original_path: str = None
) -> Dict[str, str]:
    """
    Formata informações do restore para exibição.
    
    Parameters
    ----------
    snapshot_data : Dict[str, Any]
        Dados do snapshot
    restore_path : str
        Caminho de destino do restore
    original_path : str, optional
        Caminho original sendo restaurado
        
    Returns
    -------
    Dict[str, str]
        Informações formatadas para exibição
    """
    snapshot_time = datetime.fromisoformat(
        snapshot_data["time"].replace("Z", "+00:00")
    )
    
    info = {
        "snapshot_id": snapshot_data.get("short_id", "N/A"),
        "snapshot_date": snapshot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": snapshot_data.get("hostname", "N/A"),
        "restore_target": restore_path,
    }
    
    if original_path:
        info["original_path"] = original_path
    
    original_paths = get_snapshot_paths_from_data(snapshot_data)
    if original_paths:
        info["backup_paths"] = ", ".join(original_paths)
    
    return info