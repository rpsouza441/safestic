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
        description="Restaura arquivo ou diretorio especifico de um snapshot",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    parser.add_argument(
        "--path",
        required=True,
        help="Caminho do arquivo ou diretorio a restaurar",
    )
    return parser.parse_args()


def run_restore_file(snapshot_id: str, include_path: str) -> None:
    """Restaura arquivo ou diretorio especifico do snapshot.
    
    Utiliza o ResticClient para executar a restauracao com retry automatico e tratamento de erros.
    
    Parameters
    ----------
    snapshot_id : str
        ID do snapshot a ser restaurado ou "latest" para o mais recente
    include_path : str
        Caminho do arquivo ou diretorio a ser restaurado
    """
    with ResticScript("restore_file") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        base_restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
        ctx.log("=== Iniciando restauracao de arquivo com Restic ===")
        
        try:
            # Criar diretorio de destino
            Path(base_restore_target).mkdir(parents=True, exist_ok=True)
            
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Obter informacoes do snapshot
            ctx.log(f"Buscando informacoes do snapshot '{snapshot_id}'...")
            snapshot_data = client.get_snapshot_info(snapshot_id)
            
            # Formatar data do snapshot
            snapshot_time = datetime.fromisoformat(
                snapshot_data["time"].replace("Z", "+00:00")
            )
            timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H%M%S")
            restore_target = os.path.join(base_restore_target, timestamp_str)
            Path(restore_target).mkdir(parents=True, exist_ok=True)
            
            # Exibir informacoes
            ctx.log(f"Snapshot ID: {snapshot_data['short_id']}")
            ctx.log(
                f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ctx.log(f"Arquivo/diretorio a restaurar: {include_path}")
            ctx.log(f"Destino da restauracao: {restore_target}")
            
            # Executar restauracao do arquivo especifico
            success = client.restore_snapshot(
                target_dir=restore_target,
                snapshot_id=snapshot_id,
                include_paths=[include_path]
            )
            
            if success:
                ctx.log("✅ Arquivo ou diretorio restaurado com sucesso.")
            else:
                ctx.log("Erro durante a restauracao")
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
        finally:
            ctx.log("=== Fim do processo de restauracao ===")


if __name__ == "__main__":
    args = parse_args()
    run_restore_file(args.id, args.path)

