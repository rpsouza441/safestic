import argparse
import datetime
import json
import os
from pathlib import Path

from services.script import ResticScript


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura um snapshot inteiro para o diretório alvo",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot a restaurar")
    return parser.parse_args()


def run_restore_snapshot(snapshot_id: str) -> None:
    """Restaura um snapshot inteiro para o diretório alvo."""

    with ResticScript("restore_snapshot") as ctx:
        restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
        ctx.log("=== Iniciando restauração de snapshot com Restic ===")

        try:
            Path(restore_target).mkdir(parents=True, exist_ok=True)
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

            snapshot_time = datetime.datetime.fromisoformat(
                snapshot_data["time"].replace("Z", "+00:00")
            )

            ctx.log(f"Snapshot ID: {snapshot_data['short_id']}")
            ctx.log(
                f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ctx.log(f"Destino da restauração: {restore_target}")
            print("\nIniciando processo de restauração... O progresso será exibido abaixo.")

            ctx.run_cmd(
                [
                    "restic",
                    "-r",
                    ctx.repository,
                    "restore",
                    snapshot_id,
                    "--target",
                    restore_target,
                ],
                success_msg="✅ Restauração de snapshot concluída com sucesso.",
                error_msg="Erro durante a restauração",
            )

        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")

        finally:
            ctx.log("=== Fim do processo de restauração ===")


if __name__ == "__main__":
    args = parse_args()
    run_restore_snapshot(args.id)
