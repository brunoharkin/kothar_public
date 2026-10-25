"""
Kothar Configuration Loader
Carrega as configurações do operador e caminhos dinâmicos com fallback seguro.
"""
import os
import json
from pathlib import Path

def get_kothar_config():
    """
    Retorna a configuração resolvida do Kothar.
    Prioridade:
    1. ~/.kothar/config.json
    2. configuracao/kothar-config.json (se existir)
    3. Variáveis de ambiente
    4. Defaults genéricos
    """
    home = Path.home()
    user_config_path = home / ".kothar" / "config.json"
    
    # Caminho base do repositório
    repo_root = Path(__file__).resolve().parent.parent.parent
    local_config_path = repo_root / "configuracao" / "kothar-config.json"
    
    config = {}
    
    if user_config_path.exists():
        try:
            with open(user_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass
    elif local_config_path.exists():
        try:
            with open(local_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    # Extrai ou aplica defaults dinâmicos
    operador = config.get("operador", {})
    nome_operador = os.getenv("KOTHAR_USER_NAME", operador.get("nome", os.getenv("USER", "Operador")))
    empresa = os.getenv("KOTHAR_ORG_NAME", operador.get("empresa", "Workspace"))
    cargo = operador.get("cargo", "Desenvolvedor")

    caminhos = config.get("caminhos", {})
    kothar_dir = Path(os.getenv("KOTHAR_DIR", caminhos.get("kothar_dir", str(repo_root))))
    vault_dir = Path(os.getenv("VAULT_DIR", caminhos.get("vault_dir", str(home / "Cofre"))))
    chroma_dir = Path(os.getenv("CHROMA_DATA_DIR", caminhos.get("chroma_dir", str(kothar_dir / ".chroma-data"))))

    return {
        "versao": config.get("versao", "4.0.0"),
        "operador": {
            "nome": nome_operador,
            "empresa": empresa,
            "cargo": cargo
        },
        "caminhos": {
            "kothar_dir": str(kothar_dir),
            "vault_dir": str(vault_dir),
            "chroma_dir": str(chroma_dir)
        },
        "rag": config.get("rag", {"ativo": True, "modo": "persistente_local"})
    }

if __name__ == "__main__":
    import pprint
    pprint.pprint(get_kothar_config())
