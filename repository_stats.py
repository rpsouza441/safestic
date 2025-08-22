"""Show overall size information about the Restic repository."""

from __future__ import annotations

import logging

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def show_repository_stats() -> None:
    """Print repository size information.
    
    Utiliza o ResticClient para obter estatisticas com retry automatico e tratamento de erros.
    """
    # Usar ResticScript que já carrega as credenciais corretamente
    with ResticScript("repository_stats") as ctx:
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
                credential_source=ctx.credential_source,
            )
            
            # Obter estatisticas do repositorio
            stats = client.get_repository_stats()
            
            if stats:
                size_bytes = stats.get("total_size", 0)
                size_gib = size_bytes / (1024 ** 3)
                print(
                    f"Tamanho total armazenado no repositorio (dados unicos): {size_gib:.3f} GiB",
                )
            else:
                ctx.log("Nao foi possivel obter estatisticas do repositorio.")
                raise SystemExit(1)
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            raise SystemExit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            raise SystemExit(1)


if __name__ == "__main__":
    show_repository_stats()


