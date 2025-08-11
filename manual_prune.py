import os
import sys

from services.script import ResticScript


def main() -> None:
    with ResticScript("manual_prune") as ctx:
        keep_daily = os.getenv("RETENTION_KEEP_DAILY", "7")
        keep_weekly = os.getenv("RETENTION_KEEP_WEEKLY", "4")
        keep_monthly = os.getenv("RETENTION_KEEP_MONTHLY", "6")

        ctx.log("Aplicando política de retenção manual:")
        ctx.log(f"  Diário:   {keep_daily}")
        ctx.log(f"  Semanal:  {keep_weekly}")
        ctx.log(f"  Mensal:   {keep_monthly}")

        cmd = [
            "restic",
            "-r",
            ctx.repository,
            "forget",
            "--keep-daily",
            keep_daily,
            "--keep-weekly",
            keep_weekly,
            "--keep-monthly",
            keep_monthly,
            "--prune",
        ]

        success, _ = ctx.run_cmd(
            cmd,
            success_msg="Política de retenção aplicada com sucesso.",
            error_msg="Erro ao aplicar política de retenção.",
        )

        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
