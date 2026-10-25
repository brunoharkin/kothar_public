"""
=============================================================
 KOTHAR v4.0 — Agente Disaster Recovery
 Engenheiro Kothar | Ugarit Digital
=============================================================
 O Guardião da Imutabilidade (Skill S). 
 Reidrata Bancos de Dados baseados no Cofre Obsidian.
"""

from typing import Any
import os
import json
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger

log = get_logger("agents.disaster_recovery")

class DisasterRecoveryAgent(BaseAgent):
    """
    Agente de DR. Faz Cold Backup ou Rebuild dos Bancos.
    """

    @property
    def description(self) -> str:
        return "Garante a sobrevivência dos dados RAG com espelhamento no Cofre."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        mode = task.get("mode", "sync")  # sync ou rebuild
        
        log.info(f"Disaster Recovery ativado. Modo: {mode}")

        if mode == "sync":
            # Extrai do BD e salva fisicamente
            await self.record_decision(
                decision="Espelhamento de Dados (Cold Backup)",
                reasoning="Mandato COLD_STORAGE_SYNC: Salvando estado vetorial no Cofre."
            )
            data_to_backup = task.get("data", {"info": "Mock Data"})
            backup_file = os.path.expanduser(f"~/cofre/rag_backup/vector_embeddings_source/backup_{self.session_id}.json")
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data_to_backup, f, indent=4)
            log.info(f"Cold Backup salvo em {backup_file}")
            return {"status": "passed", "report": "Backup sincronizado no Cofre."}

        elif mode == "rebuild":
            # Apaga tudo e recarrega do Cofre
            await self.record_decision(
                decision="REIDRATAÇÃO DE DESASTRE (Rebuild)",
                reasoning="Mandato VAULT_REBUILD_AUTHORITY: Recarregando ChromaDB/Neo4j a partir dos arquivos do Cofre."
            )
            log.warning("!!! INICIANDO REIDRATAÇÃO DOS BANCOS VETORIAIS A PARTIR DO COFRE !!!")
            
            from backend.memory.semantic.context_embedder import context_embedder
            
            try:
                result = await context_embedder.embed_all()
                log.success(f"Reidratação concluída. Arquivos: {result['indexed_files']}, Chunks: {result['indexed_chunks']}")
                return {"status": "passed", "report": f"O RAG foi reconstruído. {result['indexed_files']} arquivos indexados."}
            except Exception as e:
                log.error(f"Erro na reidratação: {e}")
                return {"status": "failed", "report": f"Falha na reidratação: {e}"}

        return {"status": "failed", "report": "Modo inválido."}
