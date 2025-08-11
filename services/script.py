"""Shared context manager for CLI scripts.

This module exposes :class:`ResticScript` which centralises the boilerplate
needed by all command line utilities: loading the Restic environment
configuration, preparing a timestamped log file and providing helper methods
for logging and running external commands.
"""

from __future__ import annotations

import os
from typing import Sequence, TextIO

from .restic import load_restic_env
from .logger import create_log_file, log as _log, run_cmd as _run_cmd


class ResticScript:
    """Context manager used by CLI scripts.

    Parameters
    ----------
    log_prefix: str
        Identifier used for the generated log file name.
    log_dir: str | None
        Directory where log files will be stored. Defaults to the ``LOG_DIR``
        environment variable or ``"logs"`` when unset.
    """

    def __init__(self, log_prefix: str, log_dir: str | None = None):
        self.log_prefix = log_prefix
        self.log_dir = log_dir or os.getenv("LOG_DIR", "logs")
        self.repository: str = ""
        self.env: dict[str, str] = {}
        self.provider: str = ""
        self.log_filename: str = ""
        self.log_file: TextIO | None = None

    def __enter__(self) -> "ResticScript":
        try:
            self.repository, self.env, self.provider = load_restic_env()
        except ValueError as exc:  # pragma: no cover - environment errors
            print(f"[FATAL] {exc}")
            raise SystemExit(1)

        try:
            self.log_filename = create_log_file(self.log_prefix, self.log_dir)
            self.log_file = open(self.log_filename, "w", encoding="utf-8")
        except Exception as exc:  # pragma: no cover - filesystem errors
            print(f"[FATAL] Falha ao preparar log: {exc}")
            raise SystemExit(1)

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.log_file is not None:
            self.log_file.close()

    # Convenience wrappers -------------------------------------------------
    def log(self, message: str) -> None:
        """Write ``message`` to the log file and stdout."""
        if self.log_file is None:  # pragma: no cover - defensive programming
            raise RuntimeError("ResticScript not initialised")
        _log(message, self.log_file)

    def run_cmd(
        self,
        cmd: Sequence[str],
        *,
        success_msg: str | None = None,
        error_msg: str | None = None,
    ):
        """Execute ``cmd`` forwarding output to the log file.

        Returns the tuple ``(success, CompletedProcess)`` from
        :func:`services.logger.run_cmd`.
        """
        if self.log_file is None:  # pragma: no cover - defensive programming
            raise RuntimeError("ResticScript not initialised")
        return _run_cmd(
            cmd,
            self.log_file,
            env=self.env,
            success_msg=success_msg,
            error_msg=error_msg,
        )
