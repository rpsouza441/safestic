from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class ResticError(Exception):
    """Erro base para operacoes com o Restic."""

    message: str
    command: Sequence[str]
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover - simples
        return f"{self.message} (codigo: {self.returncode})"


class ResticNetworkError(ResticError):
    """Erro de rede ao acessar o repositorio Restic."""


class ResticRepositoryError(ResticError):
    """Erro relacionado ao repositorio Restic."""


class ResticAuthenticationError(ResticError):
    """Erro de autenticacao no Restic."""


class ResticPermissionError(ResticError):
    """Erro de permissao ao acessar recursos do Restic."""


class ResticCommandError(ResticError):
    """Erro generico na execucao de comandos Restic."""


def redact_secrets(text: str) -> str:
    """Redige senhas e chaves sensiveis de uma string."""
    patterns = [
        (r"(RESTIC_PASSWORD=)[^\s,]+", r"\1REDACTED"),
        (r"(AWS_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(AZURE_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(GOOGLE_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(-p|--password) [^\s]+", r"\1 REDACTED"),
        (r"(-p|--password-file) [^\s]+", r"\1 REDACTED"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def build_command(repository: Optional[str], *args: str) -> List[str]:
    """Monta comando para execucao do Restic."""
    cmd = ["restic"]
    if repository:
        cmd.extend(["-r", repository])
    cmd.extend(args)
    return cmd


def handle_command_error(cmd: Sequence[str], result: subprocess.CompletedProcess[str]) -> None:
    """Analisa saida de erro de um comando Restic e levanta excecao adequada."""
    stderr = result.stderr or ""
    stdout = result.stdout or ""
    lowered = f"{stderr}\n{stdout}".lower()

    if any(msg in lowered for msg in ["network", "connection", "timeout", "dial tcp"]):
        raise ResticNetworkError("Erro de rede ao acessar o repositorio", cmd, result.returncode, stdout, stderr)
    if any(msg in lowered for msg in ["repository not found", "invalid repository", "corrupted"]):
        raise ResticRepositoryError("Erro no repositorio Restic", cmd, result.returncode, stdout, stderr)
    if any(msg in lowered for msg in ["authentication", "access denied", "wrong password"]):
        raise ResticAuthenticationError("Erro de autenticacao", cmd, result.returncode, stdout, stderr)
    if any(msg in lowered for msg in ["permission", "access is denied", "not permitted"]):
        raise ResticPermissionError("Erro de permissao", cmd, result.returncode, stdout, stderr)
    raise ResticCommandError(
        f"Comando Restic falhou com codigo {result.returncode}",
        cmd,
        result.returncode,
        stdout,
        stderr,
    )
