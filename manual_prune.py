import logging
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def main() -> None:
    """Executa a limpeza manual de snapshots antigos."""
    with ResticScript("manual_prune") as ctx:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

        config = ctx.config
        if not config:
            ctx.log("[FATAL] Configuracao do Restic nao carregada")
            sys.exit(1)

        ctx.log("=== Iniciando limpeza manual de snapshots com Restic ===")

        try:
            ctx.log("Aplicando politica de retencao:")
            ctx.log(f"- Manter backups diarios: {config.keep_daily}")
            ctx.log(f"- Manter backups semanais: {config.keep_weekly}")
            ctx.log(f"- Manter backups mensais: {config.keep_monthly}")

            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=ctx.credential_source,
            )

            success = client.apply_retention_policy(
                keep_daily=config.keep_daily,
                keep_weekly=config.keep_weekly,
                keep_monthly=config.keep_monthly,
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

