"""List snapshots and their approximate restore size from a Restic repository."""

from __future__ import annotations

import logging

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def list_snapshots_with_size() -> None:
    """Print snapshot information including estimated restore size.
    
    Utiliza o ResticClient para obter snapshots e seus tamanhos com retry automatico e tratamento de erros.
    """
    # Usar ResticScript que já carrega as credenciais corretamente
    with ResticScript("list_snapshots_with_size") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=ctx.credential_source,
            )
            
            # Obter lista de snapshots
            snapshots = client.list_snapshots()
            
            if not snapshots:
                ctx.log("Nenhum snapshot encontrado no repositorio.")
                return

            ctx.log(f"Listando snapshots do repositorio: {ctx.repository}\n")

            for snap in snapshots:
                short_id = snap["short_id"]
                time = snap["time"]
                hostname = snap["hostname"]
                paths = ", ".join(snap["paths"])

                # Para snapshots individuais, nao ha comando direto para obter tamanho
                # Vamos mostrar apenas as informacoes basicas
                print(f"{short_id:<12} {time:<20} {hostname:<15} {paths}")

            # Mostrar estatisticas gerais do repositorio
            try:
                repo_stats = client.get_repository_stats()
                if repo_stats and "total_size" in repo_stats:
                    total_repo_bytes = repo_stats.get("total_size", 0)
                    total_repo_gib = total_repo_bytes / (1024 ** 3)
                    ctx.log(f"\nTamanho total do repositorio: {total_repo_gib:.3f} GiB")
            except ResticError as e:
                ctx.log(f"Erro ao obter estatisticas do repositorio: {e}")

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            raise SystemExit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            raise SystemExit(1)


if __name__ == "__main__":
    list_snapshots_with_size()

