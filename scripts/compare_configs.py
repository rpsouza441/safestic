#!/usr/bin/env python3
"""
Script para comparar configurações entre Windows e Linux

Este script ajuda a identificar diferenças de configuração que podem
causar problemas ao migrar entre sistemas operacionais.
"""

import os
import sys
import json
import platform
from pathlib import Path
from dotenv import load_dotenv
from services.env import get_credential_source

def get_system_info():
    """Coleta informações do sistema."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "python_version": sys.version,
        "hostname": platform.node(),
        "user": os.getenv("USER") or os.getenv("USERNAME"),
        "home": str(Path.home()),
        "cwd": os.getcwd(),
        "path_separator": os.sep,
        "env_path": os.getenv("PATH", "").split(os.pathsep)[:5]  # Primeiros 5 paths
    }

def get_env_variables():
    """Coleta variáveis de ambiente relevantes."""
    load_dotenv()
    
    # Variáveis importantes para SafeStic
    important_vars = [
        "RESTIC_REPOSITORY",
        "RESTIC_PASSWORD",
        "STORAGE_PROVIDER",
        "STORAGE_BUCKET",
        "AZURE_ACCOUNT_NAME",
        "AZURE_ACCOUNT_KEY",
        "CREDENTIAL_SOURCE",
        "BACKUP_SOURCE",
        "RESTORE_TARGET",
        "LANG",
        "LC_ALL",
        "PYTHONPATH",
        "VIRTUAL_ENV"
    ]
    
    env_vars = {}
    for var in important_vars:
        value = get_credential_source() if var == "CREDENTIAL_SOURCE" else os.getenv(var)
        if value:
            # Mascarar credenciais sensíveis
            if any(sensitive in var.upper() for sensitive in ["PASSWORD", "KEY", "SECRET"]):
                env_vars[var] = f"***MASKED*** ({len(value)} chars)"
            else:
                env_vars[var] = value
        else:
            env_vars[var] = None
    
    return env_vars

def get_file_info():
    """Coleta informações sobre arquivos importantes."""
    files_to_check = [
        ".env",
        "Makefile",
        "pyproject.toml",
        "requirements.txt",
        "check_restic_access.py",
        "validate_config.py"
    ]
    
    file_info = {}
    for filename in files_to_check:
        path = Path(filename)
        if path.exists():
            stat = path.stat()
            file_info[filename] = {
                "exists": True,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:],
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK)
            }
        else:
            file_info[filename] = {"exists": False}
    
    return file_info

def get_python_packages():
    """Lista pacotes Python instalados (principais)."""
    important_packages = [
        "python-dotenv",
        "keyring",
        "pythonjsonlogger",
        "requests",
        "cryptography"
    ]
    
    packages = {}
    for package in important_packages:
        try:
            # Tentar importar o pacote
            module_name = package.replace("-", "_")
            module = __import__(module_name)
            
            # Tentar obter versão
            version = "unknown"
            if hasattr(module, "__version__"):
                version = module.__version__
            elif hasattr(module, "version"):
                version = module.version
            
            packages[package] = {
                "installed": True,
                "version": version,
                "location": getattr(module, "__file__", "unknown")
            }
        except ImportError:
            packages[package] = {"installed": False}
        except Exception as e:
            packages[package] = {"installed": True, "error": str(e)}
    
    return packages

def get_network_info():
    """Coleta informações de rede básicas."""
    import socket
    
    try:
        # Obter hostname e IP local
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Testar conectividade básica
        connectivity = {}
        test_hosts = [
            ("google.com", 80),
            ("azure.microsoft.com", 443),
            ("login.microsoftonline.com", 443)
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                connectivity[f"{host}:{port}"] = result == 0
            except Exception:
                connectivity[f"{host}:{port}"] = False
        
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "connectivity": connectivity
        }
    except Exception as e:
        return {"error": str(e)}

def generate_config_report():
    """Gera relatório completo da configuração."""
    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "system": get_system_info(),
        "environment": get_env_variables(),
        "files": get_file_info(),
        "packages": get_python_packages(),
        "network": get_network_info()
    }
    
    return report

def save_report(report, filename=None):
    """Salva o relatório em arquivo JSON."""
    if not filename:
        system = report["system"]["os"].lower()
        timestamp = report["timestamp"].replace(":", "-").split(".")[0]
        filename = f"config_report_{system}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return filename

def compare_reports(report1_file, report2_file):
    """Compara dois relatórios de configuração."""
    with open(report1_file, "r", encoding="utf-8") as f:
        report1 = json.load(f)
    
    with open(report2_file, "r", encoding="utf-8") as f:
        report2 = json.load(f)
    
    print(f"\n{'='*60}")
    print(" COMPARAÇÃO DE CONFIGURAÇÕES")
    print(f"{'='*60}")
    
    print(f"\nRelatório 1: {report1['system']['os']} - {report1['timestamp']}")
    print(f"Relatório 2: {report2['system']['os']} - {report2['timestamp']}")
    
    # Comparar sistemas
    print(f"\n{'='*40}")
    print(" DIFERENÇAS DE SISTEMA")
    print(f"{'='*40}")
    
    system_keys = ["os", "architecture", "python_version"]
    for key in system_keys:
        val1 = report1["system"].get(key, "N/A")
        val2 = report2["system"].get(key, "N/A")
        if val1 != val2:
            print(f"{key}:")
            print(f"  {report1['system']['os']}: {val1}")
            print(f"  {report2['system']['os']}: {val2}")
    
    # Comparar variáveis de ambiente
    print(f"\n{'='*40}")
    print(" DIFERENÇAS DE AMBIENTE")
    print(f"{'='*40}")
    
    all_env_keys = set(report1["environment"].keys()) | set(report2["environment"].keys())
    for key in sorted(all_env_keys):
        val1 = report1["environment"].get(key)
        val2 = report2["environment"].get(key)
        
        if val1 != val2:
            print(f"{key}:")
            print(f"  {report1['system']['os']}: {val1 or 'NÃO DEFINIDA'}")
            print(f"  {report2['system']['os']}: {val2 or 'NÃO DEFINIDA'}")
    
    # Comparar pacotes
    print(f"\n{'='*40}")
    print(" DIFERENÇAS DE PACOTES")
    print(f"{'='*40}")
    
    all_packages = set(report1["packages"].keys()) | set(report2["packages"].keys())
    for package in sorted(all_packages):
        pkg1 = report1["packages"].get(package, {})
        pkg2 = report2["packages"].get(package, {})
        
        installed1 = pkg1.get("installed", False)
        installed2 = pkg2.get("installed", False)
        version1 = pkg1.get("version", "unknown")
        version2 = pkg2.get("version", "unknown")
        
        if installed1 != installed2 or (installed1 and installed2 and version1 != version2):
            print(f"{package}:")
            if installed1:
                print(f"  {report1['system']['os']}: {version1}")
            else:
                print(f"  {report1['system']['os']}: NÃO INSTALADO")
            
            if installed2:
                print(f"  {report2['system']['os']}: {version2}")
            else:
                print(f"  {report2['system']['os']}: NÃO INSTALADO")
    
    # Comparar conectividade
    print(f"\n{'='*40}")
    print(" DIFERENÇAS DE CONECTIVIDADE")
    print(f"{'='*40}")
    
    conn1 = report1["network"].get("connectivity", {})
    conn2 = report2["network"].get("connectivity", {})
    
    all_hosts = set(conn1.keys()) | set(conn2.keys())
    for host in sorted(all_hosts):
        status1 = conn1.get(host, False)
        status2 = conn2.get(host, False)
        
        if status1 != status2:
            print(f"{host}:")
            print(f"  {report1['system']['os']}: {'✅ OK' if status1 else '❌ FALHA'}")
            print(f"  {report2['system']['os']}: {'✅ OK' if status2 else '❌ FALHA'}")

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comparar configurações entre sistemas")
    parser.add_argument("--generate", action="store_true", help="Gerar relatório do sistema atual")
    parser.add_argument("--compare", nargs=2, metavar=("FILE1", "FILE2"), help="Comparar dois relatórios")
    parser.add_argument("--output", help="Nome do arquivo de saída")
    
    args = parser.parse_args()
    
    if args.generate:
        print("Gerando relatório de configuração...")
        report = generate_config_report()
        filename = save_report(report, args.output)
        print(f"Relatório salvo em: {filename}")
        
        # Mostrar resumo
        print(f"\nResumo:")
        print(f"  Sistema: {report['system']['os']} {report['system']['architecture']}")
        print(f"  Python: {report['system']['python_version'].split()[0]}")
        print(f"  Diretório: {report['system']['cwd']}")
        
        env_count = sum(1 for v in report['environment'].values() if v is not None)
        print(f"  Variáveis definidas: {env_count}/{len(report['environment'])}")
        
        pkg_count = sum(1 for p in report['packages'].values() if p.get('installed', False))
        print(f"  Pacotes instalados: {pkg_count}/{len(report['packages'])}")
        
    elif args.compare:
        compare_reports(args.compare[0], args.compare[1])
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()