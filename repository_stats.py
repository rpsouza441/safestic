"""Show overall size information about the Restic repository."""

from __future__ import annotations

import logging
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError, load_env_and_get_credential_source


def show_repository_stats() -> None:
    """Print repository size information.
    
    Utiliza o ResticClient para obter estatisticas com retry automatico e tratamento de erros.
    """
    credential_source = load_env_and_get_credential_source()
    with ResticScript("repository_stats", credential_source=credential_source) as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log(f"Obtendo estatisticas gerais do repositorio: {ctx.repository}\n")

        try:
            # Criar cliente Restic com retry usando o ambiente já carregado
            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source
            )
            
            # Obter estatisticas do repositorio
            stats = client.get_stats()
            
            if stats:
                size_bytes = stats.get("total_size", 0)
                size_gib = size_bytes / (1024 ** 3)
                print(
                    f"Tamanho total armazenado no repositorio (dados unicos): {size_gib:.3f} GiB",
                )
            else:
                ctx.log("Nao foi possivel obter estatisticas do repositorio.")
                sys.exit(1)
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    show_repository_stats()


