import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from services.script import ResticScript


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
    """Restaura arquivo ou diretório específico do snapshot."""

    with ResticScript("restore_file") as ctx:
        base_restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
        ctx.log("=== Iniciando restauração de arquivo com Restic ===")
        try:
            Path(base_restore_target).mkdir(parents=True, exist_ok=True)
            ctx.log(f"Buscando informações do snapshot '{snapshot_id}'...")
            success, result = ctx.run_cmd(
                [
                    "restic",
                    "-r",
                    ctx.repository,
                    "snapshots",
                    snapshot_id,
                    "--json",
                ],
                error_msg="Falha ao buscar informações do snapshot",
            )
            if not success or result is None:
                return
            snapshot_data = json.loads(result.stdout)[0]
            snapshot_time = datetime.fromisoformat(
                snapshot_data["time"].replace("Z", "+00:00")
            )
            timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H%M%S")
            restore_target = os.path.join(base_restore_target, timestamp_str)
            Path(restore_target).mkdir(parents=True, exist_ok=True)

            ctx.log(f"Snapshot ID: {snapshot_data['short_id']}")
            ctx.log(
                f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ctx.log(f"Arquivo/diretório a restaurar: {include_path}")
            ctx.log(f"Destino da restauração: {restore_target}")

            ctx.run_cmd(
                [
                    "restic",
                    "-r",
                    ctx.repository,
                    "restore",
                    snapshot_id,
                    "--target",
                    restore_target,
                    "--include",
                    include_path,
                ],
                success_msg="✅ Arquivo ou diretório restaurado com sucesso.",
                error_msg="Erro durante a restauração",
            )

        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")

        finally:
            ctx.log("=== Fim do processo de restauração ===")


if __name__ == "__main__":
    args = parse_args()
    run_restore_file(args.id, args.path)
