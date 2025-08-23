import argparse
import logging

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
)
from services.env import get_credential_source
from services.restore_utils import (
    create_timestamped_restore_path,
    format_restore_info,
    get_snapshot_paths_from_data,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura um snapshot inteiro para o diretorio alvo",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot a restaurar")
    return parser.parse_args()


def run_restore_snapshot(snapshot_id: str) -> None:
    """Restaura um snapshot inteiro para o diretorio alvo.
    
    Utiliza o ResticClient para executar a restauracao com retry automatico e tratamento de erros.
    
    Parameters
    ----------
    snapshot_id : str
        ID do snapshot a ser restaurado ou "latest" para o mais recente
    """
    credential_source = get_credential_source()
    
    with ResticScript("restore_snapshot", credential_source=credential_source) as ctx:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

        base_restore_target = (
            ctx.config.restore_target_dir
            if ctx.config and ctx.config.restore_target_dir
            else "C:\\Restore"
        )
        ctx.log("=== Iniciando restauracao de snapshot com Restic ===")

        try:
            # Criar cliente Restic com retry usando o ambiente já carregado
            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source
            )
            
            # Obter informacoes do snapshot
            ctx.log(f"Buscando informacoes do snapshot '{snapshot_id}'...")
            snapshot_data = client.get_snapshot_info(snapshot_id)
            
            # Criar estrutura de pastas baseada na data/hora do snapshot
            # Formato: C:\Restore\2025-08-19-100320
            restore_target = create_timestamped_restore_path(
                base_restore_target, 
                snapshot_data
            )
            
            # Obter caminhos originais do backup para informação
            original_paths = get_snapshot_paths_from_data(snapshot_data)
            
            # Formatar e exibir informacoes
            info = format_restore_info(snapshot_data, restore_target)
            
            ctx.log(f"Snapshot ID: {info['snapshot_id']}")
            ctx.log(f"Data do Snapshot: {info['snapshot_date']}")
            ctx.log(f"Hostname: {info['hostname']}")
            if original_paths:
                ctx.log(f"Caminhos originais: {', '.join(original_paths)}")
            ctx.log(f"Destino da restauracao: {restore_target}")
            ctx.log(f"Estrutura: {base_restore_target}\\{info['snapshot_date'].replace(' ', '-').replace(':', '')}\\<estrutura_original>")
            print("\nIniciando processo de restauracao... O progresso sera exibido abaixo.")

            # Executar restauracao
            success = client.restore_snapshot(
                target_dir=restore_target,
                snapshot_id=snapshot_id,
            )
            
            if success:
                ctx.log("✅ Restauracao de snapshot concluida com sucesso.")
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
    run_restore_snapshot(args.id)

