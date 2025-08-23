"""Cliente assincrono para operacoes do Restic.

Este modulo fornece uma versao assincrona do ResticClient para operacoes
que envolvem I/O intensivo, permitindo execucao em paralelo quando seguro.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

from .restic_common import (
    ResticAuthenticationError,
    ResticCommandError,
    ResticError,
    ResticNetworkError,
    ResticPermissionError,
    ResticRepositoryError,
    analyze_command_error,
)
from .restic_base import (
    build_restic_command,
    redact_secrets,
    with_async_retry,
)

# Configuracao de logger
logger = logging.getLogger(__name__)


class ResticClientAsync:
    """Cliente assincrono para operacoes do Restic.
    
    Esta classe fornece metodos assincronos para executar operacoes do Restic,
    permitindo execucao em paralelo quando seguro.
    
    Parameters
    ----------
    credential_source : str
        Fonte para obtencao de credenciais (env, keyring, etc.)
    repository : Optional[str]
        URL do repositorio Restic (se fornecido, evita carregar do ambiente)
    env : Optional[Dict[str, str]]
        Variaveis de ambiente adicionais
    provider : Optional[str]
        Provedor de armazenamento (somente informativo)
    """

    def __init__(
        self,
        credential_source: str = "env",
        repository: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        provider: Optional[str] = None,
    ) -> None:
        # Usar valores fornecidos ou carregar do ambiente
        if repository and env:
            self.repository = repository
            self.env = env
            self.provider = provider or ""
        else:
            from .restic import load_restic_env

            self.repository, self.env, self.provider = load_restic_env(credential_source)

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
        # Construir comando completo
        cmd = build_restic_command(*args)
        
        # Redigir segredos para logging
        safe_cmd = [redact_secrets(str(arg)) for arg in cmd]

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
                analyze_command_error(cmd, returncode, safe_stdout, safe_stderr)
            
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
    async def check_repository_access(self) -> bool:
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
        excludes: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Realiza backup dos caminhos especificados.
        
        Parameters
        ----------
        paths : List[str]
            Caminhos a serem incluidos no backup
        excludes : Optional[List[str]]
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
        if excludes:
            for pattern in excludes:
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
        target_dir: str,
        snapshot_id: str = "latest",
        include_paths: Optional[List[str]] = None,
    ) -> bool:
        """Restaura um snapshot.
        
        Parameters
        ----------
        target_dir : str
            Diretorio de destino para restauracao
        snapshot_id : str
            ID do snapshot ou "latest"
        include_paths : Optional[List[str]]
            Caminhos a serem incluidos na restauracao
            
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
        cmd = ["restore", snapshot_id, "--target", target_dir]

        # Garantir que o diretorio de destino existe
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # Adicionar caminhos de inclusao
        if include_paths:
            for pattern in include_paths:
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
        target_dir: str = ".",
    ) -> bool:
        """Restaura um arquivo especifico.
        
        Parameters
        ----------
        path : str
            Caminho do arquivo a ser restaurado
        snapshot_id : str
            ID do snapshot ou "latest"
        target_dir : str
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
            target_dir=target_dir,
            snapshot_id=snapshot_id,
            include_paths=[path],
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
