import argparse
import logging
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista os arquivos contidos em um snapshot específico",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    return parser.parse_args()


def main(snapshot_id: str) -> None:
    with ResticScript("list_snapshot_files") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log(f"📂 Listando arquivos do snapshot '{snapshot_id}'...")
        
        try:
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Listar arquivos do snapshot
            files = client.list_snapshot_files(snapshot_id)
            
            # Exibir resultado
            if files:
                print(files)
            else:
                ctx.log("Nenhum arquivo encontrado no snapshot.")
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    main(args.id)
