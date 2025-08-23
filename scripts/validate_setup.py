#!/usr/bin/env python3
"""
Script de validacao completa do setup SafeStic
Valida se o sistema esta corretamente configurado e pronto para uso
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

class SetupValidator:
    """Validador de configuracao do sistema SafeStic"""
    
    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []
        self.critical_errors = []
    
    def add_result(self, category: str, item: str, status: str, details: str = "", critical: bool = False):
        """Adiciona resultado de validacao"""
        result = {
            "category": category,
            "item": item,
            "status": status,
            "details": details,
            "critical": critical
        }
        self.results.append(result)
        
        if status == "WARNING":
            self.warnings.append(f"{category} - {item}: {details}")
        elif status == "ERROR":
            if critical:
                self.critical_errors.append(f"{category} - {item}: {details}")
            else:
                self.errors.append(f"{category} - {item}: {details}")
    
    def validate_python_environment(self):
        """Valida ambiente Python"""
        print("\n Validando ambiente Python...")
        
        # Verificar versao do Python
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.add_result("Python", "Versao", "OK", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.add_result("Python", "Versao", "ERROR", 
                          f"Python {python_version.major}.{python_version.minor} (requer 3.8+)", critical=True)
        
        # Verificar ambiente virtual
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
                          "Nao esta em ambiente virtual (recomendado)")
        
        # Verificar pacotes criticos
        critical_packages = {
            "pydantic": ("pydantic", "Validacao de dados"),
            "python-dotenv": ("dotenv", "Carregamento de configuracoes"),
            "requests": ("requests", "Requisicoes HTTP"),
            "psutil": ("psutil", "Informacoes do sistema")
        }
        
        for package_name, (import_name, description) in critical_packages.items():
            try:
                __import__(import_name)
                self.add_result("Pacotes Python", package_name, "OK", description)
            except ImportError:
                self.add_result("Pacotes Python", package_name, "ERROR", 
                              f"{description} - Pacote nao encontrado", critical=True)
    
    def validate_system_dependencies(self):
        """Valida dependencias do sistema"""
        print("\n Validando dependencias do sistema...")
        
        critical_deps = {
            "restic": "Sistema de backup",
            "git": "Controle de versao"
        }
        
        optional_deps = {
            "make": "Automacao de tarefas",
            "pip": "Gerenciador de pacotes Python"
        }
        
        # Verificar dependencias criticas
        for cmd, description in critical_deps.items():
            if self._check_command_available(cmd):
                self.add_result("Dependencias Criticas", cmd, "OK", description)
            else:
                self.add_result("Dependencias Criticas", cmd, "ERROR", 
                              f"{description} - Comando nao encontrado", critical=True)
        
        # Verificar dependencias opcionais
        for cmd, description in optional_deps.items():
            if self._check_command_available(cmd):
                self.add_result("Dependencias Opcionais", cmd, "OK", description)
            else:
                self.add_result("Dependencias Opcionais", cmd, "WARNING", 
                              f"{description} - Comando nao encontrado")
    
    def _check_command_available(self, command: str) -> bool:
        """Verifica se um comando esta disponivel"""
        try:
            # Restic usa 'version' ao inves de '--version'
            if command == "restic":
                result = subprocess.run([command, "version"], 
                                      capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run([command, "--version"], 
                                      capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def validate_configuration_files(self):
        """Valida arquivos de configuracao"""
        print("\n Validando arquivos de configuracao...")
        
        # Arquivos criticos
        critical_files = {
            ".env": "Configuracoes de ambiente",
            "requirements.txt": "Dependencias Python",
            "services/__init__.py": "Modulo de servicos",
            "services/restic.py": "Configuracao Restic",
            "services/restic_client.py": "Cliente Restic"
        }
        
        # Arquivos opcionais
        optional_files = {
            "pyproject.toml": "Configuracao do projeto",
            "Makefile": "Automacao de tarefas",
            "README.md": "Documentacao"
        }
        
        # Verificar arquivos criticos
        for file_path, description in critical_files.items():
            if Path(file_path).exists():
                self.add_result("Arquivos Criticos", file_path, "OK", description)
            else:
                self.add_result("Arquivos Criticos", file_path, "ERROR", 
                              f"{description} - Arquivo nao encontrado", critical=True)
        
        # Verificar arquivos opcionais
        for file_path, description in optional_files.items():
            if Path(file_path).exists():
                self.add_result("Arquivos Opcionais", file_path, "OK", description)
            else:
                self.add_result("Arquivos Opcionais", file_path, "WARNING", 
                              f"{description} - Arquivo nao encontrado")
    
    def validate_restic_configuration(self):
        """Valida configuracao especifica do Restic"""
        print("\n Validando configuracao Restic...")
        
        try:
            credential_source = get_credential_source()
            config = load_restic_config(credential_source)
            
            # Verificar configuracoes criticas
            if config.storage_bucket:
                self.add_result("Configuracao Restic", "Repository", "OK", config.storage_bucket)
            else:
                self.add_result("Configuracao Restic", "Repository", "ERROR", 
                              "STORAGE_BUCKET nao configurado", critical=True)
            
            if config.restic_password:
                self.add_result("Configuracao Restic", "Password", "OK", "Senha configurada")
            else:
                self.add_result("Configuracao Restic", "Password", "ERROR", 
                              "RESTIC_PASSWORD nao configurado", critical=True)
            
            # Verificar diretorios de backup
            if config.backup_source_dirs:
                valid_dirs = []
                invalid_dirs = []
                
                for dir_path in config.backup_source_dirs:
                    if Path(dir_path).exists():
                        valid_dirs.append(dir_path)
                    else:
                        invalid_dirs.append(dir_path)
                
                if valid_dirs:
                    self.add_result("Diretorios de Backup", "Validos", "OK", 
                                  f"{len(valid_dirs)} diretorios validos")
                
                if invalid_dirs:
                    self.add_result("Diretorios de Backup", "Invalidos", "WARNING", 
                                  f"{len(invalid_dirs)} diretorios nao encontrados: {', '.join(invalid_dirs)}")
                
                if not valid_dirs:
                    self.add_result("Diretorios de Backup", "Configuracao", "ERROR", 
                                  "Nenhum diretorio valido para backup", critical=True)
            else:
                self.add_result("Configuracao Restic", "Source Dirs", "ERROR", 
                              "BACKUP_SOURCE_DIRS nao configurado", critical=True)
            
            # Verificar configuracoes opcionais
            if config.restic_excludes:
                self.add_result("Configuracao Restic", "Exclude Patterns", "OK", 
                              f"{len(config.restic_excludes)} padroes de exclusao")
            
            if config.retention_enabled:
                self.add_result("Configuracao Restic", "Retention", "OK", 
                              f"Retencao habilitada - {config.keep_daily}d/{config.keep_weekly}w/{config.keep_monthly}m/{config.keep_yearly}y")
            
        except Exception as e:
            self.add_result("Configuracao Restic", "Carregamento", "ERROR", 
                          f"Erro ao carregar configuracao: {e}", critical=True)
    
    def validate_repository_access(self):
        """Valida acesso ao repositorio Restic"""
        print("\n Validando acesso ao repositorio...")
        
        try:
            credential_source = get_credential_source()
            repository, env, provider = load_restic_env(credential_source)
            
            client = ResticClient(
                repository=repository,
                env=env,
                provider=provider,
                credential_source=credential_source
            )
            
            # Verificar se repositorio existe e e acessivel
            try:
                client.check_repository_access()
                self.add_result("Repositorio", "Acesso", "OK", "Repositorio acessivel")
                
                # Tentar operacao basica (listar snapshots)
                try:
                    snapshots = client.list_snapshots()
                    if snapshots:
                        self.add_result(
                            "Repositorio",
                            "Snapshots",
                            "OK",
                            f"Repositorio funcional com {len(snapshots)} snapshot(s)",
                        )
                    else:
                        self.add_result(
                            "Repositorio",
                            "Snapshots",
                            "OK",
                            "Repositorio vazio (pronto para primeiro backup)",
                        )
                except Exception:
                    self.add_result(
                        "Repositorio",
                        "Operacao",
                        "WARNING",
                        "Repositorio acessivel mas com problemas em operacoes",
                    )
                
            except Exception as e:
                if "repository does not exist" in str(e).lower():
                    self.add_result("Repositorio", "Inicializacao", "WARNING", 
                                  "Repositorio nao inicializado (execute 'make init' primeiro)")
                else:
                    self.add_result("Repositorio", "Acesso", "ERROR", 
                                  f"Erro de acesso: {e}", critical=True)
                
        except Exception as e:
            self.add_result("Repositorio", "Configuracao", "ERROR", 
                          f"Erro na configuracao do cliente: {e}", critical=True)
    
    def validate_mount_capability(self):
        """Valida capacidade de mount"""
        print("\n Validando capacidade de mount...")
        
        if os.name == 'nt':  # Windows
            winfsp_paths = [
                Path("C:/Program Files (x86)/WinFsp/bin/launchctl-x64.exe"),
                Path("C:/Program Files/WinFsp/bin/launchctl-x64.exe")
            ]
            
            winfsp_found = any(path.exists() for path in winfsp_paths)
            
            if winfsp_found:
                self.add_result("Mount", "WinFsp", "OK", "WinFsp instalado - mount disponivel")
                
                # Verificar se o servico esta rodando
                try:
                    result = subprocess.run(["sc", "query", "WinFsp.Launcher"], 
                                          capture_output=True, text=True)
                    if "RUNNING" in result.stdout:
                        self.add_result("Mount", "Servico WinFsp", "OK", "Servico WinFsp rodando")
                    else:
                        self.add_result("Mount", "Servico WinFsp", "WARNING", 
                                      "Servico WinFsp nao esta rodando")
                except Exception:
                    self.add_result("Mount", "Servico WinFsp", "WARNING", 
                                  "Nao foi possivel verificar status do servico")
            else:
                self.add_result("Mount", "WinFsp", "ERROR", 
                              "WinFsp nao encontrado - mount nao funcionara")
        else:
            # Linux/macOS - verificar FUSE
            fuse_paths = ["/usr/bin/fusermount", "/bin/fusermount", "/usr/local/bin/fusermount"]
            fuse_found = any(Path(path).exists() for path in fuse_paths)
            
            if fuse_found:
                self.add_result("Mount", "FUSE", "OK", "FUSE disponivel - mount disponivel")
            else:
                self.add_result("Mount", "FUSE", "WARNING", 
                              "FUSE nao encontrado - mount pode nao funcionar")
    
    def validate_directory_structure(self):
        """Valida estrutura de diretorios"""
        print("\n Validando estrutura de diretorios...")
        
        # Diretorios essenciais
        essential_dirs = {
            "services": "Modulos de servicos",
            "scripts": "Scripts de automacao"
        }
        
        # Diretorios que serao criados automaticamente
        auto_created_dirs = {
            "logs": "Arquivos de log",
            "restore": "Diretorio de restore (criado quando necessario)"
        }
        
        # Verificar diretorios essenciais
        for dir_path, description in essential_dirs.items():
            if Path(dir_path).exists() and Path(dir_path).is_dir():
                self.add_result("Estrutura", dir_path, "OK", description)
            else:
                self.add_result("Estrutura", dir_path, "ERROR", 
                              f"{description} - Diretorio nao encontrado", critical=True)
        
        # Verificar/criar diretorios automaticos
        for dir_path, description in auto_created_dirs.items():
            path_obj = Path(dir_path)
            if path_obj.exists():
                self.add_result("Estrutura", dir_path, "OK", description)
            else:
                try:
                    path_obj.mkdir(exist_ok=True)
                    self.add_result("Estrutura", dir_path, "OK", f"{description} - Criado automaticamente")
                except Exception as e:
                    self.add_result("Estrutura", dir_path, "WARNING", 
                                  f"Nao foi possivel criar {dir_path}: {e}")
    
    def run_validation(self) -> Dict:
        """Executa validacao completa do setup"""
        print(" SafeStic - Validacao Completa do Setup")
        print("=" * 50)
        
        # Executar todas as validacoes
        self.validate_python_environment()
        self.validate_system_dependencies()
        self.validate_directory_structure()
        self.validate_configuration_files()
        self.validate_restic_configuration()
        self.validate_repository_access()
        self.validate_mount_capability()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Gera relatorio final de validacao"""
        print("\n" + "=" * 50)
        print("📋 RELAToRIO DE VALIDAcaO")
        print("=" * 50)
        
        # Contar status
        ok_count = sum(1 for r in self.results if r["status"] == "OK")
        warning_count = len(self.warnings)
        error_count = len(self.errors)
        critical_count = len(self.critical_errors)
        total_count = len(self.results)
        
        print(f"\n Validacoes OK: {ok_count}")
        print(f" Avisos: {warning_count}")
        print(f" Erros: {error_count}")
        print(f" Erros Criticos: {critical_count}")
        print(f" Total: {total_count}")
        
        # Mostrar erros criticos primeiro
        if self.critical_errors:
            print("\n ERROS CRiTICOS (impedem funcionamento):")
            for error in self.critical_errors:
                print(f"  • {error}")
        
        # Mostrar erros nao criticos
        if self.errors:
            print("\n ERROS:")
            for error in self.errors:
                print(f"  • {error}")
        
        # Mostrar avisos
        if self.warnings:
            print("\n AVISOS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Determinar status final
        if critical_count > 0:
            print("\n SETUP INVaLIDO - Erros criticos impedem o funcionamento")
            print("   Corrija os erros criticos antes de usar o sistema.")
            validation_status = "INVALID"
        elif error_count > 0:
            print("\n SETUP PARCIALMENTE VaLIDO - Alguns recursos podem nao funcionar")
            print("   O sistema pode funcionar, mas com limitacoes.")
            validation_status = "PARTIAL"
        elif warning_count > 0:
            print("\n SETUP VaLIDO COM AVISOS - Sistema funcional")
            print("   Considere resolver os avisos para melhor experiencia.")
            validation_status = "VALID_WITH_WARNINGS"
        else:
            print("\n SETUP COMPLETAMENTE VaLIDO - Sistema pronto para uso!")
            print("   Todos os componentes estao configurados corretamente.")
            validation_status = "FULLY_VALID"
        
        return {
            "status": validation_status,
            "summary": {
                "ok": ok_count,
                "warnings": warning_count,
                "errors": error_count,
                "critical_errors": critical_count,
                "total": total_count
            },
            "results": self.results,
            "warnings": self.warnings,
            "errors": self.errors,
            "critical_errors": self.critical_errors
        }

def main():
    """Funcao principal"""
    try:
        validator = SetupValidator()
        report = validator.run_validation()
        
        # Salvar relatorio em arquivo
        report_file = Path("logs/validation_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatorio salvo em: {report_file}")
        
        # Codigo de saida baseado no status
        if report["status"] == "INVALID":
            sys.exit(2)  # Erros criticos
        elif report["status"] == "PARTIAL":
            sys.exit(1)  # Erros nao criticos
        else:
            sys.exit(0)  # OK ou apenas avisos
            
    except Exception as e:
        logger.error(f"Erro na validacao do setup: {e}")
        print(f" Erro na validacao do setup: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
