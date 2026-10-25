#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — RAG Preload (Busca sem Embeddings)
 Antes de cada tarefa, busca skills relevantes
=============================================================
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SKILLS_DIR = Path(__file__).parent.parent / "skills"
COFRE_DIR = Path.home() / "cofre"
GOLD_STANDARD = SKILLS_DIR / "global" / "gold_standard.yaml"

# Cache de skills
_skills_cache = None

# ============================================================
# UTILITÁRIOS
# ============================================================

def log(msg: str):
    print(f"[KOTHAR-RAG] {msg}", file=sys.stderr)

def normalize_text(text: str) -> str:
    """Normaliza texto para busca."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_keywords(text: str) -> set:
    """Extrai keywords de um texto."""
    normalized = normalize_text(text)
    words = normalized.split()
    # Remove stopwords
    stopwords = {'a', 'o', 'e', 'de', 'do', 'da', 'em', 'no', 'na', 'um', 'uma', 'para', 'com', 'por', 'que', 'se', 'ao', 'os', 'as', 'é', 'são', 'foi', 'ser', 'ter', 'não', 'mais', 'ou', 'mas', 'como', 'seu', 'sua', 'dos', 'das', 'isso', 'este', 'esta', 'esse', 'essa', 'ele', 'ela'}
    return {w for w in words if len(w) > 2 and w not in stopwords}

# ============================================================
# CARREGAMENTO DE SKILLS
# ============================================================

def load_all_skills() -> dict:
    """Carrega todas as skills em cache."""
    global _skills_cache

    if _skills_cache is not None:
        return _skills_cache

    skills = {}

    # Carrega todos os YAMLs
    for yaml_file in SKILLS_DIR.glob("**/*.yaml"):
        try:
            content = yaml_file.read_text(encoding="utf-8")
            skill_data = parse_yaml_simple(content)

            # Extrai metadados
            name = skill_data.get('name', yaml_file.stem)
            description = skill_data.get('description', skill_data.get('overview', ''))
            instructions = skill_data.get('instructions', skill_data.get('when_to_use', ''))
            category = str(yaml_file.parent.relative_to(SKILLS_DIR)).replace('/', '.')

            # Calcula keywords
            all_text = f"{name} {description} {instructions} {content}"
            keywords = get_keywords(all_text)

            skill_id = f"{category}.{yaml_file.stem}"

            skills[skill_id] = {
                "id": skill_id,
                "name": name,
                "category": category,
                "description": description,
                "instructions": instructions,
                "keywords": keywords,
                "file": str(yaml_file),
                "content": content
            }

        except Exception as e:
            log(f"Erro ao carregar {yaml_file}: {e}")

    _skills_cache = skills
    log(f"Carregadas {len(skills)} skills")
    return skills

def parse_yaml_simple(content: str) -> dict:
    """Parse simples de YAML."""
    result = {}
    for line in content.split('\n'):
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key = line.split(':', 1)[0].strip()
            value = line.split(':', 1)[1].strip()
            result[key] = value if value else True
    return result

# ============================================================
# BUSCA DE SKILLS
# ============================================================

def search_skills(query: str, skills: dict = None, max_results: int = 5) -> list:
    """Busca skills relevantes usando matching de keywords."""

    if skills is None:
        skills = load_all_skills()

    query_keywords = get_keywords(query)

    if not query_keywords:
        return []

    scored = []

    for skill_id, skill in skills.items():
        # Score baseado em interseção de keywords
        skill_keywords = skill['keywords']
        intersection = query_keywords & skill_keywords

        if intersection:
            score = len(intersection) / max(len(query_keywords), 1)

            # Bônus para match no nome
            name_words = set(normalize_text(skill['name']).split())
            if query_keywords & name_words:
                score *= 1.5

            # Bônus para match na descrição
            desc_words = get_keywords(skill['description'])
            if query_keywords & desc_words:
                score *= 1.2

            scored.append((score, skill))

    # Ordena por score
    scored.sort(key=lambda x: x[0], reverse=True)

    return [s[1] for s in scored[:max_results] if s[0] > 0]

def search_locks(query: str, skills: dict = None, max_results: int = 3) -> list:
    """Busca locks/vetos aplicáveis."""

    if skills is None:
        skills = load_all_skills()

    query_keywords = get_keywords(query)

    if not query_keywords:
        return []

    # Locks estão nos comentários de cada skill
    locks = []

    for skill_id, skill in skills.items():
        content_lower = skill['content'].lower()
        query_lower = query.lower()

        # Busca por padrões de erro conhecidos
        lock_patterns = [
            ("no_rag", "não consulta rag", "SEMPRE buscar skills antes de executar"),
            ("no_qa", "não testa", "SEMPRE executar QA após criar código"),
            ("no_browser", "não testa navegador", "SEMPRE testar no browser após criar UI"),
            ("spaghetti", "código bagunçado", "SEMPRE revisar código antes de entregar"),
            ("alucina", "alucinar", "NUNCA alucinar - consultar RAG primeiro"),
            ("hardcode", "credenciais expostas", "NUNCA expor credenciais - usar .env"),
        ]

        for lock_id, pattern, solution in lock_patterns:
            if pattern in content_lower or pattern in query_lower:
                locks.append({
                    "id": lock_id,
                    "pattern": pattern,
                    "solution": solution,
                    "skill": skill['name']
                })

    return locks[:max_results]

# ============================================================
# FORMATAÇÃO PARA CLAUDE
# ============================================================

def format_skills_for_claude(skills: list) -> str:
    """Formata skills encontradas para contexto do Claude."""

    if not skills:
        return "Nenhuma skill relevante encontrada."

    lines = []
    lines.append("=" * 60)
    lines.append("🔍 SKILLS RELEVANTES PARA ESTA TAREFA")
    lines.append("=" * 60)

    for i, skill in enumerate(skills, 1):
        lines.append(f"\n{i}. **[{skill['category']}] {skill['name']}**")
        lines.append(f"   📝 {skill['description']}")

        if skill['instructions']:
            lines.append(f"   ⚡ Instruções: {skill['instructions'][:200]}...")

        lines.append(f"   📁 {skill['file']}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)

def format_locks_for_claude(locks: list) -> str:
    """Formata locks para contexto do Claude."""

    if not locks:
        return ""

    lines = []
    lines.append("\n🚨 **VETOS ATIVOS (não fazer):**")

    for lock in locks:
        lines.append(f"  ❌ {lock['solution']}")
        lines.append(f"     (Regra de {lock['skill']})")

    return "\n".join(lines)

# ============================================================
# PRELOAD COMPLETO
# ============================================================

def preload(query: str) -> str:
    """
    Função principal: retorna contexto RAG para a tarefa.
    Use isto antes de executar qualquer tarefa.
    """

    skills = load_all_skills()

    # Busca skills
    relevant_skills = search_skills(query, skills, max_results=5)
    relevant_locks = search_locks(query, skills, max_results=3)

    # Formata
    output = format_skills_for_claude(relevant_skills)
    output += format_locks_for_claude(relevant_locks)

    return output

# ============================================================
# VERIFICAÇÃO DE LOCKS ANTES DE AÇÃO
# ============================================================

def check_locks_before_action(action: str, context: str = "") -> list:
    """Verifica se a ação viola algum lock."""

    combined = f"{action} {context}"
    skills = load_all_skills()

    violations = []

    # Padrões de violação
    dangerous_patterns = [
        ("no_rag", "Você NÃO consultou o RAG/skills antes de agir. Sempre leia as skills relevantes primeiro."),
        ("no_qa", "Você NÃO executou QA após modificar código. Sempre teste após criar/editar código."),
        ("no_browser", "Você NÃO testou no navegador. Sempre valide visualmente após criar UI."),
        ("alucina", "Você está ALUCINANDO informação. Consulte o Cofre (~/cofre/) antes de inventar dados."),
        ("hardcode", "Você está EXPONDO credenciais! Use variáveis de ambiente (.env), nunca hardcode."),
        ("spaghetti", "Você está criando código ESPAGHETTI. Siga as regras de Clean Code."),
    ]

    for lock_id, warning in dangerous_patterns:
        if lock_id not in combined.lower():
            continue

        # Verifica se a ação foi tomada sem contexto
        if "skill" not in combined.lower() and "kothar" not in combined.lower():
            violations.append({
                "lock": lock_id,
                "warning": warning,
                "action": "REVERTER"
            })

    return violations

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "frontend"
            print(preload(query))

        elif sys.argv[1] == "check":
            action = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            violations = check_locks_before_action(action)
            if violations:
                print("\n🚨 VIOLAÇÕES DETECTADAS:")
                for v in violations:
                    print(f"  ❌ {v['warning']}")
            else:
                print("✅ Nenhuma violação detectada")

        elif sys.argv[1] == "list":
            skills = load_all_skills()
            print(f"\n📚 {len(skills)} Skills carregadas:")
            for sid, s in sorted(skills.items()):
                print(f"  • [{s['category']}] {s['name']}")

        elif sys.argv[1] == "load":
            load_all_skills()
            print("✅ Skills carregadas em cache")

        else:
            print(preload(" ".join(sys.argv[1:])))
    else:
        print("Uso: python rag_preload.py <comando> [args]")
        print("  search <query>   - Busca skills relevantes")
        print("  check <action>   - Verifica violações de locks")
        print("  list             - Lista todas as skills")
        print("  load             - Carrega cache de skills")
