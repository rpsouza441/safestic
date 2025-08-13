import argparse
import datetime
import logging
import os
from pathlib import Path

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura um snapshot inteiro para o diretório alvo",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot a restaurar")
    return parser.parse_args()


def run_restore_snapshot(snapshot_id: str) -> None:
    """Restaura um snapshot inteiro para o diretório alvo.
    
    Utiliza o ResticClient para executar a restauração com retry automático e tratamento de erros.
    
    Parameters
    ----------
    snapshot_id : str
        ID do snapshot a ser restaurado ou "latest" para o mais recente
    """
    with ResticScript("restore_snapshot") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        restore_target = os.getenv("RESTORE_TARGET_DIR", "restore")
        ctx.log("=== Iniciando restauração de snapshot com Restic ===")

        try:
            # Criar diretório de destino
            Path(restore_target).mkdir(parents=True, exist_ok=True)
            
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Obter informações do snapshot
            ctx.log(f"Buscando informações do snapshot '{snapshot_id}'...")
            snapshot_data = client.get_snapshot_info(snapshot_id)
            
            # Formatar data do snapshot
            snapshot_time = datetime.datetime.fromisoformat(
                snapshot_data["time"].replace("Z", "+00:00")
            )
            
            # Exibir informações
            ctx.log(f"Snapshot ID: {snapshot_data['short_id']}")
            ctx.log(
                f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            ctx.log(f"Destino da restauração: {restore_target}")
            print("\nIniciando processo de restauração... O progresso será exibido abaixo.")

            # Executar restauração
            success = client.restore_snapshot(
                target_dir=restore_target,
                snapshot_id=snapshot_id,
            )
            
            if success:
                ctx.log("✅ Restauração de snapshot concluída com sucesso.")
            else:
                ctx.log("Erro durante a restauração")

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
        finally:
            ctx.log("=== Fim do processo de restauração ===")


if __name__ == "__main__":
    args = parse_args()
    run_restore_snapshot(args.id)
