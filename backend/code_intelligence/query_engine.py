"""
=============================================================
 KOTHAR v5.0 — Query Engine
 Queries Cypher e buscas estruturadas
=============================================================
"""

from typing import Optional, List, Dict, Any
from backend.code_intelligence.cbm_client import CBMClient
from backend.core.logger import get_logger

log = get_logger("code_intelligence.query")

class QueryEngine:
    """Motor de queries para code intelligence."""

    def __init__(self, cbm_client: CBMClient = None):
        self.cbm = cbm_client or CBMClient()

    # ============================================================
    # QUERIES COMUNS
    # ============================================================

    def find_functions_by_name(self, project: str, pattern: str) -> List[Dict]:
        """Busca funções por nome."""
        result = self.cbm.search_graph(
            project,
            query=f".*{pattern}.*",
            label="Function",
            limit=50
        )
        return result.get("nodes", []) if result else []

    def find_classes(self, project: str, pattern: str = None) -> List[Dict]:
        """Busca classes."""
        result = self.cbm.search_graph(
            project,
            query=pattern or ".*",
            label="Class",
            limit=100
        )
        return result.get("nodes", []) if result else []

    def find_modules(self, project: str, pattern: str = None) -> List[Dict]:
        """Busca módulos."""
        result = self.cbm.search_graph(
            project,
            query=pattern or ".*",
            label="Module",
            limit=100
        )
        return result.get("nodes", []) if result else []

    def get_callers(self, project: str, function_name: str) -> List[Dict]:
        """Obtém quem chama uma função."""
        result = self.cbm.trace_path(project, function_name, "inbound", depth=3)
        return result.get("paths", []) if result else []

    def get_callees(self, project: str, function_name: str) -> List[Dict]:
        """Obtém o que uma função chama."""
        result = self.cbm.trace_path(project, function_name, "outbound", depth=3)
        return result.get("paths", []) if result else []

    def get_full_call_graph(self, project: str, function_name: str) -> Dict:
        """Obtém grafo completo (caller + callee)."""
        return self.cbm.get_call_graph(project, function_name)

    # ============================================================
    # ANÁLISE DE ARQUITETURA
    # ============================================================

    def get_architecture_overview(self, project: str) -> Optional[Dict]:
        """Obtém overview da arquitetura."""
        return self.cbm.get_architecture(project)

    def get_package_structure(self, project: str) -> List[Dict]:
        """Obtém estrutura de pacotes."""
        result = self.cbm.search_graph(project, label="Package", limit=200)
        return result.get("nodes", []) if result else []

    def get_file_dependencies(self, project: str, file_path: str) -> Dict:
        """Obtém dependências de um arquivo."""
        # Busca imports do arquivo
        result = self.cbm.search_code(project, file_path, limit=1)
        if not result:
            return {"imports": [], "imported_by": []}

        return {
            "file": file_path,
            "imports": result.get("matches", [])
        }

    # ============================================================
    # ANÁLISE DE QUALIDADE
    # ============================================================

    def find_long_functions(self, project: str, min_lines: int = 100) -> List[Dict]:
        """Encontra funções muito longas."""
        query = f"MATCH (f:Function) WHERE f.end_line - f.start_line >= {min_lines} RETURN f"
        result = self.cbm.query_graph(project, query)
        return result.get("results", []) if result else []

    def find_dead_functions(self, project: str) -> List[str]:
        """Encontra funções nunca chamadas."""
        return self.cbm.find_dead_code(project)

    def find_circular_dependencies(self, project: str) -> List[str]:
        """Detecta dependências circulares."""
        return self.cbm.find_circular_deps(project)

    def get_complex_functions(self, project: str) -> List[Dict]:
        """Encontra funções complexas (muitas chamadas)."""
        # Functions com alto grau de saída
        result = self.cbm.search_graph(project, label="Function", limit=100)
        if not result or "nodes" not in result:
            return []

        nodes = result["nodes"]
        # Ordena por número de dependências (heurística)
        return sorted(
            [n for n in nodes if n.get("out_degree", 0) > 10],
            key=lambda x: x.get("out_degree", 0),
            reverse=True
        )

    # ============================================================
    # REFATORAÇÃO
    # ============================================================

    def suggest_extraction(self, project: str, function_name: str) -> Dict:
        """Sugere extração de código (refatoração)."""
        callees = self.get_callees(project, function_name)
        callers = self.get_callers(project, function_name)

        return {
            "function": function_name,
            "can_extract": len(callees) > 3 and len(callers) < 5,
            "internal_calls": len(callees),
            "external_callers": len(callers),
            "suggestion": "Boa candidate" if len(callees) > 3 else "Não vale a pena",
            "callees": callees,
            "callers": callers
        }

    def find_similar_functions(self, project: str, function_name: str) -> List[Dict]:
        """Encontra funções similares (possível duplicação)."""
        result = self.cbm.search_graph(
            project,
            query=f".*{function_name.split('_')[0] if '_' in function_name else function_name}.*",
            label="Function",
            limit=20
        )
        return [n for n in result.get("nodes", []) if n.get("name") != function_name] if result else []

    # ============================================================
    # IMPACTO DE MUDANÇAS
    # ============================================================

    def analyze_change_impact(self, project: str, changed_file: str) -> Dict:
        """Analisa impacto de mudança."""
        return self.cbm.analyze_impact(project, changed_file)

    def get_test_impact(self, project: str, changed_file: str) -> List[str]:
        """Identifica testes afetados por mudança."""
        # Encontra símbolos alterados
        impact = self.cbm.analyze_impact(project, changed_file)
        affected = impact.get("affected_symbols", [])

        # Encontra testes que usam esses símbolos
        tests = []
        for symbol in affected:
            callers = self.get_callers(project, symbol)
            for path in callers:
                if "test" in path.get("name", "").lower():
                    tests.append(path.get("name"))

        return list(set(tests))
