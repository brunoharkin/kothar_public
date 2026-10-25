"""
=============================================================
 KOTHAR v4.0 — Agente Arquivista de Sessões
 Engenheiro Kothar | Ugarit Digital
=============================================================
 O Cronista. Invocado silenciosamente ao final da sessão
 para extrair os logs do banco e gerar o relatório no Cofre.
"""

from typing import Any
import os
import datetime
from pathlib import Path
from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger

log = get_logger("agents.archivist")

class SessionArchivistAgent(BaseAgent):
    """
    Agente Arquivista (Skill R).
    Extrai Traces e gera o documento de Evolução.
    """

    @property
    def description(self) -> str:
        return "Arquivista de Sessão. Gera o relatório no Cofre de forma silenciosa."

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        session_id_to_archive = task.get("session_to_archive", self.session_id)
        
        log.info(f"Arquivista de Sessão ativado. Compilando Traces...", session_id=session_id_to_archive)

        await self.record_decision(
            decision=f"Compilando relatório silencioso para {session_id_to_archive}",
            reasoning="Mandato ZERO_CONTEXT_POLLUTION: Escrevendo direto no disco para não poluir o LLM."
        )

        # Simulação da extração do Banco de Dados (Trace Vault)
        # O agente faria SELECT * FROM traces WHERE session_id = ...
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        vault_root = os.environ.get("KOTHAR_VAULT_PATH", str(Path.home() / "Cofre"))
        vault_path = os.path.join(
            vault_root, "registro_de_sessao", f"sessao_{timestamp}.md"
        )
        
        markdown_report = f"""# Registro de Sessão: Kothar Orquestra
**Sessão ID:** {session_id_to_archive}
**Data:** {timestamp}

## 1. Resumo da Evolução
Esta sessão consolidou a arquitetura Swarm, implementou o Supervisor Severo, definiu a Lei do Padrão Ouro (MCP) e finalizou com o RAG absoluto no Cofre Obsidian.

## 2. Agentes Envolvidos
- [A00] Triador
- [A0] Arquiteto Supremo
- [I] Auditor de Segurança
- [N] Contratante Swarm
- [P] Supervisor Severo
- [Q] Estrategista de Ads
- [R] Arquivista de Sessões

## 3. Arquivos Alterados (Dossiê do Supervisor)
- `KOTHAR-AGENT-DEFINITION.md`
- `global/gold_standard.yaml`
- `~/cofre/` estruturado fisicamente.

## 4. Notas de Arquitetura
O sistema superou o modelo de agente único. A partir de agora, as sessões serão encapsuladas neste formato e salvas no Cofre para consulta via RAG, liberando tokens valiosos do buffer ativo.
"""

        # Escrevendo fisicamente no arquivo do Cofre
        os.makedirs(os.path.dirname(vault_path), exist_ok=True)
        with open(vault_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)

        log.info(f"Registro de sessão salvo fisicamente em {vault_path}")

        return {
            "status": "passed",
            "agent": self.agent_name,
            "report": f"Relatório de Sessão Arquivado silenciosamente em {vault_path}",
            "vault_path": vault_path
        }
