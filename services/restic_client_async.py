"""Cliente assíncrono para operações do Restic.

Este módulo fornece uma versão assíncrona do ResticClient para operações
que envolvem I/O intensivo, permitindo execução em paralelo quando seguro.
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

# Configuração de logger
logger = logging.getLogger(__name__)

# Tipos para anotações
T = TypeVar('T')
AsyncCallable = Callable[..., T]


def with_async_retry(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retriable_errors: Tuple[type[Exception], ...] = (ResticNetworkError,),
) -> Callable[[AsyncCallable], AsyncCallable]:
    """Decorador para funções assíncronas com retry automático.
    
    Parameters
    ----------
    max_attempts : int
        Número máximo de tentativas
    retry_delay : float
        Tempo de espera inicial entre tentativas (segundos)
    backoff_factor : float
        Fator de multiplicação do tempo de espera a cada tentativa
    retriable_errors : Tuple[type[Exception], ...]
        Tipos de exceções que devem ser retentadas
        
    Returns
    -------
    Callable
        Função decorada com retry
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
                            f"Último erro: {str(e)}"
                        )
                        raise
                except Exception as e:
                    # Não retentar para outros tipos de exceção
                    logger.error(f"Erro não-retentável: {str(e)}")
                    raise
            
            # Nunca deve chegar aqui, mas para satisfazer o type checker
            assert last_exception is not None
            raise last_exception
        
        return wrapper
    
    return decorator


class ResticClientAsync:
    """Cliente assíncrono para operações do Restic.
    
    Esta classe fornece métodos assíncronos para executar operações do Restic,
    permitindo execução em paralelo quando seguro.
    
    Parameters
    ----------
    repository : str
        URL do repositório Restic
    password : str
        Senha do repositório
    env : Optional[Dict[str, str]]
        Variáveis de ambiente adicionais
    """
    
    def __init__(
        self,
        repository: str,
        password: str,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self.repository = repository
        self.password = password
        
        # Preparar variáveis de ambiente
        self.env = os.environ.copy()
        self.env["RESTIC_REPOSITORY"] = repository
        self.env["RESTIC_PASSWORD"] = password
        
        # Adicionar variáveis de ambiente extras
        if env:
            self.env.update(env)
    
    async def _run_command(
        self,
        args: Sequence[str],
        timeout: Optional[int] = None,
        capture_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Executa um comando Restic de forma assíncrona.
        
        Parameters
        ----------
        args : Sequence[str]
            Argumentos para o comando Restic
        timeout : Optional[int]
            Tempo limite em segundos
        capture_json : bool
            Se deve capturar e analisar a saída como JSON
            
        Returns
        -------
        Tuple[int, str, str]
            Código de retorno, stdout e stderr
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao executar o comando
        """
        # Verificar se o Restic está instalado
        if not shutil.which("restic"):
            raise ResticError("Restic não está instalado ou não está no PATH")
        
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
            
            # Aguardar conclusão com timeout
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
            
            # Obter código de retorno
            returncode = process.returncode
            
            # Redigir segredos na saída
            safe_stdout = redact_secrets(stdout)
            safe_stderr = redact_secrets(stderr)
            
            # Analisar saída
            if returncode != 0:
                # Identificar tipo de erro
                if "network" in safe_stderr.lower() or "connection" in safe_stderr.lower():
                    raise ResticNetworkError(f"Erro de rede: {safe_stderr}")
                elif "repository" in safe_stderr.lower():
                    raise ResticRepositoryError(f"Erro no repositório: {safe_stderr}")
                elif "password" in safe_stderr.lower() or "authentication" in safe_stderr.lower():
                    raise ResticAuthenticationError(f"Erro de autenticação: {safe_stderr}")
                else:
                    raise ResticError(f"Comando falhou com código {returncode}: {safe_stderr}")
            
            # Capturar JSON se solicitado
            if capture_json and safe_stdout:
                try:
                    json.loads(safe_stdout)
                except json.JSONDecodeError:
                    logger.warning("Falha ao analisar saída como JSON")
            
            return returncode, safe_stdout, safe_stderr
            
        except ResticError:
            # Re-lançar exceções específicas
            raise
        except Exception as e:
            # Converter outras exceções
            raise ResticError(f"Erro ao executar comando: {str(e)}")
    
    @with_async_retry()
    async def check_repository(self) -> bool:
        """Verifica se o repositório está acessível e íntegro.
        
        Returns
        -------
        bool
            True se o repositório está acessível e íntegro
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao verificar o repositório
        """
        try:
            _, stdout, _ = await self._run_command(["check", "--read-data=false"])
            return "no errors were found" in stdout.lower()
        except ResticError as e:
            logger.error(f"Erro ao verificar repositório: {str(e)}")
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
            Caminhos a serem incluídos no backup
        exclude_patterns : Optional[List[str]]
            Padrões a serem excluídos do backup
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
                raise ResticError(f"Caminho não encontrado: {path}")
        
        # Construir comando
        cmd = ["backup"]
        
        # Adicionar tags
        if tags:
            for tag in tags:
                cmd.extend(["--tag", tag])
        
        # Adicionar exclusões
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
                raise ResticError("Não foi possível extrair ID do snapshot")
        except ResticError as e:
            logger.error(f"Erro ao realizar backup: {str(e)}")
            raise
    
    @with_async_retry()
    async def list_snapshots(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista snapshots no repositório.
        
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
            
            # Analisar saída JSON
            snapshots = json.loads(stdout)
            return snapshots
        except ResticError as e:
            logger.error(f"Erro ao listar snapshots: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saída JSON: {str(e)}")
    
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
            
            # Analisar saída JSON
            files = json.loads(stdout)
            return files
        except ResticError as e:
            logger.error(f"Erro ao listar arquivos: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saída JSON: {str(e)}")
    
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
            Diretório de destino para restauração
        include_patterns : Optional[List[str]]
            Padrões a serem incluídos na restauração
            
        Returns
        -------
        bool
            True se a restauração foi bem-sucedida
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao restaurar snapshot
        """
        # Construir comando
        cmd = ["restore", snapshot_id]
        
        # Adicionar diretório de destino
        if target_dir:
            cmd.extend(["--target", target_dir])
            
            # Criar diretório de destino se não existir
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        # Adicionar padrões de inclusão
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
        """Restaura um arquivo específico.
        
        Parameters
        ----------
        path : str
            Caminho do arquivo a ser restaurado
        snapshot_id : str
            ID do snapshot ou "latest"
        target_dir : Optional[str]
            Diretório de destino para restauração
            
        Returns
        -------
        bool
            True se a restauração foi bem-sucedida
            
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
        """Aplica política de retenção ao repositório.
        
        Parameters
        ----------
        keep_last : Optional[int]
            Número de snapshots recentes a manter
        keep_daily : Optional[int]
            Número de snapshots diários a manter
        keep_weekly : Optional[int]
            Número de snapshots semanais a manter
        keep_monthly : Optional[int]
            Número de snapshots mensais a manter
        keep_yearly : Optional[int]
            Número de snapshots anuais a manter
        keep_tags : Optional[List[str]]
            Tags de snapshots a manter
            
        Returns
        -------
        bool
            True se a política foi aplicada com sucesso
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao aplicar política de retenção
        """
        # Construir comando
        cmd = ["forget", "--prune"]
        
        # Adicionar políticas de retenção
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
            logger.error(f"Erro ao aplicar política de retenção: {str(e)}")
            raise
    
    @with_async_retry()
    async def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do repositório.
        
        Returns
        -------
        Dict[str, Any]
            Estatísticas do repositório
            
        Raises
        ------
        ResticError
            Se ocorrer um erro ao obter estatísticas
        """
        try:
            # Executar comando
            _, stdout, _ = await self._run_command(
                ["stats", "--json"],
                capture_json=True,
            )
            
            # Analisar saída JSON
            stats = json.loads(stdout)
            return stats
        except ResticError as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            raise ResticError(f"Erro ao analisar saída JSON: {str(e)}")