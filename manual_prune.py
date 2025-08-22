import logging
import os
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError, load_env_and_get_credential_source


def main() -> None:
    """Executa a limpeza manual de snapshots antigos.
    
    Utiliza o ResticClient para aplicar politicas de retencao com retry automatico e tratamento de erros.
    """
    credential_source = load_env_and_get_credential_source()
    with ResticScript("manual_prune", credential_source=credential_source) as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log("=== Iniciando limpeza manual de snapshots com Restic ===")

        try:
            # Obter configuracoes de retencao
            keep_daily = int(os.getenv("RETENTION_KEEP_DAILY", "7"))
            keep_weekly = int(os.getenv("RETENTION_KEEP_WEEKLY", "4"))
            keep_monthly = int(os.getenv("RETENTION_KEEP_MONTHLY", "6"))

            ctx.log(f"Aplicando politica de retencao:")
            ctx.log(f"- Manter backups diarios: {keep_daily}")
            ctx.log(f"- Manter backups semanais: {keep_weekly}")
            ctx.log(f"- Manter backups mensais: {keep_monthly}")

            # Criar cliente Restic com retry usando o ambiente já carregado
            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source
            )
            
            # Aplicar politica de retencao
            success = client.apply_retention_policy(
                keep_daily=keep_daily,
                keep_weekly=keep_weekly,
                keep_monthly=keep_monthly
            )
            
            if success:
                ctx.log("✅ Limpeza de snapshots concluida com sucesso.")
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

