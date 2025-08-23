#!/usr/bin/env python3
"""Monta o repositorio Restic como sistema de arquivos."""

from __future__ import annotations

import os
import sys
import signal
from pathlib import Path

from services.script import ResticScript
from services.restic_client import (
    ResticClient,
    ResticError,
)
from services.env import get_credential_source


def check_fuse_support() -> tuple[bool, str | None]:
    """Verifica se FUSE/WinFsp esta disponivel."""
    system = os.name
    if system == "posix":
        try:
            import subprocess

            subprocess.run(["fusermount", "--version"], capture_output=True, check=True)
            return True, "./mount"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("FUSE nao encontrado. Instale o pacote apropriado para seu sistema.")
            return False, None
    elif system == "nt":
        winfsp_paths = [
            r"C:\\Program Files\\WinFsp\\bin\\launchctl-x64.exe",
            r"C:\\Program Files (x86)\\WinFsp\\bin\\launchctl-x86.exe",
        ]
        for path in winfsp_paths:
            if Path(path).exists():
                return True, ".\\mount"
        print("WinFsp nao encontrado. Instale a partir de https://winfsp.dev/rel/")
        return False, None
    else:
        print(f"Sistema nao suportado: {system}")
        return False, None


def create_mount_point(mount_path: str) -> bool:
    try:
        Path(mount_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as exc:  # pragma: no cover - filesystem errors
        print(f"Erro ao criar ponto de montagem: {exc}")
        return False


def main() -> int:
    credential_source = get_credential_source()

    with ResticScript("mount_repo", credential_source=credential_source) as ctx:
        try:
            client = ResticClient(
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source,
            )

            fuse_ok, default_mount = check_fuse_support()
            if not fuse_ok:
                return 1

            mount_path = os.getenv("MOUNT_POINT", default_mount or "./mount")
            if not create_mount_point(mount_path):
                return 1

            process = client.mount_repository(mount_path)

            def signal_handler(sig, frame):
                print("\nDesmontando repositorio...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except Exception:
                    process.kill()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)

            print(f"Repositorio montado em {Path(mount_path).resolve()}")
            print("Pressione Ctrl+C para desmontar")

            for line in process.stdout:  # type: ignore[attr-defined]
                if line.strip():
                    print(line.strip())
            process.wait()
            return 0 if process.returncode == 0 else 1

        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}", level="ERROR")
            return 1


if __name__ == "__main__":
    sys.exit(main())
