#!/usr/bin/env python3
"""
Script de verificacao de saude completa do sistema SafeStic
Verifica todas as dependencias, configuracoes e funcionalidades
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Adicionar o diretorio raiz ao path para importar services
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.logger import setup_logger
from services.restic import load_restic_config, load_restic_env
from services.restic_client import ResticClient
from services.env import get_credential_source

logger = setup_logger(__name__)

class HealthChecker:
    """Verificador de saude do sistema SafeStic"""
    
    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []
    
    def add_result(self, category: str, item: str, status: str, details: str = ""):
        """Adiciona resultado de verificacao"""
        result = {
            "category": category,
            "item": item,
            "status": status,
            "details": details
        }
        self.results.append(result)
        
        if status == "WARNING":
            self.warnings.append(f"{category} - {item}: {details}")
        elif status == "ERROR":
            self.errors.append(f"{category} - {item}: {details}")
    
    def check_command(self, command: str, name: str) -> bool:
        """Verifica se um comando esta disponivel"""
        try:
            # Restic usa 'version' ao inves de '--version'
            if command == "restic":
                result = subprocess.run([command, "version"], 
                                      capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run([command, "--version"], 
                                      capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                self.add_result("Dependencias", name, "OK", version)
                return True
            else:
                self.add_result("Dependencias", name, "ERROR", "Comando falhou")
                return False
        except FileNotFoundError:
            self.add_result("Dependencias", name, "ERROR", "Comando nao encontrado")
            return False
        except subprocess.TimeoutExpired:
            self.add_result("Dependencias", name, "ERROR", "Timeout na verificacao")
            return False
        except Exception as e:
            self.add_result("Dependencias", name, "ERROR", str(e))
            return False
    
    def check_python_packages(self):
        """Verifica pacotes Python necessarios"""
        required_packages = {
            "pydantic": "pydantic",
            "python-dotenv": "dotenv",
            "colorama": "colorama",
            "requests": "requests",
            "psutil": "psutil",
            "cryptography": "cryptography"
        }
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                self.add_result("Python Packages", package_name, "OK", "Importado com sucesso")
            except ImportError:
                self.add_result("Python Packages", package_name, "ERROR", "Pacote nao encontrado")
    
    def check_files_and_directories(self):
        """Verifica arquivos e diretorios essenciais"""
        essential_files = [
            ".env",
            "requirements.txt",
            "pyproject.toml",
            "Makefile",
            "services/__init__.py",
            "services/restic.py",
            "services/restic_client.py"
        ]
        
        for file_path in essential_files:
            if Path(file_path).exists():
                self.add_result("Arquivos", file_path, "OK", "Arquivo existe")
            else:
                self.add_result("Arquivos", file_path, "ERROR", "Arquivo nao encontrado")
        
        # Verificar diretorios
        essential_dirs = ["services", "scripts", "logs"]
        for dir_path in essential_dirs:
            if Path(dir_path).exists():
                self.add_result("Diretorios", dir_path, "OK", "Diretorio existe")
            else:
                if dir_path == "logs":
                    # Criar diretorio de logs se nao existir
                    Path(dir_path).mkdir(exist_ok=True)
                    self.add_result("Diretorios", dir_path, "OK", "Diretorio criado")
                else:
                    self.add_result("Diretorios", dir_path, "ERROR", "Diretorio nao encontrado")
    
    def check_restic_config(self):
        """Verifica configuracao do Restic"""
        try:
            credential_source = get_credential_source()
            config = load_restic_config(credential_source)
            
            # Verificar variaveis essenciais
            if config.storage_bucket:
                self.add_result("Configuracao", "STORAGE_BUCKET", "OK", config.storage_bucket)
            else:
                self.add_result("Configuracao", "STORAGE_BUCKET", "ERROR", "Nao configurado")
            
            if config.restic_password:
                self.add_result("Configuracao", "RESTIC_PASSWORD", "OK", "Configurado")
            else:
                self.add_result("Configuracao", "RESTIC_PASSWORD", "ERROR", "Nao configurado")
            
            if config.backup_source_dirs:
                self.add_result("Configuracao", "BACKUP_SOURCE_DIRS", "OK", 
                              f"{len(config.backup_source_dirs)} diretorios")
                
                # Verificar se diretorios de backup existem
                for dir_path in config.backup_source_dirs:
                    if Path(dir_path).exists():
                        self.add_result("Diretorios de Backup", dir_path, "OK", "Diretorio existe")
                    else:
                        self.add_result("Diretorios de Backup", dir_path, "WARNING", "Diretorio nao encontrado")
            else:
                self.add_result("Configuracao", "BACKUP_SOURCE_DIRS", "ERROR", "Nao configurado")
                
        except Exception as e:
            self.add_result("Configuracao", "Carregamento", "ERROR", str(e))
    
    def check_restic_repository(self):
        """Verifica acesso ao repositorio Restic"""
        try:
            credential_source = get_credential_source()
            repository, env, provider = load_restic_env(credential_source)
            
            client = ResticClient(
                repository=repository,
                env=env,
                provider=provider,
                credential_source=credential_source
            )
            client.check_repository_access()
            self.add_result("Repositorio", "Acesso", "OK", "Repositorio acessivel")
            
            # Tentar listar snapshots usando ResticClient
            try:
                snapshots = client.list_snapshots()
                self.add_result(
                    "Repositorio",
                    "Snapshots",
                    "OK",
                    f"{len(snapshots)} snapshots encontrados",
                )
            except Exception as e:
                self.add_result("Repositorio", "Snapshots", "WARNING", f"Erro: {e}")
                
        except Exception as e:
            self.add_result("Repositorio", "Acesso", "ERROR", str(e))
    
    def check_winfsp(self):
        """Verifica se WinFsp esta instalado (Windows)"""
        if os.name == 'nt':  # Windows
            winfsp_paths = [
                Path("C:/Program Files (x86)/WinFsp/bin/launchctl-x64.exe"),
                Path("C:/Program Files/WinFsp/bin/launchctl-x64.exe")
            ]
            
            winfsp_found = any(path.exists() for path in winfsp_paths)
            
            if winfsp_found:
                self.add_result("Sistema", "WinFsp", "OK", "WinFsp instalado (mount disponivel)")
            else:
                self.add_result("Sistema", "WinFsp", "WARNING", 
                              "WinFsp nao encontrado (mount nao disponivel)")
        else:
            # Linux/macOS - verificar FUSE
            if Path("/usr/bin/fusermount").exists() or Path("/bin/fusermount").exists():
                self.add_result("Sistema", "FUSE", "OK", "FUSE disponivel (mount disponivel)")
            else:
                self.add_result("Sistema", "FUSE", "WARNING", 
                              "FUSE nao encontrado (mount pode nao funcionar)")
    
    def check_virtual_environment(self):
        """Verifica ambiente virtual Python"""
        # Verificar multiplas formas de detectar ambiente virtual
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None
        )
        
        if in_venv:
            venv_path = os.environ.get('VIRTUAL_ENV', 'ambiente virtual')
            self.add_result("Python", "Ambiente Virtual", "OK", f"Executando em {venv_path}")
        else:
            self.add_result("Python", "Ambiente Virtual", "WARNING", 
                          "Nao esta em ambiente virtual (recomendado usar .venv)")
    
    def run_health_check(self) -> Dict:
        """Executa verificacao completa de saude"""
        print(" SafeStic - Verificacao de Saude do Sistema")
        print("=" * 50)
        
        # Verificar dependencias do sistema
        print("\n Verificando dependencias do sistema...")
        self.check_command("git", "Git")
        self.check_command("make", "Make")
        self.check_command("python", "Python")
        self.check_command("pip", "pip")
        self.check_command("restic", "Restic")
        
        # Verificar ambiente virtual
        print("\n Verificando ambiente Python...")
        self.check_virtual_environment()
        self.check_python_packages()
        
        # Verificar arquivos e diretorios
        print("\n Verificando arquivos e diretorios...")
        self.check_files_and_directories()
        
        # Verificar configuracao
        print("\n Verificando configuracao...")
        self.check_restic_config()
        
        # Verificar repositorio
        print("\n Verificando repositorio Restic...")
        self.check_restic_repository()
        
        # Verificar sistema de arquivos
        print("\n Verificando sistema de arquivos...")
        self.check_winfsp()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Gera relatorio final"""
        print("\n" + "=" * 50)
        print(" RELAToRIO DE SAuDE")
        print("=" * 50)
        
        # Contar status
        ok_count = sum(1 for r in self.results if r["status"] == "OK")
        warning_count = len(self.warnings)
        error_count = len(self.errors)
        total_count = len(self.results)
        
        print(f"\n OK: {ok_count}")
        print(f" Avisos: {warning_count}")
        print(f" Erros: {error_count}")
        print(f" Total: {total_count}")
        
        # Mostrar avisos
        if self.warnings:
            print("\n AVISOS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Mostrar erros
        if self.errors:
            print("\n ERROS:")
            for error in self.errors:
                print(f"  • {error}")
        
        # Status geral
        if error_count == 0:
            if warning_count == 0:
                print("\n SISTEMA SAUDaVEL - Tudo funcionando perfeitamente!")
                health_status = "HEALTHY"
            else:
                print("\n SISTEMA OK - Alguns avisos, mas funcional")
                health_status = "OK_WITH_WARNINGS"
        else:
            print("\n SISTEMA COM PROBLEMAS - Erros encontrados que precisam ser corrigidos")
            health_status = "UNHEALTHY"
        
        return {
            "status": health_status,
            "summary": {
                "ok": ok_count,
                "warnings": warning_count,
                "errors": error_count,
                "total": total_count
            },
            "results": self.results,
            "warnings": self.warnings,
            "errors": self.errors
        }

def main():
    """Funcao principal"""
    try:
        checker = HealthChecker()
        report = checker.run_health_check()
        
        # Salvar relatorio em arquivo
        report_file = Path("logs/health_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n Relatorio salvo em: {report_file}")
        
        # Codigo de saida baseado no status
        if report["status"] == "UNHEALTHY":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Erro na verificacao de saude: {e}")
        print(f" Erro na verificacao de saude: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
