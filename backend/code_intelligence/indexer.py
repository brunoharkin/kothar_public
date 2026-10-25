"""
=============================================================
 KOTHAR v5.0 — Codebase Indexer
 Indexação automática de projetos
=============================================================
"""

import os
from pathlib import Path
from typing import Optional, List
from backend.code_intelligence.cbm_client import CBMClient
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("code_intelligence.indexer")

class CodebaseIndexer:
    """Indexador de codebases usando CBM."""

    def __init__(self, cbm_client: CBMClient = None):
        self.cbm = cbm_client or CBMClient()
        self._indexed_projects = set()

    def should_index(self, project_name: str, repo_path: str) -> bool:
        """Decide se um projeto deve ser re-indexado."""
        status = self.cbm.index_status(project_name)
        if not status:
            return True

        # Verifica se há arquivos mais novos que a última indexação
        last_indexed = status.get("last_indexed", 0)
        repo_mtime = os.path.getmtime(repo_path)

        return repo_mtime > last_indexed

    def index_project(
        self,
        repo_path: str,
        project_name: str = None,
        force: bool = False
    ) -> dict:
        """Indexa um projeto."""
        if project_name is None:
            project_name = Path(repo_path).name

        log.info(f"Indexando {repo_path} como '{project_name}'")

        # Verifica se precisa indexar
        if not force and project_name in self._indexed_projects:
            if not self.should_index(project_name, repo_path):
                log.info(f"Projeto {project_name} já está atualizado")
                return {"status": "skipped", "reason": "up_to_date"}

        # Indexa
        result = self.cbm.index_repository(repo_path, project_name)

        if result:
            self._indexed_projects.add(project_name)
            log.info(f"Projeto {project_name} indexado com sucesso")

            # Registra no trace
            if trace_recorder:
                trace_recorder.record(
                    event_type="codebase_indexed",
                    content=f"Projeto {project_name} indexado",
                    tool_name="cbm_indexer",
                    tool_output={"project": project_name, "path": repo_path}
                )

            return {"status": "success", "project": project_name, "stats": result}
        else:
            log.error(f"Falha ao indexar {project_name}")
            return {"status": "error", "project": project_name}

    def index_projects(self, repo_paths: List[str]) -> dict:
        """Indexa múltiplos projetos."""
        results = []
        for path in repo_paths:
            result = self.index_project(path)
            results.append(result)

        success = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")

        return {
            "total": len(repo_paths),
            "success": success,
            "failed": failed,
            "results": results
        }

    def auto_discover_and_index(self, base_path: str = None) -> dict:
        """Descobre e indexa projetos automaticamente."""
        if base_path is None:
            base_path = str(Path.home())

        # Procura diretórios com .git
        git_dirs = []
        for root, dirs, files in os.walk(base_path):
            if ".git" in dirs:
                git_dirs.append(root)

        return self.index_projects(git_dirs[:10])  # Limita a 10

    def get_project_stats(self, project_name: str) -> Optional[dict]:
        """Obtém estatísticas de um projeto."""
        arch = self.cbm.get_architecture(project_name)
        schema = self.cbm.get_graph_schema(project_name)

        if not arch:
            return None

        return {
            "name": project_name,
            "languages": arch.get("languages", []),
            "packages": arch.get("packages", []),
            "node_count": schema.get("node_count", 0) if schema else 0,
            "edge_count": schema.get("edge_count", 0) if schema else 0,
            "files": arch.get("file_count", 0),
            "loc": arch.get("loc", 0)
        }
