import os
import sys

from services.script import ResticScript


def build_args(prefix, items):
    """Repete ``prefix`` para cada item não vazio."""
    return [arg for i in items for arg in (prefix, i.strip()) if i.strip()]


def run_backup():
    with ResticScript("backup") as ctx:
        source_dirs = os.getenv("BACKUP_SOURCE_DIRS", "").split(",")
        excludes = os.getenv("RESTIC_EXCLUDES", "").split(",")
        tags = os.getenv("RESTIC_TAGS", "").split(",")

        retention_enabled = os.getenv("RETENTION_ENABLED", "true").lower() == "true"
        keep_hourly = os.getenv("RETENTION_KEEP_HOURLY", "0")
        keep_daily = os.getenv("RETENTION_KEEP_DAILY", "7")
        keep_weekly = os.getenv("RETENTION_KEEP_WEEKLY", "4")
        keep_monthly = os.getenv("RETENTION_KEEP_MONTHLY", "6")

        if not any(source_dirs):
            print("[FATAL] Variáveis obrigatórias ausentes no .env")
            sys.exit(1)

        ctx.log("=== Iniciando backup com Restic ===")

        ctx.log("🔍 Verificando acesso ao repositório...")
        if not ctx.run_cmd(
            ["restic", "-r", ctx.repository, "snapshots"],
            success_msg="✅ Repositório acessível.",
            error_msg="Não foi possível acessar o repositório. Abortando.",
        )[0]:
            return

        cmd_backup = ["restic", "-r", ctx.repository, "backup"]
        cmd_backup += [d.strip() for d in source_dirs if d.strip()]
        cmd_backup += build_args("--exclude", excludes)
        cmd_backup += build_args("--tag", tags)

        ctx.log(f"Executando backup de: {', '.join(source_dirs)}")
        ctx.run_cmd(
            cmd_backup,
            success_msg="Backup concluído.",
            error_msg="Erro durante o backup.",
        )

        if retention_enabled:
            ctx.log("Aplicando política de retenção...")
            cmd_retention = [
                "restic",
                "-r",
                ctx.repository,
                "forget",
                "--keep-hourly",
                keep_hourly,
                "--keep-daily",
                keep_daily,
                "--keep-weekly",
                keep_weekly,
                "--keep-monthly",
                keep_monthly,
                "--prune",
            ]
            ctx.run_cmd(
                cmd_retention,
                success_msg="Política de retenção aplicada.",
                error_msg="Erro ao aplicar retenção.",
            )
        else:
            ctx.log("Retenção desativada via .env.")

        ctx.log("=== Fim do backup ===")


if __name__ == "__main__":
    try:
        run_backup()
    except Exception as e:  # pragma: no cover - runtime errors
        print(f"[FATAL] Erro inesperado: {e}")
        sys.exit(1)
