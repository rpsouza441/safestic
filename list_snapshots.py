"""List all snapshots stored in the configured Restic repository."""

from __future__ import annotations

import sys
from datetime import datetime
from services.script import ResticScript
from services.restic_client import ResticClient, ResticError
from services.env import get_credential_source


def list_snapshots() -> None:
    """Fetch and print all snapshots from the repository.
    
    Utiliza o ResticClient para obter a lista de snapshots com retry automatico e tratamento de erros.
    """
    credential_source = get_credential_source()

    with ResticScript("list_snapshots", credential_source=credential_source) as ctx:
        ctx.log(f"Listando snapshots do repositorio: {ctx.repository}\n")

        try:
            # Criar cliente Restic com retry usando o ambiente já carregado
            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source
            )
            
            # Obter lista de snapshots
            snapshots = client.list_snapshots()
            
            if not snapshots:
                ctx.log("Nenhum snapshot encontrado no repositorio.")
                sys.exit(0)

            print("{:<12} {:<20} {:<15} {}".format("ID", "Data", "Host", "Caminhos"))
            print("-" * 80)

            for snap in snapshots:
                snapshot_time = datetime.fromisoformat(
                    snap["time"].replace("Z", "+00:00")
                )
                formatted_time = snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
                paths = ", ".join(snap["paths"])
                print(
                    "{:<12} {:<20} {:<15} {}".format(
                        snap["short_id"],
                        formatted_time,
                        snap["hostname"],
                        paths,
                    )
                )

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    list_snapshots()

