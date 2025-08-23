import argparse

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
)
from services.env import get_credential_source
from services.restore_utils import (
    create_full_restore_structure,
    format_restore_info,
    get_snapshot_paths_from_data,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura arquivo ou diretorio especifico de um snapshot",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    parser.add_argument(
        "--path",
        required=True,
        help="Caminho do arquivo ou diretorio a restaurar",
    )
    return parser.parse_args()


def run_restore_file(snapshot_id: str, include_path: str) -> None:
    """Restaura arquivo ou diretorio especifico do snapshot.
    
    Utiliza o ResticClient para executar a restauracao com retry automatico e tratamento de erros.
    
    Parameters
    ----------
    snapshot_id : str
        ID do snapshot a ser restaurado ou "latest" para o mais recente
    include_path : str
        Caminho do arquivo ou diretorio a ser restaurado
    """
    credential_source = get_credential_source()
    with ResticScript("restore_file", credential_source=credential_source) as ctx:
        base_restore_target = (
            ctx.config.restore_target_dir
            if ctx.config and ctx.config.restore_target_dir
            else "C:\\Restore"
        )
        ctx.log("=== Iniciando restauracao de arquivo com Restic ===")
        
        try:
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3, credential_source=credential_source)
            
            # Obter informacoes do snapshot
            ctx.log(f"Buscando informacoes do snapshot '{snapshot_id}'...")
            snapshot_data = client.get_snapshot_info(snapshot_id)
            
            # Criar estrutura completa de pastas baseada na data/hora do snapshot
            # Formato: C:\Restore\2025-08-19-100320\C\Users\Administrator\Documents\Docker
            restore_target = create_full_restore_structure(
                base_restore_target,
                snapshot_data,
                include_path
            )
            
            # Formatar e exibir informacoes
            info = format_restore_info(snapshot_data, restore_target, include_path)
            
            ctx.log(f"Snapshot ID: {info['snapshot_id']}")
            ctx.log(f"Data do Snapshot: {info['snapshot_date']}")
            ctx.log(f"Hostname: {info['hostname']}")
            ctx.log(f"Arquivo/diretorio a restaurar: {include_path}")
            ctx.log(f"Destino da restauracao: {restore_target}")
            
            # Mostrar exemplo da estrutura criada
            timestamp_part = info['snapshot_date'].replace(' ', '-').replace(':', '')
            normalized_path = include_path.replace(':', '')
            if normalized_path.startswith(('\\', '/')):
                normalized_path = normalized_path[1:]
            example_structure = f"{base_restore_target}\\{timestamp_part}\\{normalized_path}"
            ctx.log(f"Estrutura criada: {example_structure}")
            
            # Executar restauracao do arquivo especifico
            success = client.restore_snapshot(
                target_dir=restore_target,
                snapshot_id=snapshot_id,
                include_paths=[include_path]
            )
            
            if success:
                ctx.log("✅ Arquivo ou diretorio restaurado com sucesso.")
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
    run_restore_file(args.id, args.path)

