#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — Pre-Execution Hook
 Executado ANTES de cada ação do Claude
 Verifica RAG, locks e valida a ação planejada
=============================================================
"""

import os
import sys
import json
import re
from pathlib import Path

# Adiciona hooks ao path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SKILLS_DIR = Path(__file__).parent.parent / "skills"
COFRE_DIR = Path.home() / "cofre"

# ============================================================
# CARREGAMENTO DE SKILLS
# ============================================================

def load_all_skills():
    """Carrega todas as skills."""
    skills = {}
    for yaml_file in SKILLS_DIR.glob("**/*.yaml"):
        try:
            content = yaml_file.read_text(encoding="utf-8")
            name = extract_yaml_value(content, 'name') or yaml_file.stem
            description = extract_yaml_value(content, 'description') or ''
            category = str(yaml_file.parent.relative_to(SKILLS_DIR)).replace('/', '.')

            skills[f"{category}.{yaml_file.stem}"] = {
                "name": name,
                "description": description,
                "category": category,
                "file": str(yaml_file)
            }
        except:
            pass
    return skills

def extract_yaml_value(content: str, key: str) -> str:
    """Extrai valor de chave YAML."""
    pattern = rf'^{key}:\s*(.+)$'
    match = re.search(pattern, content, re.MULTILINE)
    return match.group(1).strip() if match else ""

def normalize_text(text: str) -> str:
    """Normaliza texto."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def get_keywords(text: str) -> set:
    """Extrai keywords."""
    stopwords = {'a', 'o', 'e', 'de', 'do', 'da', 'em', 'no', 'na', 'um', 'uma', 'para', 'com', 'por', 'que', 'se'}
    words = normalize_text(text).split()
    return {w for w in words if len(w) > 2 and w not in stopwords}

# ============================================================
# BUSCA DE SKILLS
# ============================================================

def search_skills(query: str, skills: dict, max_results: int = 5) -> list:
    """Busca skills relevantes."""
    query_keywords = get_keywords(query)

    if not query_keywords:
        return []

    scored = []
    for skill_id, skill in skills.items():
        skill_keywords = get_keywords(f"{skill['name']} {skill['description']}")
        intersection = query_keywords & skill_keywords

        if intersection:
            score = len(intersection)
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:max_results]]

# ============================================================
# VERIFICAÇÃO DE LOCKS
# ============================================================

def check_locks(query: str, action: str = "") -> list:
    """Verifica violações de locks."""

    violations = []
    combined = f"{query} {action}".lower()

    # Padrões proibidos
    locks = [
        ("no_rag", "Você NÃO consultou o RAG/skills antes de agir!",
         "Execute: python3 ~/kothar/hooks/rag_preload.py search <tarefa>"),

        ("no_qa", "Você NÃO executou QA/testes após modificar código!",
         "Sempre execute testes após criar/editar código."),

        ("no_browser", "Você NÃO testou no navegador após criar UI!",
         "Sempre valide visualmente após criar componentes frontend."),

        ("alucina", "Você está ALUCINANDO informação!",
         "Consulte ~/cofre/ ou execute rag_preload.py antes de inventar dados."),

        ("hardcode_creds", "Você está EXPONDO credenciais no código!",
         "Use variáveis de ambiente (.env), nunca hardcode chaves/senhas."),

        ("no_cofre", "Você não consultou o Cofre (~/cofre/)!",
         "Sempre leia ~/cofre/ para informações sobre empresa/projetos/clientes."),
    ]

    # Verifica se está fazendo algo técnico sem RAG
    technical_actions = ['criar', 'modificar', 'implementar', 'desenvolver', 'corrigir']
    has_technical_action = any(a in combined for a in technical_actions)
    has_rag_call = 'rag_preload' in combined or 'skill' in combined

    if has_technical_action and not has_rag_call:
        violations.append({
            "lock": "MANDATORY_RAG",
            "warning": "⚠️ AÇÃO TÉCNICA SEM CONSULTA AO RAG!",
            "instruction": "Execute primeiro: python3 ~/kothar/hooks/rag_preload.py search <sua_tarefa>"
        })

    # Verifica padrões específicos
    if 'print(' in action and '.py' in action:
        violations.append({
            "lock": "debug_print",
            "warning": "❌ print() de debug no código!",
            "instruction": "Remova prints de debug antes de entregar código."
        })

    if re.search(r'password\s*=\s*["\'][^"\']+["\']', action, re.IGNORECASE):
        violations.append({
            "lock": "hardcoded_password",
            "warning": "❌ SENHA HARDCODADA DETECTADA!",
            "instruction": "Use: os.environ.get('PASSWORD') ou .env"
        })

    if re.search(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', action, re.IGNORECASE):
        violations.append({
            "lock": "hardcoded_apikey",
            "warning": "❌ API KEY HARDCODADA DETECTADA!",
            "instruction": "Use: os.environ.get('API_KEY') ou .env"
        })

    return violations

# ============================================================
# FORMATÇÃO DE OUTPUT
# ============================================================

def format_output(query: str, skills: list, locks: list) -> str:
    """Formata resultado para o Claude."""

    lines = []

    # Header
    lines.append("\n" + "=" * 60)
    lines.append("🔍 KOTHAR RAG PRELOAD")
    lines.append("=" * 60)

    # Skills relevantes
    if skills:
        lines.append("\n📚 **Skills relevantes para esta tarefa:**")
        for i, skill in enumerate(skills[:5], 1):
            lines.append(f"  {i}. **[{skill['category']}] {skill['name']}**")
            if skill['description']:
                lines.append(f"     {skill['description'][:100]}...")
            lines.append(f"     📁 {skill['file']}")
    else:
        lines.append("\n📚 Nenhuma skill encontrada para esta tarefa.")

    # Locks
    if locks:
        lines.append("\n" + "=" * 60)
        lines.append("🚨 **VERIFICAÇÃO DE LOCKS**")
        lines.append("=" * 60)
        for lock in locks:
            lines.append(f"\n{lock['warning']}")
            lines.append(f"   💡 {lock['instruction']}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)

# ============================================================
# MAIN
# ============================================================

def main():
    # Carrega skills
    skills = load_all_skills()

    # Pega query dos argumentos ou stdin
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = sys.stdin.read().strip()

    if not query:
        print("Uso: python pre_exec_hook.py <query>")
        print("   ou: echo '<tarefa>' | python pre_exec_hook.py")
        sys.exit(0)

    # Busca skills
    relevant_skills = search_skills(query, skills)

    # Verifica locks
    violations = check_locks(query)

    # Formata e exibe
    output = format_output(query, relevant_skills, violations)
    print(output)

if __name__ == "__main__":
    main()
