#!/usr/bin/env python3
"""
Script de verificação de saúde do Safestic
Verifica todos os componentes e configurações do sistema
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_status(condition, success_msg, error_msg):
    """Verifica condição e imprime status"""
    if condition:
        print(f"✅ {success_msg}")
        return True
    else:
        print(f"❌ {error_msg}")
        return False

def check_warning(condition, success_msg, warning_msg):
    """Verifica condição e imprime aviso"""
    if condition:
        print(f"✅ {success_msg}")
        return True
    else:
        print(f"⚠️  {warning_msg}")
        return False

def load_config():
    """Carrega configurações do .env"""
    env_path = Path('.env')
    if not env_path.exists():
        return False, "Arquivo .env não encontrado"
    
    try:
        load_dotenv(env_path)
        return True, "Configuração carregada"
    except Exception as e:
        return False, f"Erro ao carregar .env: {e}"

def check_dependencies():
    """Verifica dependências do sistema"""
    print_section("Dependências do Sistema")
    
    dependencies = {
        'python': ['python', '--version'],
        'restic': ['restic', 'version'],
        'make': ['make', '--version'] if os.name != 'nt' else ['make', '--version'],
        'git': ['git', '--version']
    }
    
    results = {}
    
    for name, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✅ {name}: {version}")
                results[name] = True
            else:
                print(f"❌ {name}: Erro na execução")
                results[name] = False
        except FileNotFoundError:
            print(f"❌ {name}: Não encontrado")
            results[name] = False
        except subprocess.TimeoutExpired:
            print(f"❌ {name}: Timeout")
            results[name] = False
        except Exception as e:
            print(f"❌ {name}: {e}")
            results[name] = False
    
    return results

def check_configuration():
    """Verifica configuração do Safestic"""
    print_section("Configuração")
    
    # Verificar arquivo .env
    config_ok, config_msg = load_config()
    check_status(config_ok, config_msg, config_msg)
    
    if not config_ok:
        return False
    
    # Verificar variáveis obrigatórias
    required_vars = {
        'STORAGE_PROVIDER': 'Provedor de armazenamento',
        'STORAGE_BUCKET': 'Bucket/caminho de armazenamento',
        'RESTIC_PASSWORD': 'Senha do repositório',
        'BACKUP_SOURCE_DIRS': 'Diretórios para backup'
    }
    
    config_score = 0
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {desc}: Configurado")
            config_score += 1
        else:
            print(f"❌ {desc}: Não configurado ({var})")
    
    # Verificar configurações específicas do provedor
    provider = os.getenv('STORAGE_PROVIDER', '').lower()
    if provider == 'aws':
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        for var in aws_vars:
            value = os.getenv(var)
            check_status(value and value.strip(), 
                        f"AWS {var}: Configurado", 
                        f"AWS {var}: Não configurado")
    elif provider == 'azure':
        azure_vars = ['AZURE_ACCOUNT_NAME', 'AZURE_ACCOUNT_KEY']
        for var in azure_vars:
            value = os.getenv(var)
            check_status(value and value.strip(), 
                        f"Azure {var}: Configurado", 
                        f"Azure {var}: Não configurado")
    elif provider == 'gcp':
        gcp_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        check_status(gcp_creds and Path(gcp_creds).exists(), 
                    "GCP: Credenciais configuradas", 
                    "GCP: Credenciais não encontradas")
    
    return config_score == len(required_vars)

def check_directories():
    """Verifica diretórios de backup e logs"""
    print_section("Diretórios")
    
    # Verificar diretórios de origem
    source_dirs = os.getenv('BACKUP_SOURCE_DIRS', '').split(',')
    source_ok = True
    
    for dir_path in source_dirs:
        dir_path = dir_path.strip()
        if dir_path:
            exists = Path(dir_path).exists()
            check_status(exists, f"Origem: {dir_path}", f"Origem não encontrada: {dir_path}")
            if not exists:
                source_ok = False
    
    # Verificar diretório de logs
    log_dir = os.getenv('LOG_DIR', './logs')
    log_exists = Path(log_dir).exists()
    check_status(log_exists, f"Logs: {log_dir}", f"Diretório de logs não existe: {log_dir}")
    
    # Verificar diretório de restore
    restore_dir = os.getenv('RESTORE_TARGET_DIR', './restore')
    restore_parent = Path(restore_dir).parent
    restore_ok = restore_parent.exists()
    check_status(restore_ok, f"Restore (pai): {restore_parent}", f"Diretório pai do restore não existe: {restore_parent}")
    
    return source_ok and log_exists and restore_ok

def check_repository_access():
    """Verifica acesso ao repositório"""
    print_section("Repositório")
    
    try:
        # Construir ambiente
        env = os.environ.copy()
        provider = os.getenv('STORAGE_PROVIDER', '').lower()
        bucket = os.getenv('STORAGE_BUCKET', '')
        
        if provider == 'local':
            env['RESTIC_REPOSITORY'] = bucket
        elif provider == 'aws':
            env['RESTIC_REPOSITORY'] = f's3:{bucket}'
        elif provider == 'azure':
            account = os.getenv('AZURE_ACCOUNT_NAME')
            env['RESTIC_REPOSITORY'] = f'azure:{account}:{bucket}'
        elif provider == 'gcp':
            env['RESTIC_REPOSITORY'] = f'gs:{bucket}'
        
        env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
        
        # Testar acesso
        result = subprocess.run(
            ['restic', 'cat', 'config'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Repositório: Acessível")
            
            # Obter estatísticas básicas
            stats_result = subprocess.run(
                ['restic', 'stats', '--json'],
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if stats_result.returncode == 0:
                try:
                    stats = json.loads(stats_result.stdout)
                    total_size = stats.get('total_size', 0)
                    total_file_count = stats.get('total_file_count', 0)
                    print(f"📊 Tamanho total: {total_size:,} bytes")
                    print(f"📊 Total de arquivos: {total_file_count:,}")
                except:
                    pass
            
            return True
        else:
            print(f"❌ Repositório: Inacessível - {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Repositório: Timeout no acesso")
        return False
    except Exception as e:
        print(f"❌ Repositório: Erro - {e}")
        return False

def check_recent_backups():
    """Verifica backups recentes"""
    print_section("Backups Recentes")
    
    try:
        # Construir ambiente
        env = os.environ.copy()
        provider = os.getenv('STORAGE_PROVIDER', '').lower()
        bucket = os.getenv('STORAGE_BUCKET', '')
        
        if provider == 'local':
            env['RESTIC_REPOSITORY'] = bucket
        elif provider == 'aws':
            env['RESTIC_REPOSITORY'] = f's3:{bucket}'
        elif provider == 'azure':
            account = os.getenv('AZURE_ACCOUNT_NAME')
            env['RESTIC_REPOSITORY'] = f'azure:{account}:{bucket}'
        elif provider == 'gcp':
            env['RESTIC_REPOSITORY'] = f'gs:{bucket}'
        
        env['RESTIC_PASSWORD'] = os.getenv('RESTIC_PASSWORD', '')
        
        # Listar snapshots recentes
        result = subprocess.run(
            ['restic', 'snapshots', '--json', '--last', '5'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                snapshots = json.loads(result.stdout)
                if snapshots:
                    print(f"✅ Encontrados {len(snapshots)} snapshots recentes")
                    
                    # Verificar backup mais recente
                    latest = snapshots[0]
                    backup_time = datetime.fromisoformat(latest['time'].replace('Z', '+00:00'))
                    now = datetime.now(backup_time.tzinfo)
                    age = now - backup_time
                    
                    print(f"📅 Último backup: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"⏰ Idade: {age.days} dias, {age.seconds//3600} horas")
                    
                    # Verificar se backup é muito antigo
                    if age > timedelta(days=7):
                        print("⚠️  Último backup tem mais de 7 dias")
                        return False
                    elif age > timedelta(days=2):
                        print("⚠️  Último backup tem mais de 2 dias")
                        return True
                    else:
                        print("✅ Backup recente")
                        return True
                else:
                    print("❌ Nenhum snapshot encontrado")
                    return False
            except Exception as e:
                print(f"❌ Erro ao processar snapshots: {e}")
                return False
        else:
            print(f"❌ Erro ao listar snapshots: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao verificar backups")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar backups: {e}")
        return False

def check_log_files():
    """Verifica arquivos de log"""
    print_section("Arquivos de Log")
    
    log_dir = Path(os.getenv('LOG_DIR', './logs'))
    
    if not log_dir.exists():
        print("❌ Diretório de logs não existe")
        return False
    
    # Verificar logs recentes
    log_files = list(log_dir.glob('*.log'))
    
    if not log_files:
        print("⚠️  Nenhum arquivo de log encontrado")
        return False
    
    print(f"✅ Encontrados {len(log_files)} arquivos de log")
    
    # Verificar log mais recente
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    mod_time = datetime.fromtimestamp(latest_log.stat().st_mtime)
    age = datetime.now() - mod_time
    
    print(f"📄 Log mais recente: {latest_log.name}")
    print(f"📅 Modificado: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Idade: {age.days} dias, {age.seconds//3600} horas")
    
    # Verificar erros recentes
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
            error_count = content.lower().count('error')
            warning_count = content.lower().count('warning')
            
            if error_count > 0:
                print(f"⚠️  {error_count} erros encontrados no log")
            if warning_count > 0:
                print(f"⚠️  {warning_count} avisos encontrados no log")
            
            if error_count == 0 and warning_count == 0:
                print("✅ Nenhum erro ou aviso no log mais recente")
                
    except Exception as e:
        print(f"⚠️  Erro ao ler log: {e}")
    
    return True

def generate_health_report():
    """Gera relatório de saúde completo"""
    print_header("RELATÓRIO DE SAÚDE - SAFESTIC")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Sistema: {os.name}")
    print(f"📁 Diretório: {Path.cwd()}")
    
    # Executar verificações
    checks = {
        'Dependências': check_dependencies(),
        'Configuração': check_configuration(),
        'Diretórios': check_directories(),
        'Repositório': check_repository_access(),
        'Backups': check_recent_backups(),
        'Logs': check_log_files()
    }
    
    # Resumo final
    print_section("Resumo Final")
    
    total_checks = 0
    passed_checks = 0
    
    for check_name, result in checks.items():
        if isinstance(result, dict):  # Dependências retorna dict
            total_deps = len(result)
            passed_deps = sum(1 for v in result.values() if v)
            status = "✅" if passed_deps == total_deps else "⚠️" if passed_deps > 0 else "❌"
            print(f"{status} {check_name}: {passed_deps}/{total_deps}")
            total_checks += total_deps
            passed_checks += passed_deps
        else:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'OK' if result else 'FALHA'}")
            total_checks += 1
            if result:
                passed_checks += 1
    
    print(f"\n📊 Score geral: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    if passed_checks == total_checks:
        print("🎉 Sistema totalmente saudável!")
        return 0
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  Sistema majoritariamente saudável com alguns problemas")
        return 1
    else:
        print("❌ Sistema com problemas significativos")
        return 2

def main():
    """Função principal"""
    return generate_health_report()

if __name__ == '__main__':
    sys.exit(main())