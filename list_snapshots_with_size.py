"""List snapshots and their approximate restore size from a Restic repository."""

from __future__ import annotations

import json
import sys
import logging

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def list_snapshots_with_size() -> None:
    """Print snapshot information including estimated restore size.
    
    Utiliza o ResticClient para obter snapshots e seus tamanhos com retry automático e tratamento de erros.
    """
    with ResticScript("list_snapshots_with_size") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        try:
            # Criar cliente Restic com retry
            client = ResticClient(repository=ctx.repository, max_attempts=3)
            
            # Obter lista de snapshots
            snapshots = client.list_snapshots()
            
            if not snapshots:
                ctx.log("Nenhum snapshot encontrado no repositório.")
                return

            ctx.log(f"Listando snapshots do repositório: {ctx.repository}\n")

            for snap in snapshots:
                short_id = snap["short_id"]
                time = snap["time"]
                hostname = snap["hostname"]
                paths = ", ".join(snap["paths"])

                try:
                    stats = client.get_snapshot_size(short_id)
                    if stats and "total_size" in stats:
                        total_bytes = stats.get("total_size", 0)
                        total_gib = total_bytes / (1024 ** 3)
                        print(
                            f"{short_id} | {time} | {hostname} | {paths} | {total_gib:.3f} GiB",
                        )
                    else:
                        print(
                            f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)",
                        )
                except ResticError:
                    print(
                        f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)",
                    )

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    list_snapshots_with_size()
