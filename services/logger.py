"""Utility helpers for timestamped logging in scripts."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path
from typing import TextIO, List, Optional


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
    cmd: List[str],
    log_file: TextIO,
    success_msg: str,
    error_msg: str,
    env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """Execute ``cmd`` capturing stdout/stderr and log details."""

    log(f"Comando: {' '.join(cmd)}", log_file)
    result = subprocess.run(cmd, env=env, text=True, capture_output=True)

    if result.stdout:
        log_file.write(result.stdout)
    if result.stderr:
        log_file.write(result.stderr)

    if result.returncode == 0:
        log(success_msg, log_file)
    else:
        log(f"{error_msg} (código {result.returncode})", log_file)

    return result
