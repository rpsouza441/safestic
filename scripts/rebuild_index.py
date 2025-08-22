#!/usr/bin/env python3
"""Reconstrói o indice do repositorio Restic."""

from __future__ import annotations

import sys

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
    load_env_and_get_credential_source,
)


def main() -> int:
    read_all_packs = "--read-all-packs" in sys.argv or "--full" in sys.argv
    credential_source = load_env_and_get_credential_source()

    with ResticScript("rebuild_index", credential_source=credential_source) as ctx:
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source,
            )

            ctx.log("Verificando acesso ao repositorio...")
            if not client.check_repository():
                ctx.log("Erro ao acessar repositorio", level="ERROR")
                return 1

            ctx.log("Reconstruindo indice do repositorio...")
            if not client.rebuild_index(read_all_packs=read_all_packs):
                ctx.log("Falha ao reconstruir indice", level="ERROR")
                return 1

            ctx.log("Verificando indice reconstruido...")
            if not client.check_repository(read_data_subset="5%"):
                ctx.log(
                    "Problemas detectados durante verificacao final",
                    level="WARNING",
                )
                return 1

            ctx.log("Reconstrucao do indice concluida com sucesso.")
            return 0

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}", level="ERROR")
            return 1


if __name__ == "__main__":
    sys.exit(main())
