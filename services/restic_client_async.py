"""Cliente assincrono para operacoes do Restic.

Este modulo fornece uma versao assincrona do ResticClient para operacoes
que envolvem I/O intensivo, permitindo execucao em paralelo quando seguro.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union, cast

from .restic_client import (
    ResticError, 
    ResticNetworkError, 
    ResticRepositoryError, 
    ResticAuthenticationError,
    redact_secrets
)

# Configuracao de logger
logger = logging.getLogger(__name__)

# Tipos para anotacoes
T = TypeVar('T')
AsyncCallable = Callable[..., T]


def with_async_retry(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retriable_errors: Tuple[type[Exception], ...] = (ResticNetworkError,),
) -> Callable[[AsyncCallable], AsyncCallable]:
    """Decorador para funcoes assincronas com retry automatico.
    
    Parameters
    ----------
    max_attempts : int
        Numero maximo de tentativas
    retry_delay : float
        Tempo de espera inicial entre tentativas (segundos)
    backoff_factor : float
        Fator de multiplicacao do tempo de espera a cada tentativa
    retriable_errors : Tuple[type[Exception], ...]
        Tipos de excecoes que devem ser retentadas
        
    Returns
    -------
    Callable
        Funcao decorada com retry
    """
    def decorator(func: AsyncCallable) -> AsyncCallable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = retry_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retriable_errors as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Tentativa {attempt}/{max_attempts} falhou: {str(e)}. "
                            f"Tentando novamente em {current_delay:.1f}s."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Todas as {max_attempts} tentativas falharam. "
                            f"ultimo erro: {str(e)}"
                        )
                        raise
                except Exception as e:
                    # Nao retentar para outros tipos de excecao
                    logger.error(f"Erro nao-retentavel: {str(e)}")
                    raise
            
            # Nunca deve chegar aqui, mas para satisfazer o type checker
            assert last_exception is not None
            raise last_exception
        
        return wrapper
    
    return decorator


class ResticClientAsync:
    """Cliente assincrono para operacoes do Restic.
    
    Esta classe fornece metodos assincronos para executar operacoes do Restic,
    permitindo execucao em paralelo quando seguro.
    
    Parameters
    ----------
    repository : str
        URL do repositorio Restic
    password : str
        Senha do repositorio
    env : Optional[Dict[str, str]]
        Variaveis de ambiente adicionais
    """
    
    def __init__(
        self,
        repository: str,
        password: str,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self.repository = repository
        self.password = password
        
        # Preparar variaveis de ambiente
        self.env = os.environ.copy()
        self.env["RESTIC_REPOSITORY"] = repository
        self.env["RESTIC_PASSWORD"] = password
        
        # Adicionar variaveis de ambiente extras
        if env:
            self.env.update(env)
    
    async def _run_command(
        self,
        args: Sequence[str],
        timeout: Optional[int] = None,
        capture_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Executa um comando Restic de forma assincrona.
        
        Parameters
        ----------
        args : Sequence[str]
            Argumentos para o comando Restic
        timeout : Optional[int]
            Tempo limite em segundos
        capture_json : bool
            Se deve capturar e analisar a saida como JSON
            
        Returns
        -------
        Tuple[int, str, str]
            Codigo de retorno, stdout e stderr
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao executar o comando
        """
        # Verificar se o Restic esta instalado
        if not shutil.which("restic"):
            raise ResticError("Restic nao esta instalado ou nao esta no PATH")
        
        # Construir comando completo
        cmd = ["restic"] + list(args)
        
        # Redigir segredos para logging
        safe_cmd = [redact_secrets(str(arg)) for arg in cmd]
        safe_env = {k: redact_secrets(str(v)) for k, v in self.env.items()}
        
        logger.debug(f"Executando: {' '.join(safe_cmd)}")
        
        try:
            # Criar processo
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=self.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True,
            )
            
            # Aguardar conclusao com timeout
            try:
                if timeout:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout
                    )
                else:
                    stdout, stderr = await process.communicate()
            except asyncio.TimeoutError:
                # Matar processo em caso de timeout
                try:
                    process.kill()
                except Exception:
                    pass
                raise ResticError(f"Comando excedeu o timeout de {timeout}s")
            
            # Obter codigo de retorno
            returncode = process.returncode
            
            # Redigir segredos na saida
            safe_stdout = redact_secrets(stdout)
            safe_stderr = redact_secrets(stderr)
            
            # Analisar saida
            if returncode != 0:
                # Identificar tipo de erro
                if "network" in safe_stderr.lower() or "connection" in safe_stderr.lower():
                    raise ResticNetworkError(f"Erro de rede: {safe_stderr}")
                elif "repository" in safe_stderr.lower():
                    raise ResticRepositoryError(f"Erro no repositorio: {safe_stderr}")
                elif "password" in safe_stderr.lower() or "authentication" in safe_stderr.lower():
                    raise ResticAuthenticationError(f"Erro de autenticacao: {safe_stderr}")
                else:
                    raise ResticError(f"Comando falhou com codigo {returncode}: {safe_stderr}")
            
            # Capturar JSON se solicitado
            if capture_json and safe_stdout:
                try:
                    json.loads(safe_stdout)
                except json.JSONDecodeError:
                    logger.warning("Falha ao analisar saida como JSON")
            
            return returncode, safe_stdout, safe_stderr
            
        except ResticError:
            # Re-lancar excecoes especificas
            raise
        except Exception as e:
            # Converter outras excecoes
            raise ResticError(f"Erro ao executar comando: {str(e)}")
    
    @with_async_retry()
    async def check_repository(self) -> bool:
        """Verifica se o repositorio esta acessivel e integro.
        
        Returns
        -------
        bool
            True se o repositorio esta acessivel e integro
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao verificar o repositorio
        """
        try:
            _, stdout, _ = await self._run_command(["check", "--read-data=false"])
            return "no errors were found" in stdout.lower()
        except ResticError as e:
            logger.error(f"Erro ao verificar repositorio: {str(e)}")
            raise
    
    @with_async_retry()
    async def backup(
        self,
        paths: List[str],
        exclude_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Realiza backup dos caminhos especificados.
        
        Parameters
        ----------
        paths : List[str]
            Caminhos a serem incluidos no backup
        exclude_patterns : Optional[List[str]]
            Padroes a serem excluidos do backup
        tags : Optional[List[str]]
            Tags a serem associadas ao snapshot
            
        Returns
        -------
        str
            ID do snapshot criado
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao realizar o backup
        """
        # Validar caminhos
        for path in paths:
            if not Path(path).exists():
                raise ResticError(f"Caminho nao encontrado: {path}")
        
        # Construir comando
        cmd = ["backup"]
        
        # Adicionar tags
        if tags:
            for tag in tags:
                cmd.extend(["--tag", tag])
        
        # Adicionar exclusoes
        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])
        
        # Adicionar caminhos
        cmd.extend(paths)
        
        try:
            # Executar comando
            _, stdout, _ = await self._run_command(cmd)
            
            # Extrair ID do snapshot
            match = re.search(r"snapshot ([a-f0-9]+) saved", stdout)
            if match:
                return match.group(1)
            else:
                raise ResticError("Nao foi possivel extrair ID do snapshot")
        except ResticError as e:
            logger.error(f"Erro ao realizar backup: {str(e)}")
            raise
    
    @with_async_retry()
    async def list_snapshots(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista snapshots no repositorio.
        
        Parameters
        ----------
        tag : Optional[str]
            Filtrar snapshots por tag
            
        Returns
        -------
        List[Dict[str, Any]]
            Lista de snapshots
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar snapshots
        """
        # Construir comando
        cmd = ["snapshots", "--json"]
        
        # Adicionar filtro por tag
        if tag:
            cmd.extend(["--tag", tag])
        
        try:
            # Executar comando
            _, stdout, _ = await self._run_command(cmd, capture_json=True)
            
            # Analisar saida JSON
            snapshots = json.loads(stdout)
            return snapshots
        except ResticError as e:
            logger.error(f"Erro ao listar snapshots: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saida JSON: {str(e)}")
    
    @with_async_retry()
    async def list_files(self, snapshot_id: str = "latest") -> List[Dict[str, Any]]:
        """Lista arquivos em um snapshot.
        
        Parameters
        ----------
        snapshot_id : str
            ID do snapshot ou "latest"
            
        Returns
        -------
        List[Dict[str, Any]]
            Lista de arquivos
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao listar arquivos
        """
        try:
            # Executar comando
            _, stdout, _ = await self._run_command(
                ["ls", snapshot_id, "--json"],
                capture_json=True,
            )
            
            # Analisar saida JSON
            files = json.loads(stdout)
            return files
        except ResticError as e:
            logger.error(f"Erro ao listar arquivos: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saida JSON: {str(e)}")
    
    @with_async_retry()
    async def restore_snapshot(
        self,
        snapshot_id: str = "latest",
        target_dir: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
    ) -> bool:
        """Restaura um snapshot.
        
        Parameters
        ----------
        snapshot_id : str
            ID do snapshot ou "latest"
        target_dir : Optional[str]
            Diretorio de destino para restauracao
        include_patterns : Optional[List[str]]
            Padroes a serem incluidos na restauracao
            
        Returns
        -------
        bool
            True se a restauracao foi bem-sucedida
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao restaurar snapshot
        """
        # Construir comando
        cmd = ["restore", snapshot_id]
        
        # Adicionar diretorio de destino
        if target_dir:
            cmd.extend(["--target", target_dir])
            
            # Criar diretorio de destino se nao existir
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Adicionar padroes de inclusao
        if include_patterns:
            for pattern in include_patterns:
                cmd.extend(["--include", pattern])
        
        try:
            # Executar comando
            await self._run_command(cmd)
            return True
        except ResticError as e:
            logger.error(f"Erro ao restaurar snapshot: {str(e)}")
            raise
    
    @with_async_retry()
    async def restore_file(
        self,
        path: str,
        snapshot_id: str = "latest",
        target_dir: Optional[str] = None,
    ) -> bool:
        """Restaura um arquivo especifico.
        
        Parameters
        ----------
        path : str
            Caminho do arquivo a ser restaurado
        snapshot_id : str
            ID do snapshot ou "latest"
        target_dir : Optional[str]
            Diretorio de destino para restauracao
            
        Returns
        -------
        bool
            True se a restauracao foi bem-sucedida
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao restaurar arquivo
        """
        return await self.restore_snapshot(
            snapshot_id=snapshot_id,
            target_dir=target_dir,
            include_patterns=[path],
        )
    
    @with_async_retry()
    async def apply_retention_policy(
        self,
        keep_last: Optional[int] = None,
        keep_daily: Optional[int] = None,
        keep_weekly: Optional[int] = None,
        keep_monthly: Optional[int] = None,
        keep_yearly: Optional[int] = None,
        keep_tags: Optional[List[str]] = None,
    ) -> bool:
        """Aplica politica de retencao ao repositorio.
        
        Parameters
        ----------
        keep_last : Optional[int]
            Numero de snapshots recentes a manter
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
            
        Returns
        -------
        bool
            True se a politica foi aplicada com sucesso
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao aplicar politica de retencao
        """
        # Construir comando
        cmd = ["forget", "--prune"]
        
        # Adicionar politicas de retencao
        if keep_last is not None:
            cmd.extend(["--keep-last", str(keep_last)])
        if keep_daily is not None:
            cmd.extend(["--keep-daily", str(keep_daily)])
        if keep_weekly is not None:
            cmd.extend(["--keep-weekly", str(keep_weekly)])
        if keep_monthly is not None:
            cmd.extend(["--keep-monthly", str(keep_monthly)])
        if keep_yearly is not None:
            cmd.extend(["--keep-yearly", str(keep_yearly)])
        
        # Adicionar tags a manter
        if keep_tags:
            for tag in keep_tags:
                cmd.extend(["--keep-tag", tag])
        
        try:
            # Executar comando
            await self._run_command(cmd)
            return True
        except ResticError as e:
            logger.error(f"Erro ao aplicar politica de retencao: {str(e)}")
            raise
    
    @with_async_retry()
    async def get_stats(self) -> Dict[str, Any]:
        """Obtem estatisticas do repositorio.
        
        Returns
        -------
        Dict[str, Any]
            Estatisticas do repositorio
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter estatisticas
        """
        try:
            # Executar comando
            _, stdout, _ = await self._run_command(
                ["stats", "--json"],
                capture_json=True,
            )
            
            # Analisar saida JSON
            stats = json.loads(stdout)
            return stats
        except ResticError as e:
            logger.error(f"Erro ao obter estatisticas: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saida JSON: {str(e)}")
