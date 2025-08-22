#!/usr/bin/env python3
"""Verifica se o comando ``restic mount`` esta disponivel."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
    load_env_and_get_credential_source,
)


def check_winfsp() -> bool:
    """Verifica se WinFsp esta instalado (Windows)."""
    winfsp_paths = [
        r"C:\\Program Files\\WinFsp\\bin\\launchctl-x64.exe",
        r"C:\\Program Files (x86)\\WinFsp\\bin\\launchctl-x64.exe",
    ]
    for path in winfsp_paths:
        if Path(path).exists():
            print(f"✅ WinFsp encontrado: {path}")
            return True
    print("❌ WinFsp nao encontrado")
    print("💡 Instale WinFsp de: https://winfsp.dev/rel/")
    return False


def main() -> int:
    credential_source = load_env_and_get_credential_source()

    with ResticScript("check_mount_support", credential_source=credential_source) as ctx:
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source,
            )

            restic_ok = client.supports_mount()
            winfsp_ok = True
            if os.name == "nt":
                winfsp_ok = check_winfsp()
            else:
                print("ℹ️  Verificacao de WinFsp ignorada (nao Windows)")

            print("\n" + "=" * 50)
            if winfsp_ok and restic_ok:
                print("🎉 SUCESSO: Comando 'restic mount' deve funcionar!")
                return 0
            print("⚠️  AVISO: Comando 'restic mount' pode nao funcionar")
            return 1

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}", level="ERROR")
            return 1


if __name__ == "__main__":
    sys.exit(main())
