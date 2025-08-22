import logging
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def run_backup() -> None:
    """Executa o backup baseado na configuracao carregada pelo ``ResticScript``."""
    with ResticScript("backup") as ctx:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

        config = ctx.config
        if not config or not config.backup_source_dirs:
            ctx.log("[FATAL] Variaveis obrigatorias ausentes na configuracao")
            sys.exit(1)

        ctx.log("=== Iniciando backup com Restic ===")

        client = ResticClient(
            max_attempts=3,
            repository=ctx.repository,
            env=ctx.env,
            provider=ctx.provider,
            credential_source=ctx.credential_source,
        )

        try:
            ctx.log("🔍 Verificando acesso ao repositorio...")
            if not client.check_repository_access():
                ctx.log("Nao foi possivel acessar o repositorio. Abortando.")
                return
            ctx.log("✅ Repositorio acessivel.")

            ctx.log(f"Executando backup de: {', '.join(config.backup_source_dirs)}")
            snapshot_id = client.backup(
                paths=config.backup_source_dirs,
                excludes=config.restic_excludes,
                tags=config.restic_tags,
            )
            ctx.log(f"Backup concluido com sucesso. ID do snapshot: {snapshot_id}")

            if config.retention_enabled:
                ctx.log("Aplicando politica de retencao...")
                client.apply_retention_policy(
                    keep_daily=config.keep_daily,
                    keep_weekly=config.keep_weekly,
                    keep_monthly=config.keep_monthly,
                    prune=True,
                )
                ctx.log("Politica de retencao aplicada.")
            else:
                ctx.log("Retencao desativada via configuracao.")

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[FATAL] Erro inesperado: {exc}")
            sys.exit(1)

        ctx.log("=== Fim do backup ===")


if __name__ == "__main__":
    run_backup()

