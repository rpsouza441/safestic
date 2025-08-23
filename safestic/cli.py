"""Command line interface for Safestic."""
from __future__ import annotations

import argparse
from pathlib import Path

from services.restic_client import (
    ResticClient,
    ResticError,
)
from services.env import get_credential_source
from services.restic import load_restic_config
from services.script import ResticScript


def cmd_backup(args: argparse.Namespace) -> None:
    """Run backup using existing helper script."""
    from restic_backup import run_backup

    run_backup()


def cmd_list(args: argparse.Namespace) -> None:
    """List snapshots in repository."""
    from list_snapshots import list_snapshots

    list_snapshots()


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize repository if needed."""
    credential_source = get_credential_source()
    with ResticScript("init", credential_source=credential_source) as ctx:
        client = ResticClient(
            repository=ctx.repository,
            env=ctx.env,
            provider=ctx.provider,
            credential_source=credential_source,
        )
        try:
            client.check_repository_access()
            ctx.log("[OK] Repositorio ja existe e esta acessivel")
        except Exception:
            try:
                client.init_repository()
                ctx.log("[OK] Repositorio inicializado com sucesso")
            except ResticError as init_error:  # pragma: no cover - runtime failure
                ctx.log(f"[ERRO] Erro ao inicializar repositorio: {init_error}")
                raise SystemExit(1)


def cmd_dry_run(args: argparse.Namespace) -> None:
    """Display configured backup paths and check their existence."""
    credential_source = get_credential_source()
    config = load_restic_config(credential_source)
    print("Configuracao de backup:")
    print(f"Diretorios: {config.backup_source_dirs}")
    print(f"Exclusoes: {config.restic_excludes}")
    print(f"Tags: {config.restic_tags}")
    for dir_path in config.backup_source_dirs:
        status = "OK" if Path(dir_path).exists() else "NAO ENCONTRADO"
        print(f"{dir_path} - {status}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safestic")
    sub = parser.add_subparsers(dest="command", required=True)

    backup_p = sub.add_parser("backup", help="Executa backup completo")
    backup_p.set_defaults(func=cmd_backup)

    list_p = sub.add_parser("list", help="Lista snapshots")
    list_p.set_defaults(func=cmd_list)

    init_p = sub.add_parser("init", help="Inicializa repositorio")
    init_p.set_defaults(func=cmd_init)

    dry_p = sub.add_parser("dry-run", help="Simula backup sem executar")
    dry_p.set_defaults(func=cmd_dry_run)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
