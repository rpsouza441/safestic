"""Wrapper centralizado para operacoes do Restic com retry e tratamento de erros.

Este modulo fornece a classe ResticClient que encapsula todas as operacoes comuns
do Restic (backup, restore, listagem, etc.) com suporte a retry automatico,
backoff exponencial e tratamento estruturado de erros.
"""

from __future__ import annotations

import json
import logging
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union, cast

from .restic import load_restic_env
from .restic_common import (
    ResticAuthenticationError,
    ResticCommandError,
    ResticError,
    ResticNetworkError,
    ResticPermissionError,
    ResticRepositoryError,
    analyze_command_error,
    build_restic_command,
    redact_secrets,
)
from .env import get_credential_source

# Tipo generico para o resultado de funcoes com retry
T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    retriable_errors: Sequence[type[Exception]] | Tuple[type[Exception], ...] = (
        ResticNetworkError,
        ResticRepositoryError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator para adicionar retry com backoff exponencial a uma funcao.

    Parameters
    ----------
    max_attempts : int, optional
        Numero maximo de tentativas, por padrao 3
    initial_backoff : float, optional
        Tempo inicial de espera em segundos, por padrao 1.0
    max_backoff : float, optional
        Tempo maximo de espera em segundos, por padrao 30.0
    backoff_factor : float, optional
        Fator multiplicativo para backoff exponencial, por padrao 2.0
    jitter : float, optional
        Fator de aleatoriedade para evitar thundering herd, por padrao 0.1

    Returns
    -------
    Callable
        Funcao decorada com retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            attempt = 1

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(retriable_errors) as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        break

                    # Calcular tempo de espera com backoff exponencial e jitter
                    backoff = min(
                        max_backoff,
                        initial_backoff * (backoff_factor ** (attempt - 1)),
                    )
                    # Adicionar jitter (variacao aleatoria)
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
                    # Outros tipos de excecao nao sao retentados
                    raise exc

            # Se chegamos aqui, todas as tentativas falharam
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


class ResticClient:
    """Cliente para interacao com o Restic com suporte a retry e tratamento de erros.

    Esta classe encapsula todas as operacoes comuns do Restic e fornece uma
    interface Python amigavel com tratamento adequado de erros, retry automatico
    para falhas transitorias e logging estruturado.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        max_attempts: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 30.0,
        credential_source: str = "env",
        repository: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        provider: Optional[str] = None,
    ):
        """Inicializa o cliente Restic.

        Parameters
        ----------
        log_file : Optional[str], optional
            Caminho para o arquivo de log, por padrao None
        max_attempts : int, optional
            Numero maximo de tentativas para operacoes com retry, por padrao 3
        initial_backoff : float, optional
            Tempo inicial de espera entre tentativas em segundos, por padrao 1.0
        max_backoff : float, optional
            Tempo maximo de espera entre tentativas em segundos, por padrao 30.0
        credential_source : str, optional
            Fonte de credenciais (env, keyring, etc.), por padrao "env"
        repository : Optional[str], optional
            URL do repositorio (se fornecido, evita carregar do ambiente)
        env : Optional[Dict[str, str]], optional
            Variaveis de ambiente (se fornecido, evita carregar do ambiente)
        provider : Optional[str], optional
            Provedor de armazenamento (se fornecido, evita carregar do ambiente)
        """
        # Usar valores fornecidos ou carregar do ambiente
        if repository and env and provider:
            self.repository = repository
            self.env = env
            self.provider = provider
        else:
            self.repository, self.env, self.provider = load_restic_env(credential_source)
        
        self.log_file = log_file
        self.logger = logging.getLogger("restic_client")

        # Configuracoes de retry
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
            Se True, tenta fazer parse do output como JSON, por padrao False
        check : bool, optional
            Se True, verifica o codigo de retorno e levanta excecao em caso de erro,
            por padrao True

        Returns
        -------
        Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]
            Tupla contendo (sucesso, resultado do processo, dados JSON se aplicavel)

        Raises
        ------
        ResticNetworkError
            Erro de rede ao acessar o repositorio
        ResticRepositoryError
            Erro relacionado ao repositorio
        ResticAuthenticationError
            Erro de autenticacao
        ResticPermissionError
            Erro de permissao
        ResticCommandError
            Outro erro na execucao do comando
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
                "Comando concluido em %.2f segundos (codigo: %d)",
                elapsed,
                result.returncode,
            )

            # Processar saida e erro
            if result.stdout:
                self.logger.debug("Saida: %s", redact_secrets(result.stdout))

            if result.stderr:
                self.logger.debug("Erro: %s", redact_secrets(result.stderr))

            # Verificar erros
            if check and result.returncode != 0:
                analyze_command_error(
                    cmd, result.returncode, result.stdout or "", result.stderr or ""
                )

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

    def run_raw(
        self,
        args: Sequence[str],
        capture_json: bool = False,
        check: bool = True,
    ) -> Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]:
        """Executa um comando Restic arbitrário.

        Parameters
        ----------
        args : Sequence[str]
            Argumentos do comando Restic, sem incluir a palavra ``restic``.
        capture_json : bool, optional
            Se True, tenta fazer parse do output como JSON, por padrao False
        check : bool, optional
            Se True, verifica o codigo de retorno e levanta excecao em caso de erro,
            por padrao True

        Returns
        -------
        Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]
            Resultado da execucao do comando.
        """

        cmd = build_restic_command(*args)
        return self._run_command(cmd, capture_json=capture_json, check=check)

    def get_version(self) -> str:
        """Obtém a versão instalada do Restic."""

        success, result, _ = self.run_raw(["version"])
        if result is None:
            return ""
        return result.stdout.strip()

    @with_retry()
    def check_repository_access(self) -> bool:
        """Verifica se o repositorio Restic esta acessivel.

        Returns
        -------
        bool
            True se o repositorio esta acessivel, False caso contrario

        Raises
        ------
        ResticError
            Se ocorrer um erro ao acessar o repositorio
        """
        self.logger.info("Verificando acesso ao repositorio: %s", self.repository)
        success, _, _ = self._run_command(
            build_restic_command("snapshots", repository=self.repository),
            check=True,
        )
        return success

    def init_repository(self) -> bool:
        """Inicializa um novo repositorio Restic se nao existir.

        Returns
        -------
        bool
            True se o repositorio foi inicializado com sucesso, False caso contrario
        """
        self.logger.info("Inicializando repositorio: %s", self.repository)
        success, _, _ = self._run_command(
            build_restic_command("init", repository=self.repository),
            check=False,
        )
        return success

    def check_restic_installed(self) -> bool:
        """Verifica se o Restic esta instalado e acessivel.

        Returns
        -------
        bool
            True se o Restic esta instalado e acessivel, False caso contrario
        """
        self.logger.info("Verificando se o Restic esta instalado...")
        try:
            success, _, _ = self._run_command(
                build_restic_command("version"),
                check=False,
            )
            return success
        except Exception as exc:
            self.logger.error("Erro ao verificar instalacao do Restic: %s", exc)
            return False

    def supports_mount(self) -> bool:
        """Verifica se o comando ``mount`` esta disponivel no Restic."""
        self.logger.info("Verificando suporte ao comando mount")
        success, result, _ = self._run_command(
            build_restic_command("help"), check=False
        )
        return success and result is not None and "mount" in result.stdout

    @with_retry()
    def check_repository(self, read_data_subset: Optional[str] = None) -> bool:
        """Executa ``restic check`` para validar o repositorio.

        Parameters
        ----------
        read_data_subset : Optional[str], optional
            Percentual de dados a serem lidos para verificacao, por padrao None

        Returns
        -------
        bool
            True se o repositorio passou na verificacao

        Raises
        ------
        ResticError
            Se ocorrer um erro durante a verificacao
        """
        cmd = build_restic_command("check", repository=self.repository)
        if read_data_subset:
            cmd.extend(["--read-data-subset", read_data_subset])

        self.logger.info("Verificando integridade do repositorio")
        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def backup(
        self,
        paths: Optional[List[str]] = None,
        excludes: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source_dirs: Optional[List[str]] = None,
    ) -> str:
        """Executa um backup com Restic.

        Parameters
        ----------
        paths : Optional[List[str]]
            Lista de caminhos a serem incluidos no backup
        excludes : Optional[List[str]], optional
            Lista de padroes a serem excluidos, por padrao None
        tags : Optional[List[str]], optional
            Lista de tags a serem aplicadas ao snapshot, por padrao None
        source_dirs : Optional[List[str]]
            Alias para ``paths`` para compatibilidade retroativa

        Returns
        -------
        str
            ID do snapshot criado

        Raises
        ------
        ResticError
            Se ocorrer um erro durante o backup
        """
        if paths is None:
            paths = source_dirs or []
        if not paths:
            raise ValueError("Pelo menos um caminho deve ser especificado para backup")

        cmd = build_restic_command("backup", repository=self.repository)
        cmd.extend(paths)

        # Adicionar exclusoes
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
            "Iniciando backup de %d caminhos com %d exclusoes e %d tags",
            len(paths),
            len(excludes or []),
            len(tags or []),
        )

        success, result, _ = self._run_command(cmd)

        if success and result and result.stdout:
            snapshot_id = None
            match = re.search(r"snapshot ([a-f0-9]+) saved", result.stdout)
            if match:
                snapshot_id = match.group(1)
            else:
                try:
                    data = json.loads(result.stdout)
                    snapshot_id = data.get("snapshot", {}).get("id")
                except json.JSONDecodeError:
                    pass

            if snapshot_id:
                self.logger.info("Backup concluido com sucesso, ID: %s", snapshot_id)
                return snapshot_id

        raise ResticCommandError(
            message="Nao foi possivel extrair o ID do snapshot da saida do comando",
            command=cmd,
            returncode=result.returncode if result else None,
            stdout=result.stdout if result else None,
            stderr=result.stderr if result else None,
        )

    @with_retry()
    def apply_retention_policy(
        self,
        keep_last: Optional[int] = None,
        keep_hourly: Optional[int] = None,
        keep_daily: Optional[int] = None,
        keep_weekly: Optional[int] = None,
        keep_monthly: Optional[int] = None,
        keep_yearly: Optional[int] = None,
        prune: bool = True,
        last: Optional[int] = None,
        hourly: Optional[int] = None,
        daily: Optional[int] = None,
        weekly: Optional[int] = None,
        monthly: Optional[int] = None,
        yearly: Optional[int] = None,
    ) -> bool:
        """Aplica politica de retencao aos snapshots."""

        keep_last = keep_last if keep_last is not None else last
        keep_hourly = keep_hourly if keep_hourly is not None else hourly
        keep_daily = keep_daily if keep_daily is not None else daily
        keep_weekly = keep_weekly if keep_weekly is not None else weekly
        keep_monthly = keep_monthly if keep_monthly is not None else monthly
        keep_yearly = keep_yearly if keep_yearly is not None else yearly

        cmd = build_restic_command("forget", repository=self.repository)
        if keep_last is not None:
            cmd.extend(["--keep-last", str(keep_last)])
        if keep_hourly is not None:
            cmd.extend(["--keep-hourly", str(keep_hourly)])
        if keep_daily is not None:
            cmd.extend(["--keep-daily", str(keep_daily)])
        if keep_weekly is not None:
            cmd.extend(["--keep-weekly", str(keep_weekly)])
        if keep_monthly is not None:
            cmd.extend(["--keep-monthly", str(keep_monthly)])
        if keep_yearly is not None:
            cmd.extend(["--keep-yearly", str(keep_yearly)])

        if prune:
            cmd.append("--prune")

        self.logger.info(
            "Aplicando politica de retencao (l:%s, h:%s, d:%s, w:%s, m:%s, y:%s, prune:%s)",
            keep_last,
            keep_hourly,
            keep_daily,
            keep_weekly,
            keep_monthly,
            keep_yearly,
            prune,
        )

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def forget_snapshots(
        self,
        keep_hourly: int = 0,
        keep_daily: int = 7,
        keep_weekly: int = 4,
        keep_monthly: int = 6,
        tags: Optional[List[str]] = None,
        prune: bool = True,
    ) -> bool:
        """Esquece snapshots antigos aplicando politica de retencao.

        Parameters
        ----------
        keep_hourly : int, optional
            Numero de snapshots horarios a manter, por padrao 0
        keep_daily : int, optional
            Numero de snapshots diarios a manter, por padrao 7
        keep_weekly : int, optional
            Numero de snapshots semanais a manter, por padrao 4
        keep_monthly : int, optional
            Numero de snapshots mensais a manter, por padrao 6
        tags : Optional[List[str]], optional
            Lista de tags usadas para filtrar snapshots, por padrao None
        prune : bool, optional
            Se True, executa prune apos forget, por padrao True

        Returns
        -------
        bool
            True se a politica foi aplicada com sucesso

        Raises
        ------
        ResticError
            Se ocorrer um erro ao aplicar a politica
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

        if tags:
            for tag in tags:
                if tag.strip():
                    cmd.extend(["--tag", tag.strip()])

        if prune:
            cmd.append("--prune")

        cmd.append("--verbose")

        self.logger.info(
            "Esquecendo snapshots com politica de retencao (h:%d, d:%d, w:%d, m:%d, tags:%s, prune:%s)",
            keep_hourly,
            keep_daily,
            keep_weekly,
            keep_monthly,
            tags,
            prune,
        )

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Lista todos os snapshots no repositorio.

        Returns
        -------
        List[Dict[str, Any]]
            Lista de snapshots com suas informacoes

        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar os snapshots
        """
        self.logger.info("Listando snapshots do repositorio")
        _, _, json_data = self._run_command(
            build_restic_command("snapshots", "--json", repository=self.repository),
            capture_json=True,
        )

        if json_data is None:
            return []

        return cast(List[Dict[str, Any]], json_data)

    @with_retry()
    def get_snapshot_info(self, snapshot_id: str = "latest") -> Dict[str, Any]:
        """Obtem informacoes detalhadas sobre um snapshot especifico.

        Parameters
        ----------
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrao "latest"

        Returns
        -------
        Dict[str, Any]
            Informacoes do snapshot

        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter as informacoes
        """
        self.logger.info("Obtendo informacoes do snapshot: %s", snapshot_id)
        _, _, json_data = self._run_command(
            build_restic_command(
                "snapshots", snapshot_id, "--json", repository=self.repository
            ),
            capture_json=True,
        )

        if not json_data or not isinstance(json_data, list) or not json_data:
            raise ResticCommandError(
                message=f"Nao foi possivel obter informacoes do snapshot {snapshot_id}",
                command=build_restic_command(
                    "snapshots", snapshot_id, "--json", repository=self.repository
                ),
            )

        return cast(Dict[str, Any], json_data[0])

    @with_retry()
    def list_files(self, snapshot_id: str = "latest") -> List[Dict[str, Any]]:
        """Lista os arquivos contidos em um snapshot.

        Parameters
        ----------
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrao "latest"

        Returns
        -------
        List[Dict[str, Any]]
            Lista de arquivos com metadados

        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar os arquivos
        """
        self.logger.info("Listando arquivos do snapshot: %s", snapshot_id)
        _, _, json_data = self._run_command(
            build_restic_command("ls", snapshot_id, "--json", repository=self.repository),
            capture_json=True,
        )

        if json_data is None:
            return []

        return cast(List[Dict[str, Any]], json_data)

    # Alias para compatibilidade retroativa
    def list_snapshot_files(self, snapshot_id: str = "latest") -> List[str]:
        return [f.get("path", "") for f in self.list_files(snapshot_id)]

    @with_retry()
    def rebuild_index(self, read_all_packs: bool = False) -> bool:
        """Reconstrói o indice do repositorio.

        Parameters
        ----------
        read_all_packs : bool, optional
            Se True, usa ``--read-all-packs`` para verificacao completa

        Returns
        -------
        bool
            True se a reconstrucao foi bem-sucedida

        Raises
        ------
        ResticError
            Se ocorrer um erro durante a reconstrucao
        """
        cmd = build_restic_command("rebuild-index", repository=self.repository)
        if read_all_packs:
            cmd.append("--read-all-packs")

        self.logger.info("Reconstruindo indice do repositorio")
        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def repair_snapshots(self) -> bool:
        """Repara snapshots corrompidos no repositorio."""
        self.logger.info("Reparando snapshots do repositorio")
        success, _, _ = self._run_command(
            build_restic_command("repair", "snapshots", repository=self.repository)
        )
        return success

    @with_retry()
    def repair_index(self) -> bool:
        """Repara o indice do repositorio."""
        self.logger.info("Reparando indice do repositorio")
        success, _, _ = self._run_command(
            build_restic_command("repair", "index", repository=self.repository)
        )
        return success

    @with_retry()
    def repair_packs(self) -> bool:
        """Repara packs corrompidos no repositorio."""
        self.logger.info("Reparando packs do repositorio")
        success, _, _ = self._run_command(
            build_restic_command("repair", "packs", repository=self.repository)
        )
        return success

    def mount_repository(self, mount_path: str, extra_args: Optional[List[str]] = None) -> subprocess.Popen[str]:
        """Monta o repositorio utilizando ``restic mount``.

        Esta operacao e bloqueante e retorna o processo iniciado para que o
        chamador possa gerenciar seu ciclo de vida.

        Parameters
        ----------
        mount_path : str
            Caminho onde o repositorio sera montado
        extra_args : Optional[List[str]], optional
            Lista de argumentos adicionais a serem passados para ``restic mount``

        Returns
        -------
        subprocess.Popen[str]
            Processo em execucao do comando ``restic mount``
        """
        cmd = build_restic_command("mount", mount_path, repository=self.repository)
        if extra_args:
            cmd.extend(extra_args)

        self.logger.info("Montando repositorio em %s", mount_path)
        process = subprocess.Popen(
            cmd,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        return process

    @with_retry()
    def restore_snapshot(
        self, target_dir: str, snapshot_id: str = "latest", include_paths: Optional[List[str]] = None
    ) -> bool:
        """Restaura um snapshot completo ou arquivos especificos.

        Parameters
        ----------
        target_dir : str
            Diretorio de destino para a restauracao
        snapshot_id : str, optional
            ID do snapshot ou "latest", por padrao "latest"
        include_paths : Optional[List[str]], optional
            Lista de caminhos especificos a restaurar, por padrao None (restaura tudo)

        Returns
        -------
        bool
            True se a restauracao foi bem-sucedida

        Raises
        ------
        ResticError
            Se ocorrer um erro durante a restauracao
        """
        # Garantir que o diretorio de destino existe
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        cmd = build_restic_command(
            "restore", snapshot_id, "--target", target_dir, repository=self.repository
        )

        # Adicionar caminhos especificos se fornecidos
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
        """Obtem estatisticas do repositorio.

        Parameters
        ----------
        mode : str, optional
            Modo de calculo ("raw-data", "restore-size", "blobs-per-file"),
            por padrao "raw-data"

        Returns
        -------
        Dict[str, Any]
            Estatisticas do repositorio

        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter as estatisticas
        """
        self.logger.info("Obtendo estatisticas do repositorio (modo: %s)", mode)
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
        """Cria um diretorio com timestamp para restauracao.

        Parameters
        ----------
        base_dir : str
            Diretorio base para criar o subdiretorio com timestamp

        Returns
        -------
        str
            Caminho completo do diretorio criado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        restore_dir = Path(base_dir) / timestamp
        restore_dir.mkdir(parents=True, exist_ok=True)
        return str(restore_dir)


def load_env_and_get_credential_source() -> str:
    """Backward compatible wrapper for :func:`get_credential_source`."""
    return get_credential_source()
