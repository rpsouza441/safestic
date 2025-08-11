import argparse
import sys

from services.script import ResticScript


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista os arquivos contidos em um snapshot específico",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    return parser.parse_args()


def main(snapshot_id: str) -> None:
    with ResticScript("list_snapshot_files") as ctx:
        ctx.log(f"📂 Listando arquivos do snapshot '{snapshot_id}'...")
        success, _ = ctx.run_cmd(
            ["restic", "-r", ctx.repository, "ls", snapshot_id],
            error_msg="Falha ao listar arquivos do snapshot",
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    main(args.id)
