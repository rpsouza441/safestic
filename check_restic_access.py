import logging
import os
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def check_restic_access() -> None:
    """Verifica se o Restic está instalado e se o repositório está acessível.
    
    Utiliza o ResticClient para verificar acesso ao repositório com retry automático e tratamento de erros.
    """
    with ResticScript("check_restic_access") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log("=== Verificando acesso ao repositório Restic ===")
        restic_password = os.getenv("RESTIC_PASSWORD")

        print("🔍 Verificando variáveis essenciais do .env")

        def print_status(name: str, result: bool) -> None:
            line = f"{name.ljust(30)}: {'OK' if result else '❌ FALHA'}"
            print(line)
            ctx.log(line)

        print_status("RESTIC_REPOSITORY", bool(ctx.repository))
        print_status("RESTIC_PASSWORD", bool(restic_password))

        if ctx.provider == "aws":
            print_status("AWS_ACCESS_KEY_ID", bool(os.getenv("AWS_ACCESS_KEY_ID")))
            print_status(
                "AWS_SECRET_ACCESS_KEY",
                bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
            )
        elif ctx.provider == "azure":
            print_status("AZURE_ACCOUNT_NAME", bool(os.getenv("AZURE_ACCOUNT_NAME")))
            print_status("AZURE_ACCOUNT_KEY", bool(os.getenv("AZURE_ACCOUNT_KEY")))
        elif ctx.provider == "gcp":
            print_status("GOOGLE_PROJECT_ID", bool(os.getenv("GOOGLE_PROJECT_ID")))
            print_status(
                "GOOGLE_APPLICATION_CREDENTIALS",
                bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
            )

        if not ctx.repository or not restic_password:
            ctx.log("[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
            print("\n[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
            sys.exit(1)

        try:
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3)
            
            # Verificar se o Restic está disponível
            ctx.log("\nVerificando se 'restic' está disponível no PATH...")
            if not client.check_restic_installed():
                ctx.log("Restic não encontrado ou com erro")
                sys.exit(1)
            ctx.log("Restic está instalado e acessível.")
            print("Restic está instalado e acessível.")
            
            # Testar acesso ao repositório
            ctx.log("\nTestando acesso ao repositório...")
            if client.check_repository_access():
                ctx.log("Acesso ao repositório bem-sucedido.")
                print("Acesso ao repositório bem-sucedido.")
            else:
                print("Não foi possível acessar o repositório.")
                ctx.log("Tentando inicializar...")
                if client.init_repository():
                    ctx.log("Repositório foi inicializado com sucesso!")
                    print("Repositório foi inicializado com sucesso!")
                else:
                    ctx.log("Falha ao inicializar o repositório")
                    sys.exit(1)
                    
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    check_restic_access()
