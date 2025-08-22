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
    build_restic_command,
    redact_secrets,
    raise_for_command_error,
)

# Tipo generico para o resultado de funcoes com retry
T = TypeVar("T")



def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
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
                except (ResticNetworkError, ResticRepositoryError) as exc:
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
        args: Sequence[str],
        capture_json: bool = False,
        check: bool = True,
    ) -> Tuple[bool, Optional[subprocess.CompletedProcess[str]], Optional[Any]]:
        """Executa um comando do Restic com tratamento de erros.

        Parameters
        ----------
        args : Sequence[str]
            Argumentos a serem passados para o comando restic
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
        cmd = build_restic_command(*args)
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
                raise_for_command_error(
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

    @with_retry()
    def check_repository(self) -> bool:
        """Verifica se o repositorio Restic esta acessivel e integro."""
        self.logger.info("Verificando acesso ao repositorio: %s", self.repository)
        _, result, _ = self._run_command(
            ["-r", self.repository, "check", "--read-data=false"]
        )
        stdout = result.stdout if result and result.stdout else ""
        return "no errors were found" in stdout.lower()

    def init_repository(self) -> bool:
        """Inicializa um novo repositorio Restic se nao existir.

        Returns
        -------
        bool
            True se o repositorio foi inicializado com sucesso, False caso contrario
        """
        self.logger.info("Inicializando repositorio: %s", self.repository)
        success, _, _ = self._run_command(
            ["-r", self.repository, "init"],
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
            success, _, _ = self._run_command(["version"], check=False)
            return success
        except Exception as exc:
            self.logger.error("Erro ao verificar instalacao do Restic: %s", exc)
            return False

    @with_retry()
    def backup(
        self,
        paths: List[str],
        exclude_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Executa um backup com Restic.

        Parameters
        ----------
        paths : List[str]
            Lista de caminhos a serem incluidos no backup
        exclude_patterns : Optional[List[str]], optional
            Lista de padroes a serem excluidos, por padrao None
        tags : Optional[List[str]], optional
            Lista de tags a serem aplicadas ao snapshot, por padrao None

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

        cmd = ["-r", self.repository, "backup"]
        cmd.extend(paths)

        # Adicionar exclusoes
        if exclude_patterns:
            for exclude in exclude_patterns:
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
            len(exclude_patterns or []),
            len(tags or []),
        )

        success, result, _ = self._run_command(cmd)

        if success and result and result.stdout:
            # Extrair ID do snapshot da saida
            match = re.search(r"snapshot ([a-f0-9]+) saved", result.stdout)
            if match:
                snapshot_id = match.group(1)
                self.logger.info("Backup concluido com sucesso, ID: %s", snapshot_id)
                return snapshot_id

        # Se chegamos aqui, nao conseguimos extrair o ID do snapshot
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
        keep_tags: Optional[List[str]] = None,
        prune: bool = True,
    ) -> bool:
        """Aplica politica de retencao aos snapshots.

        Parameters
        ----------
        keep_last : Optional[int]
            Numero total de snapshots recentes a manter
        keep_hourly : Optional[int]
            Numero de snapshots horarios a manter
        keep_daily : Optional[int]
            Numero de snapshots diarios a manter
        keep_weekly : Optional[int]
            Numero de snapshots semanais a manter
        keep_monthly : Optional[int]
            Numero de snapshots mensais a manter
        keep_yearly : Optional[int]
            Numero de snapshots anuais a manter
        keep_tags : Optional[List[str]]
            Tags de snapshots a manter
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
        cmd = ["-r", self.repository, "forget"]

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
        if keep_tags:
            for tag in keep_tags:
                cmd.extend(["--keep-tag", tag])
        if prune:
            cmd.append("--prune")

        self.logger.info("Aplicando politica de retencao: %s", " ".join(cmd))

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def restore_file(
        self,
        path: str,
        snapshot_id: str = "latest",
        target_dir: Optional[str] = None,
    ) -> bool:
        """Restaura um arquivo especifico de um snapshot."""
        return self.restore_snapshot(
            snapshot_id=snapshot_id,
            target_dir=target_dir,
            include_patterns=[path],
        )

    @with_retry()
    def list_snapshots(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista snapshots no repositorio."""
        self.logger.info("Listando snapshots do repositorio")
        cmd = ["-r", self.repository, "snapshots", "--json"]
        if tag:
            cmd.extend(["--tag", tag])
        _, _, json_data = self._run_command(cmd, capture_json=True)
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
        cmd = ["-r", self.repository, "snapshots", snapshot_id, "--json"]
        _, _, json_data = self._run_command(cmd, capture_json=True)

        if not json_data or not isinstance(json_data, list) or not json_data:
            raise ResticCommandError(
                message=f"Nao foi possivel obter informacoes do snapshot {snapshot_id}",
                command=build_restic_command(*cmd),
            )

        return cast(Dict[str, Any], json_data[0])

    @with_retry()
    def list_files(self, snapshot_id: str = "latest") -> List[Dict[str, Any]]:
        """Lista os arquivos contidos em um snapshot."""
        self.logger.info("Listando arquivos do snapshot: %s", snapshot_id)
        _, _, json_data = self._run_command(
            ["-r", self.repository, "ls", snapshot_id, "--json"],
            capture_json=True,
        )
        if json_data is None:
            return []
        return cast(List[Dict[str, Any]], json_data)

    @with_retry()
    def restore_snapshot(
        self,
        snapshot_id: str = "latest",
        target_dir: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
    ) -> bool:
        """Restaura um snapshot completo ou arquivos especificos.

        Parameters
        ----------
        snapshot_id : str
            ID do snapshot ou "latest"
        target_dir : Optional[str]
            Diretorio de destino para restauracao
        include_patterns : Optional[List[str]]
            Lista de caminhos especificos a restaurar

        Returns
        -------
        bool
            True se a restauracao foi bem-sucedida

        Raises
        ------
        ResticError
            Se ocorrer um erro durante a restauracao
        """
        if target_dir:
            Path(target_dir).mkdir(parents=True, exist_ok=True)

        cmd = ["-r", self.repository, "restore", snapshot_id]
        if target_dir:
            cmd.extend(["--target", target_dir])
        if include_patterns:
            for path in include_patterns:
                cmd.extend(["--include", path])

        self.logger.info(
            "Restaurando snapshot %s para %s", snapshot_id, target_dir or self.repository
        )

        success, _, _ = self._run_command(cmd)
        return success

    @with_retry()
    def get_stats(self, mode: str = "raw-data") -> Dict[str, Any]:
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
            ["-r", self.repository, "stats", "--mode", mode, "--json"],
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
    """Carrega o arquivo .env e retorna o credential_source configurado.
    
    Esta função centraliza o carregamento do ambiente para evitar duplicação
    de código nos comandos do Makefile.
    
    Returns
    -------
    str
        O valor de CREDENTIAL_SOURCE do arquivo .env (padrão: 'env')
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    return os.getenv('CREDENTIAL_SOURCE', 'env')
