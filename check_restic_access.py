import logging
import sys

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError, load_env_and_get_credential_source


def check_restic_access() -> None:
    """Verifica se o Restic esta instalado e se o repositorio esta acessivel.
    
    Utiliza o ResticClient para verificar acesso ao repositorio com retry automatico e tratamento de erros.
    """
    credential_source = load_env_and_get_credential_source()
    with ResticScript("check_restic_access", credential_source=credential_source) as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log("=== Verificando acesso ao repositorio Restic ===")
        restic_password = ctx.env.get("RESTIC_PASSWORD")

        print("Verificando variaveis essenciais do .env")

        def print_status(name: str, result: bool) -> None:
            line = f"{name.ljust(30)}: {'OK' if result else 'FALHA'}"
            print(line)
            ctx.log(line)

        print_status("RESTIC_REPOSITORY", bool(ctx.repository))
        print_status("RESTIC_PASSWORD", bool(restic_password))

        if ctx.provider == "aws":
            print_status("AWS_ACCESS_KEY_ID", bool(ctx.env.get("AWS_ACCESS_KEY_ID")))
            print_status(
                "AWS_SECRET_ACCESS_KEY",
                bool(ctx.env.get("AWS_SECRET_ACCESS_KEY")),
            )
        elif ctx.provider == "azure":
            print_status("AZURE_ACCOUNT_NAME", bool(ctx.env.get("AZURE_ACCOUNT_NAME")))
            print_status("AZURE_ACCOUNT_KEY", bool(ctx.env.get("AZURE_ACCOUNT_KEY")))
        elif ctx.provider == "gcp":
            print_status("GOOGLE_PROJECT_ID", bool(ctx.env.get("GOOGLE_PROJECT_ID")))
            print_status(
                "GOOGLE_APPLICATION_CREDENTIALS",
                bool(ctx.env.get("GOOGLE_APPLICATION_CREDENTIALS")),
            )

        if not ctx.repository or not restic_password:
            ctx.log("[FATAL] Variaveis obrigatorias estao ausentes. Abortando.")
            print("\n[FATAL] Variaveis obrigatorias estao ausentes. Abortando.")
            sys.exit(1)

        try:
            # Criar cliente Restic com retry usando o ambiente já carregado
            client = ResticClient(
                max_attempts=3,
                repository=ctx.repository,
                env=ctx.env,
                provider=ctx.provider,
                credential_source=credential_source
            )
            
            # Verificar se o Restic esta disponivel
            ctx.log("\nVerificando se 'restic' esta disponivel no PATH...")
            if not client.check_restic_installed():
                ctx.log("Restic nao encontrado ou com erro")
                sys.exit(1)
            ctx.log("Restic esta instalado e acessivel.")
            print("Restic esta instalado e acessivel.")
            
            # Testar acesso ao repositorio
            ctx.log("\nTestando acesso ao repositorio...")
            if client.check_repository_access():
                ctx.log("Acesso ao repositorio bem-sucedido.")
                print("Acesso ao repositorio bem-sucedido.")
            else:
                print("Nao foi possivel acessar o repositorio.")
                ctx.log("Tentando inicializar...")
                if client.init_repository():
                    ctx.log("Repositorio foi inicializado com sucesso!")
                    print("Repositorio foi inicializado com sucesso!")
                else:
                    ctx.log("Falha ao inicializar o repositorio")
                    sys.exit(1)
                    
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    check_restic_access()

