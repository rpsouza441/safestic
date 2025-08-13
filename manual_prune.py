import logging
import os
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def main() -> None:
    """Executa a limpeza manual de snapshots antigos.
    
    Utiliza o ResticClient para aplicar políticas de retenção com retry automático e tratamento de erros.
    """
    with ResticScript("manual_prune") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log("=== Iniciando limpeza manual de snapshots com Restic ===")

        try:
            # Obter configurações de retenção
            keep_daily = int(os.getenv("RETENTION_KEEP_DAILY", "7"))
            keep_weekly = int(os.getenv("RETENTION_KEEP_WEEKLY", "4"))
            keep_monthly = int(os.getenv("RETENTION_KEEP_MONTHLY", "6"))

            ctx.log(f"Aplicando política de retenção:")
            ctx.log(f"- Manter backups diários: {keep_daily}")
            ctx.log(f"- Manter backups semanais: {keep_weekly}")
            ctx.log(f"- Manter backups mensais: {keep_monthly}")

            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Aplicar política de retenção
            success = client.apply_retention_policy(
                keep_daily=keep_daily,
                keep_weekly=keep_weekly,
                keep_monthly=keep_monthly
            )
            
            if success:
                ctx.log("✅ Limpeza de snapshots concluída com sucesso.")
            else:
                ctx.log("Erro durante a limpeza de snapshots")
                sys.exit(1)

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)
        finally:
            ctx.log("=== Fim do processo de limpeza de snapshots ===")


if __name__ == "__main__":
    main()
