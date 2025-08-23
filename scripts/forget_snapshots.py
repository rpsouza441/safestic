#!/usr/bin/env python3
"""Aplica politica de retencao para esquecer snapshots antigos."""

from __future__ import annotations

import os
import sys

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
)
from services.env import get_credential_source


def main() -> int:
    credential_source = get_credential_source()

    with ResticScript("forget_snapshots", credential_source=credential_source) as ctx:
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source,
            )

            if os.getenv("RETENTION_ENABLED", "true").lower() != "true":
                ctx.log("Retencao desabilitada. Nenhum snapshot sera esquecido.")
                return 0

            keep_hourly = int(os.getenv("KEEP_HOURLY", "24"))
            keep_daily = int(os.getenv("KEEP_DAILY", "7"))
            keep_weekly = int(os.getenv("KEEP_WEEKLY", "4"))
            keep_monthly = int(os.getenv("KEEP_MONTHLY", "12"))
            tags = [t.strip() for t in os.getenv("RESTIC_TAGS", "").split(",") if t.strip()]

            ctx.log(
                "Aplicando politica de retencao: h=%s, d=%s, w=%s, m=%s", 
                keep_hourly,
                keep_daily,
                keep_weekly,
                keep_monthly,
            )

            if client.forget_snapshots(
                keep_hourly=keep_hourly,
                keep_daily=keep_daily,
                keep_weekly=keep_weekly,
                keep_monthly=keep_monthly,
                tags=tags,
            ):
                ctx.log("Snapshots esquecidos com sucesso.")
                return 0

            ctx.log("Falha ao aplicar politica de retencao", level="ERROR")
            return 1

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}", level="ERROR")
            return 1


if __name__ == "__main__":
    sys.exit(main())
