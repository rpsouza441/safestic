import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura arquivo ou diretório específico de um snapshot",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    parser.add_argument(
        "--path",
        required=True,
        help="Caminho do arquivo ou diretório a restaurar",
    )
    return parser.parse_args()


def run_restore_file(snapshot_id: str, include_path: str) -> None:
    """Restaura arquivo ou diretório específico do snapshot.
    
    Utiliza o ResticClient para executar a restauração com retry automático e tratamento de erros.
    
    Parameters
    ----------
    snapshot_id : str
        ID do snapshot a ser restaurado ou "latest" para o mais recente
    include_path : str
        Caminho do arquivo ou diretório a ser restaurado
    """
    with ResticScript("restore_file") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        base_restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
        ctx.log("=== Iniciando restauração de arquivo com Restic ===")
        
        try:
            # Criar diretório de destino
            Path(base_restore_target).mkdir(parents=True, exist_ok=True)
            
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Obter informações do snapshot
            ctx.log(f"Buscando informações do snapshot '{snapshot_id}'...")
            snapshot_data = client.get_snapshot_info(snapshot_id)
            
            # Formatar data do snapshot
            snapshot_time = datetime.fromisoformat(
                snapshot_data["time"].replace("Z", "+00:00")
            )
            timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H%M%S")
            restore_target = os.path.join(base_restore_target, timestamp_str)
            Path(restore_target).mkdir(parents=True, exist_ok=True)
            
            # Exibir informações
            ctx.log(f"Snapshot ID: {snapshot_data['short_id']}")
            ctx.log(
                f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ctx.log(f"Arquivo/diretório a restaurar: {include_path}")
            ctx.log(f"Destino da restauração: {restore_target}")
            
            # Executar restauração do arquivo específico
            success = client.restore_snapshot(
                target_dir=restore_target,
                snapshot_id=snapshot_id,
                include_path=include_path
            )
            
            if success:
                ctx.log("✅ Arquivo ou diretório restaurado com sucesso.")
            else:
                ctx.log("Erro durante a restauração")
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
        finally:
            ctx.log("=== Fim do processo de restauração ===")


if __name__ == "__main__":
    args = parse_args()
    run_restore_file(args.id, args.path)
