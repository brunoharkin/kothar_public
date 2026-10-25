"""
=============================================================
 KOTHAR v5.0 — CBM Client
 Wrapper Python para Codebase Memory CLI
=============================================================
"""

import subprocess
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from backend.core.logger import get_logger

log = get_logger("code_intelligence.cbm")

class CBMClient:
    """Cliente Python para o Codebase Memory MCP."""

    def __init__(self, binary: str = "codebase-memory-mcp"):
        self.binary = binary
        self._projects = None

    def _run(self, args: List[str], timeout: int = 60) -> Optional[Dict]:
        """Executa comando CBM."""
        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
            log.warning(f"CBM retornou código {result.returncode}: {result.stderr}")
            return None
        except subprocess.TimeoutExpired:
            log.error(f"Timeout em CBM: {' '.join(args)}")
            return None
        except Exception as e:
            log.error(f"Erro ao executar CBM: {e}")
            return None

    # ============================================================
    # INDEXING
    # ============================================================

    def index_repository(self, repo_path: str, project_name: str = None) -> Optional[Dict]:
        """Indexa um repositório."""
        args = ["cli", "index_repository", "--repo-path", repo_path]
        if project_name:
            args.extend(["--project-name", project_name])
        return self._run(args, timeout=300)

    def list_projects(self) -> List[str]:
        """Lista projetos indexados."""
        result = self._run(["cli", "list_projects"])
        if result and "projects" in result:
            return result["projects"]
        return []

    def delete_project(self, project_name: str) -> bool:
        """Remove um projeto."""
        result = self._run(["cli", "delete_project", "--project", project_name])
        return result is not None

    def index_status(self, project_name: str) -> Optional[Dict]:
        """Verifica status de indexação."""
        return self._run(["cli", "index_status", "--project", project_name])

    # ============================================================
    # QUERYING
    # ============================================================

    def search_graph(
        self,
        project: str,
        query: str = None,
        label: str = None,
        limit: int = 50
    ) -> Optional[Dict]:
        """Busca estruturada no grafo."""
        args = ["cli", "search_graph", "--project", project, "--limit", str(limit)]
        if query:
            args.extend(["--query", query])
        if label:
            args.extend(["--label", label])
        return self._run(args)

    def trace_path(
        self,
        project: str,
        function_name: str,
        direction: str = "both",
        depth: int = 3
    ) -> Optional[Dict]:
        """Traça caminho de dependências."""
        return self._run([
            "cli", "trace_path",
            "--project", project,
            "--function-name", function_name,
            "--direction", direction,
            "--depth", str(depth)
        ])

    def query_graph(self, project: str, cypher_query: str) -> Optional[Dict]:
        """Executa query Cypher."""
        return self._run([
            "cli", "query_graph",
            "--project", project,
            "--query", cypher_query
        ])

    def get_graph_schema(self, project: str) -> Optional[Dict]:
        """Obtém schema do grafo."""
        return self._run(["cli", "get_graph_schema", "--project", project])

    def get_code_snippet(
        self,
        project: str,
        qualified_name: str,
        start_line: int = None,
        end_line: int = None
    ) -> Optional[str]:
        """Obtém snippet de código."""
        args = [
            "cli", "get_code_snippet",
            "--project", project,
            "--qualified-name", qualified_name
        ]
        if start_line:
            args.extend(["--start-line", str(start_line)])
        if end_line:
            args.extend(["--end-line", str(end_line)])

        result = self._run(args)
        if result and "code" in result:
            return result["code"]
        return None

    def get_architecture(self, project: str) -> Optional[Dict]:
        """Obtém overview da arquitetura."""
        return self._run(["cli", "get_architecture", "--project", project])

    def search_code(
        self,
        project: str,
        pattern: str,
        file_pattern: str = None,
        limit: int = 100
    ) -> Optional[Dict]:
        """Busca texto em código."""
        args = [
            "cli", "search_code",
            "--project", project,
            "--pattern", pattern,
            "--limit", str(limit)
        ]
        if file_pattern:
            args.extend(["--file-pattern", file_pattern])
        return self._run(args)

    def detect_changes(self, project: str, git_diff: str = None) -> Optional[Dict]:
        """Detecta mudanças via git diff."""
        args = ["cli", "detect_changes", "--project", project]
        if git_diff:
            args.extend(["--git-diff", git_diff])
        return self._run(args)

    # ============================================================
    # ADR & TRACES
    # ============================================================

    def manage_adr(
        self,
        action: str,  # create, read, update, delete, list
        title: str = None,
        content: str = None,
        adr_id: str = None
    ) -> Optional[Dict]:
        """Gerencia Architecture Decision Records."""
        args = ["cli", "manage_adr", "--action", action]
        if title:
            args.extend(["--title", title])
        if content:
            args.extend(["--content", content])
        if adr_id:
            args.extend(["--id", adr_id])
        return self._run(args)

    def ingest_traces(self, project: str, trace_file: str) -> Optional[Dict]:
        """Ingere traces de runtime."""
        return self._run([
            "cli", "ingest_traces",
            "--project", project,
            "--trace-file", trace_file
        ])

    # ============================================================
    # UTILIDADES
    # ============================================================

    def find_dead_code(self, project: str) -> List[Dict]:
        """Encontra código morto (nós sem arestas de entrada)."""
        result = self.query_graph(
            project,
            "MATCH (n) WHERE NOT ()-[:CALLS]->(n) AND n:Function RETURN n"
        )
        if result and "results" in result:
            return result["results"]
        return []

    def find_circular_deps(self, project: str) -> List[List[str]]:
        """Detecta dependências circulares."""
        result = self.query_graph(
            project,
            "MATCH p=(a)-[:CALLS*]->(a) WHERE a:Function RETURN a.name, length(p)"
        )
        if result and "results" in result:
            return [r[0] for r in result["results"]]
        return []

    def get_call_graph(self, project: str, function: str) -> Dict:
        """Obtém grafo de chamadas completo."""
        upstream = self.trace_path(project, function, "inbound", depth=5)
        downstream = self.trace_path(project, function, "outbound", depth=5)
        return {
            "upstream": upstream.get("paths", []) if upstream else [],
            "downstream": downstream.get("paths", []) if downstream else []
        }

    def analyze_impact(self, project: str, changed_file: str) -> Dict:
        """Analisa impacto de mudança em arquivo."""
        result = self.detect_changes(project, git_diff=f"-- {changed_file}")
        return {
            "changed_file": changed_file,
            "affected_symbols": result.get("affected_symbols", []) if result else [],
            "dependency_count": len(result.get("affected_symbols", [])) if result else 0
        }
