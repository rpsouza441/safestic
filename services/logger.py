"""Utility helpers for timestamped logging in scripts.

This module centralises logging-related helpers so that every script in the
project can easily create timestamped log files and record detailed
information about the commands being executed.  The goal is to make debugging
easier by exposing the full stdout/stderr of external processes and any
exceptions raised during execution.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path
from typing import TextIO, Sequence


def create_log_file(prefix: str, log_dir: str) -> str:
    """Return a new log file path inside ``log_dir`` using ``prefix``.

    Parameters
    ----------
    prefix: str
        Short identifier used in the log file name, e.g. ``"backup"``.
    log_dir: str
        Directory where the log file will be created.

    Returns
    -------
    str
        Full path to the newly created log file. The directory is created
        automatically if it does not exist.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    return now.strftime(f"{log_dir}/{prefix}_%Y%m%d_%H%M%S.log")


def log(msg: str, log_file: TextIO) -> None:
    """Print ``msg`` and append it to ``log_file`` with a timestamp."""
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")


def run_cmd(
    cmd: Sequence[str],
    log_file: TextIO,
    env: dict[str, str] | None = None,
    success_msg: str | None = None,
    error_msg: str | None = None,
) -> tuple[bool, subprocess.CompletedProcess[str] | None]:
    """Execute ``cmd`` capturing stdout and stderr.

    All output is written both to ``log_file`` and to the console so the user
    can follow the progress in real time.  The function returns a tuple where
    the first element indicates success and the second is the underlying
    ``CompletedProcess`` instance (``None`` when the command could not be
    spawned).
    """

    log(f"Comando: {' '.join(cmd)}", log_file)
    try:
        result = subprocess.run(
            cmd,
            env=env,
            text=True,
            capture_output=True,
        )
    except Exception as exc:  # pragma: no cover - runtime issues
        log(
            f"{error_msg or 'Falha ao executar comando'}: {exc}",
            log_file,
        )
        return False, None

    if result.stdout:
        print(result.stdout, end="")
        log_file.write(result.stdout)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
        log_file.write(result.stderr)

    if result.returncode == 0:
        if success_msg:
            log(success_msg, log_file)
        return True, result

    log(
        f"{error_msg or 'Comando falhou'} (código {result.returncode})",
        log_file,
    )
    return False, result

