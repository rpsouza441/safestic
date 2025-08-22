import argparse
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from services.script import ResticScript
from services.restic_client import ResticClient, ResticError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista os arquivos contidos em um snapshot especifico",
    )
    parser.add_argument("--id", default="latest", help="ID do snapshot (default: latest)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Formato de saida (default: text)")
    parser.add_argument("--output", help="Arquivo de saida (opcional)")
    parser.add_argument("--pretty", action="store_true", help="Formatacao legivel para humanos")
    return parser.parse_args()


def main(snapshot_id: str, output_format: str = "text", output_file: str = None, pretty: bool = False) -> None:
    # Usar ResticScript que já carrega as credenciais corretamente
    with ResticScript("list_snapshot_files") as ctx:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        
        ctx.log(f"Listando arquivos do snapshot '{snapshot_id}'...")
        
        try:
            # Criar cliente Restic com retry
            client = ResticClient(max_attempts=3, credential_source=credential_source)
            
            # Listar arquivos do snapshot
            files_output = client.list_snapshot_files(snapshot_id)
            
            if not files_output:
                ctx.log("Nenhum arquivo encontrado no snapshot.")
                return
            
            # Processar saida baseado no formato
            if output_format == "json":
                # files_output ja e uma lista de strings
                result = {
                    "snapshot_id": snapshot_id,
                    "total_files": len(files_output),
                    "files": files_output
                }
                
                if pretty:
                    output_content = json.dumps(result, indent=2, ensure_ascii=False)
                else:
                    output_content = json.dumps(result, ensure_ascii=False)
            else:
                # Formato texto com melhor legibilidade
                if pretty:
                    output_content = f"Snapshot ID: {snapshot_id}\n"
                    output_content += f"Total de arquivos: {len(files_output)}\n"
                    output_content += "\nArquivos:\n"
                    output_content += "\n".join(f"  {file}" for file in files_output)
                else:
                    output_content = "\n".join(files_output)
            
            # Salvar em arquivo ou exibir na tela
            if output_file:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                ctx.log(f"Resultado salvo em: {output_file}")
            else:
                print(output_content)
                
        except ResticError as exc:
            ctx.log(f"[ERRO] {exc}")
            sys.exit(1)
        except Exception as exc:
            ctx.log(f"[ERRO] Uma falha inesperada ocorreu: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    main(args.id, args.format, args.output, args.pretty)

