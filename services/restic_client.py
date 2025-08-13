"""Wrapper centralizado para operações do Restic com retry e tratamento de erros.

Este módulo fornece a classe ResticClient que encapsula todas as operações comuns
do Restic (backup, restore, listagem, etc.) com suporte a retry automático,
backoff exponencial e tratamento estruturado de erros.
"""

from __future__ import annotations

import json
import logging
import random
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union, cast

from .restic import load_restic_env

# Tipo genérico para o resultado de funções com retry
T = TypeVar("T")


@dataclass
class ResticError(Exception):
    """Exceção base para erros relacionados ao Restic."""
    message: str
    command: List[str]
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.message} (código: {self.returncode})"


class ResticNetworkError(ResticError):
    """Erro de rede ao acessar o repositório Restic."""
    pass


class ResticRepositoryError(ResticError):
    """Erro relacionado ao repositório Restic (não encontrado, corrompido, etc.)."""
    pass


class ResticAuthenticationError(ResticError):
    """Erro de autenticação (senha incorreta, credenciais inválidas, etc.)."""
    pass


class ResticPermissionError(ResticError):
    """Erro de permissão ao acessar arquivos ou o repositório."""
    pass


class ResticCommandError(ResticError):
    """Erro genérico na execução de um comando Restic."""
    pass


def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator para adicionar retry com backoff exponencial a uma função.

    Parameters
    ----------
    max_attempts : int, optional
        Número máximo de tentativas, por padrão 3
    initial_backoff : float, optional
        Tempo inicial de espera em segundos, por padrão 1.0
    max_backoff : float, optional
        Tempo máximo de espera em segundos, por padrão 30.0
    backoff_factor : float, optional
        Fator multiplicativo para backoff exponencial, por padrão 2.0
    jitter : float, optional
        Fator de aleatoriedade para evitar thundering herd, por padrão 0.1

    Returns
    -------
    Callable
        Função decorada com retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            attempt = 1

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except (ResticNetworkError, ResticRepositoryError) as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        break

                    # Calcular tempo de espera com backoff exponencial e jitter
                    backoff = min(
                        max_backoff,
                        initial_backoff * (backoff_factor ** (attempt - 1)),
                    )
                    # Adicionar jitter (variação aleatória)
                    backoff = backoff * (1 + random.uniform(-jitter, jitter))

                    logging.warning(
                        "Tentativa %d/%d falhou: %s. Tentando novamente em %.2f segundos.",
                        attempt,
                        max_attempts,
                        exc,
                        backoff,
                    )

                    time.sleep(backoff)
                    attempt += 1
                except Exception as exc:
                    # Outros tipos de exceção não são retentados
                    raise exc

            # Se chegamos aqui, todas as tentativas falharam
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


def redact_secrets(text: str) -> str:
    """Redaciona senhas e chaves de acesso em strings de texto.

    Parameters
    ----------
    text : str
        Texto a ser redacionado

    Returns
    -------
    str
        Texto com senhas e chaves substituídas por ***
    """
    # Padrões para redação de segredos
    patterns = [
        # Senha do Restic
        (r"(RESTIC_PASSWORD=)[^\s,]+", r"\1***"),
        # Chaves AWS
        (r"(AWS_[^=]+=)[^\s,]+", r"\1***"),
        # Chaves Azure
        (r"(AZURE_[^=]+=)[^\s,]+", r"\1***"),
        # Chaves GCP
        (r"(GOOGLE_[^=]+=)[^\s,]+", r"\1***"),
        # Argumentos de senha na linha de comando
        (r"(-p|--password) [^\s]+", r"\1 ***"),
        # Argumentos de senha em arquivos
        (r"(-p|--password-file) [^\s]+", r"\1 ***"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    return result


class ResticClient:
    """Cliente para interação com o Restic com suporte a retry e tratamento de erros.

    Esta classe encapsula todas as operações comuns do Restic e fornece uma
    interface Python amigável com tratamento adequado de erros, retry automático
    para falhas transitórias e logging estruturado.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        max_attempts: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 30.0,
    ):
        """Inicializa o cliente Restic.

        Parameters
        ----------
        log_file : Optional[str], optional
            Caminho para o arquivo de log, por padrão None
        max_attempts : int, optional
            Número máximo de tentativas para operações com retry, por padrão 3
        initial_backoff : float, optional
            Tempo inicial de espera entre tentativas em segundos, por padrão 1.0
        max_backoff : float, optional
            Tempo máximo de espera entre tentativas em segundos, por padrão 30.0
        """
        self.repository, self.env, self.provider = load_restic_env()
        self.log_file = log_file
        self.logger = logging.getLogger("restic_client")

        # Configurações de retry
        self.max_attempts = max_attempts
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

    def _run_command(
        self,
        cmd: Sequence[str],
        capture_json: bool = False,
        check: bool = True,
    ) -> Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]:
        """Executa um comando do Restic com tratamento de erros.

        Parameters
        ----------
        cmd : Sequence[str]
            Comando a ser executado
        capture_json : bool, optional
            Se True, tenta fazer parse do output como JSON, por padrão False
        check : bool, optional
            Se True, verifica o código de retorno e levanta exceção em caso de erro,
            por padrão True

        Returns
        -------
        Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]
            Tupla contendo (sucesso, resultado do processo, dados JSON se aplicável)

        Raises
        ------
        ResticNetworkError
            Erro de rede ao acessar o repositório
        ResticRepositoryError
            Erro relacionado ao repositório
        ResticAuthenticationError
            Erro de autenticação
        ResticPermissionError
            Erro de permissão
        ResticCommandError
            Outro erro na execução do comando
        """
        redacted_cmd = [redact_secrets(arg) for arg in cmd]
        start_time = time.time()

        self.logger.info("Executando comando: %s", " ".join(redacted_cmd))

        try:
            result = subprocess.run(
                cmd,
                env=self.env,
                text=True,
                capture_output=True,
            )

            elapsed = time.time() - start_time
            self.logger.debug(
                "Comando concluído em %.2f segundos (código: %d)",
                elapsed,
                result.returncode,
            )

            # Processar saída e erro
            if result.stdout:
                self.logger.debug("Saída: %s", redact_secrets(result.stdout))

            if result.stderr:
                self.logger.debug("Erro: %s", redact_secrets(result.stderr))

            # Verificar erros
            if check and result.returncode != 0:
                self._handle_command_error(cmd, result)

            # Processar JSON se solicitado
            json_data = None
            if capture_json and result.stdout:
                try:
                    json_data = json.loads(result.stdout)
                except json.JSONDecodeError as exc:
                    self.logger.error("Erro ao decodificar JSON: %s", exc)
                    return False, result, None

            return result.returncode == 0, result, json_data

        except subprocess.SubprocessError as exc:
            self.logger.error("Erro ao executar comando: %s", exc)
            raise ResticCommandError(
                message=f"Erro ao executar comando: {exc}",
                command=cmd,
            )

    def _handle_command_error(
        self, cmd: Sequence[str], result: subprocess.CompletedProcess[str]
    ) -> None:
        """Analisa o erro de um comando e levanta a exceção apropriada.

        Parameters
        ----------
        cmd : Sequence[str]
            Comando executado
        result : subprocess.CompletedProcess[str]
            Resultado da execução do comando

        Raises
        ------
        ResticNetworkError
            Erro de rede
        ResticRepositoryError
            Erro de repositório
        ResticAuthenticationError
            Erro de autenticação
        ResticPermissionError
            Erro de permissão
        ResticCommandError
            Outro erro de comando
        """
        stderr = result.stderr or ""
        stdout = result.stdout or ""

        # Analisar o erro para determinar o tipo
        if any(
            msg in stderr.lower() or msg in stdout.lower()
            for msg in ["network", "connection", "timeout", "dial tcp"]
        ):
            raise ResticNetworkError(
                message="Erro de rede ao acessar o repositório",
                command=cmd,
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        elif any(
            msg in stderr.lower() or msg in stdout.lower()
            for msg in ["repository not found", "invalid repository", "corrupted"]
        ):
            raise ResticRepositoryError(
                message="Erro no repositório Restic",
                command=cmd,
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        elif any(
            msg in stderr.lower() or msg in stdout.lower()
            for msg in ["authentication", "access denied", "wrong password"]
        ):
            raise ResticAuthenticationError(
                message="Erro de autenticação",
                command=cmd,
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        elif any(
            msg in stderr.lower() or msg in stdout.lower()
            for msg in ["permission", "access is denied", "not permitted"]
        ):
            raise ResticPermissionError(
                message="Erro de permissão",
                command=cmd,
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        else:
            raise ResticCommandError(
                message=f"Comando Restic falhou com código {result.returncode}",
                command=cmd,
                returncode=result.returncode,
                stdout=stdout,
                stderr=stderr,
            )

    @with_retry()
    def check_repository_access(self) -> bool:
        """Verifica se o repositório Restic está acessível.

        Returns
        -------
        bool
            True se o repositório está acessível, False caso contrário

        Raises
        ------
        ResticError
            Se ocorrer um erro ao acessar o repositório
        """
        self.logger.info("Verificando acesso ao repositório: %s", self.repository)
        success, _, _ = self._run_command(
            ["restic", "-r", self.repository, "snapshots"],
            check=False,
        )
        return success

    def init_repository(self) -> bool:
        """Inicializa um novo repositório Restic se não existir.

        Returns
        -------
        bool
            True se o repositório foi inicializado com sucesso, False caso contrário
        """
        self.logger.info("Inicializando repositório: %s", self.repository)
        success, _, _ = self._run_command(
            ["restic", "-r", self.repository, "init"],
            check=False,
        )
        return success

    @with_retry()
    def backup(
        self,
        paths: List[str],
        excludes: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Executa um backup com Restic.

        Parameters
        ----------
        paths : List[str]
            Lista de caminhos a serem incluídos no backup
        excludes : Optional[List[str]], optional
            Lista de padrões a serem excluídos, por padrão None
        tags : Optional[List[str]], optional
            Lista de tags a serem aplicadas ao snapshot, por padrão None

        Returns
        -------
        str
            ID do snapshot criado

        Raises
        ------
        ResticError
            Se ocorrer um erro durante o backup
        """
        if not paths:
            raise ValueError("Pelo menos um caminho deve ser especificado para backup")

        cmd = ["restic", "-r", self.repository, "backup"]
        cmd.extend(paths)

        # Adicionar exclusões
        if excludes:
            for exclude in excludes:
                if exclude.strip():
                    cmd.extend(["--exclude", exclude.strip()])

        # Adicionar tags
        if tags:
            for tag in tags:
                if tag.strip():
                    cmd.extend(["--tag", tag.strip()])

        self.logger.info(
            "Iniciando backup de %d caminhos com %d exclusões e %d tags",
            len(paths),
            len(excludes or []),
            len(tags or []),
        )

        success, result, _ = self._run_command(cmd)

        if success and result and result.stdout:
            # Extrair ID do snapshot da saída
            match = re.search(r"snapshot ([a-f0-9]+) saved", result.stdout)
            if match:
                snapshot_id = match.group(1)
                self.logger.info("Backup concluído com sucesso, ID: %s", snapshot_id)
                return snapshot_id

        # Se chegamos aqui, não conseguimos extrair o ID do snapshot
        raise ResticCommandError(
            message="Não foi possível extrair o ID do snapshot da saída do comando",
            command=cmd,
            returncode=result.returncode if result else None,
            stdout=result.stdout if result else None,
            stderr=result.stderr if result else None,
        )

    @with_retry()
    def apply_retention_policy(
        self,
        keep_hourly: int = 0,
        keep_daily: int = 7,
        keep_weekly: int = 4,
        keep_monthly: int = 6,
        prune: bool = True,
    ) -> bool:
        """Aplica política de retenção aos snapshots.

        Parameters
        ----------
        keep_hourly : int, optional
            Número de snapshots horários a manter, por padrão 0
        keep_daily : int, optional
            Número de snapshots diários a manter, por padrão 7
        keep_weekly : int, optional
            Número de snapshots semanais a manter, por padrão 4
        keep_monthly : int, optional
            Número de snapshots mensais a manter, por padrão 6
        prune : bool, optional
            Se True, executa prune após forget, por padrão True

        Returns
        -------
        bool
            True se a política foi aplicada com sucesso

        Raises
        ------
        ResticError
            Se ocorrer um erro ao aplicar a política
        """
        cmd = [
            "restic",
            "-r",
            self.repository,
            "forget",
            "--keep-hourly",
            str(keep_hourly),
            "--keep-daily",
            str(keep_daily),
            "--keep-weekly",
            str(keep_weekly),
            "--keep-monthly",
            str(keep_monthly),
        ]

        if prune:
            cmd.append("--prune")

        self.logger.info(
            "Aplicando política de retenção (h:%d, d:%d, w:%d, m:%d, prune:%s)",
            keep_hourly,
            keep_daily,
            keep_weekly,
            keep_monthly,
            prune,
        )

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Lista todos os snapshots no repositório.

        Returns
        -------
        List[Dict[str, Any]]
            Lista de snapshots com suas informações

        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar os snapshots
        """
        self.logger.info("Listando snapshots do repositório")
        _, _, json_data = self._run_command(
            ["restic", "-r", self.repository, "snapshots", "--json"],
            capture_json=True,
        )

        if json_data is None:
            return []

        return cast(List[Dict[str, Any]], json_data)

    @with_retry()
    def get_snapshot_info(self, snapshot_id: str = "latest") -> Dict[str, Any]:
        """Obtém informações detalhadas sobre um snapshot específico.

        Parameters
        ----------
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrão "latest"

        Returns
        -------
        Dict[str, Any]
            Informações do snapshot

        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter as informações
        """
        self.logger.info("Obtendo informações do snapshot: %s", snapshot_id)
        _, _, json_data = self._run_command(
            ["restic", "-r", self.repository, "snapshots", snapshot_id, "--json"],
            capture_json=True,
        )

        if not json_data or not isinstance(json_data, list) or not json_data:
            raise ResticCommandError(
                message=f"Não foi possível obter informações do snapshot {snapshot_id}",
                command=["restic", "-r", self.repository, "snapshots", snapshot_id, "--json"],
            )

        return cast(Dict[str, Any], json_data[0])

    @with_retry()
    def list_snapshot_files(self, snapshot_id: str = "latest") -> List[str]:
        """Lista os arquivos contidos em um snapshot.

        Parameters
        ----------
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrão "latest"

        Returns
        -------
        List[str]
            Lista de caminhos de arquivos no snapshot

        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar os arquivos
        """
        self.logger.info("Listando arquivos do snapshot: %s", snapshot_id)
        success, result, _ = self._run_command(
            ["restic", "-r", self.repository, "ls", snapshot_id],
        )

        if success and result and result.stdout:
            # Processar a saída para extrair os caminhos dos arquivos
            files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return files

        return []

    @with_retry()
    def restore_snapshot(
        self, target_dir: str, snapshot_id: str = "latest", include_paths: Optional[List[str]] = None
    ) -> bool:
        """Restaura um snapshot completo ou arquivos específicos.

        Parameters
        ----------
        target_dir : str
            Diretório de destino para a restauração
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrão "latest"
        include_paths : Optional[List[str]], optional
            Lista de caminhos específicos a restaurar, por padrão None (restaura tudo)

        Returns
        -------
        bool
            True se a restauração foi bem-sucedida

        Raises
        ------
        ResticError
            Se ocorrer um erro durante a restauração
        """
        # Garantir que o diretório de destino existe
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        cmd = [
            "restic",
            "-r",
            self.repository,
            "restore",
            snapshot_id,
            "--target",
            target_dir,
        ]

        # Adicionar caminhos específicos se fornecidos
        if include_paths:
            for path in include_paths:
                cmd.extend(["--include", path])

        self.logger.info(
            "Restaurando snapshot %s para %s", snapshot_id, target_dir
        )

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def get_repository_stats(self, mode: str = "raw-data") -> Dict[str, Any]:
        """Obtém estatísticas do repositório.

        Parameters
        ----------
        mode : str, optional
            Modo de cálculo ("raw-data", "restore-size", "blobs-per-file"),
            por padrão "raw-data"

        Returns
        -------
        Dict[str, Any]
            Estatísticas do repositório

        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter as estatísticas
        """
        self.logger.info("Obtendo estatísticas do repositório (modo: %s)", mode)
        _, _, json_data = self._run_command(
            [
                "restic",
                "-r",
                self.repository,
                "stats",
                "--mode",
                mode,
                "--json",
            ],
            capture_json=True,
        )

        if json_data is None:
            return {}

        return cast(Dict[str, Any], json_data)

    def create_timestamped_restore_dir(self, base_dir: str) -> str:
        """Cria um diretório com timestamp para restauração.

        Parameters
        ----------
        base_dir : str
            Diretório base para criar o subdiretório com timestamp

        Returns
        -------
        str
            Caminho completo do diretório criado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        restore_dir = Path(base_dir) / timestamp
        restore_dir.mkdir(parents=True, exist_ok=True)
        return str(restore_dir)