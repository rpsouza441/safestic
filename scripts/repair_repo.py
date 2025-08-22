#!/usr/bin/env python3
"""Executa reparos no repositorio Restic."""

from __future__ import annotations

import sys

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
    load_env_and_get_credential_source,
)


def main() -> int:
    repair_type = "all"
    if "--snapshots" in sys.argv:
        repair_type = "snapshots"
    elif "--index" in sys.argv:
        repair_type = "index"
    elif "--packs" in sys.argv:
        repair_type = "packs"

    credential_source = load_env_and_get_credential_source()

    with ResticScript("repair_repo", credential_source=credential_source) as ctx:
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source,
            )

            ctx.log("Verificando integridade inicial do repositorio...")
            client.check_repository()

            success = True
            if repair_type in ("all", "snapshots"):
                success &= client.repair_snapshots()
            if repair_type in ("all", "index"):
                success &= client.repair_index()
            if repair_type in ("all", "packs"):
                success &= client.repair_packs()

            if not success:
                ctx.log("Falha durante o processo de reparo", level="ERROR")
                return 1

            ctx.log("Verificando repositorio apos reparo...")
            client.check_repository(read_data_subset="10%")
            ctx.log("Reparo concluido.")
            return 0

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}", level="ERROR")
            return 1


if __name__ == "__main__":
    sys.exit(main())
