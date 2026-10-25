#!/usr/bin/env python3
import os
import glob
from pathlib import Path

# =======================================================
# KOTHAR SWARM ANALYZER (Map-Reduce Simulation)
# =======================================================
# Este script atua como o Agente N (O Contratante). Ele
# fatia os diretorios do awesome-llm-apps, le as docstrings
# e READMEs (Operarios Freelancers) e condensa tudo.

SOURCE_DIR = os.path.expanduser("~/kothar/scratch/awesome-llm-apps")
OUTPUT_FILE = os.path.expanduser("~/cofre/produtos/awesome-llm-apps-audit.md")

def analyze_directory(base_path):
    print(f"[CONTRATANTE] Iniciando varredura em {base_path}...")
    
    audit_lines = [
        "# Auditoria Profunda: Awesome LLM Apps",
        "**Gerado por:** Kothar Swarm (Agente N + O)",
        "**Objetivo:** Destilar a inteligência de +100 apps em um único contexto RAG.",
        "---"
    ]
    
    # Categorias principais na raiz
    categories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and not d.startswith(".")]
    
    for category in sorted(categories):
        cat_path = os.path.join(base_path, category)
        audit_lines.append(f"\n## Categoria: {category.replace('_', ' ').title()}")
        
        # Encontrar apps dentro da categoria
        apps = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d)) and not d.startswith(".")]
        
        for app in sorted(apps):
            app_path = os.path.join(cat_path, app)
            audit_lines.append(f"### 📦 App: {app}")
            
            # Tenta ler o README da app
            readme_path = os.path.join(app_path, "README.md")
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Extrai as primeiras linhas nao vazias para ser o "pitch" do freelance
                        pitch = [line.strip() for line in lines if line.strip() and not line.startswith("<") and not line.startswith("!")][:3]
                        audit_lines.append("**Resumo Freelancer:**")
                        for p in pitch:
                            audit_lines.append(f"> {p}")
                except Exception as e:
                    audit_lines.append(f"> Erro ao ler README: {e}")
            
            # Lista os arquivos principais de codigo
            py_files = glob.glob(f"{app_path}/*.py")
            if py_files:
                audit_lines.append("**Componentes Chave:**")
                for py in py_files:
                    audit_lines.append(f"- `{os.path.basename(py)}`")
            audit_lines.append("\n---")
            
    # Certificar-se que a pasta cofre/produtos existe
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("\n".join(audit_lines))
        
    print(f"[CONTRATANTE] Missão Cumprida! Relatório colossal gerado em: {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_directory(SOURCE_DIR)
