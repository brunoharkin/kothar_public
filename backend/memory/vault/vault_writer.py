"""
=============================================================
 KOTHAR v4.0 — Vault Writer/Reader (Cofre Obsidian)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Memória de Longo Prazo: relatórios de sessão em Markdown.
 Todo fim de sessão → relatório legível salvo no Cofre.
 Todo início de sessão antiga → Agente lê o relatório e retoma.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config import settings
from backend.core.exceptions import VaultError
from backend.core.logger import get_logger

log = get_logger("memory.vault")


class VaultWriter:
    """
    Grava relatórios de sessão no Cofre (diretório Obsidian).
    Formato: Markdown estruturado, legível por humanos e agentes.
    """

    def __init__(self):
        self.sessions_path: Path = settings.vault_sessions_path

    def _build_filename(self, session_id: str, task_summary: str) -> str:
        """
        Gera nome de arquivo descritivo.
        Ex: sessao_2026-08-30_Construcao_Frontend_abc12345.md
        """
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        slug = re.sub(r"[^\w\s-]", "", task_summary or "sessao")
        slug = re.sub(r"[\s]+", "_", slug.strip())[:40]
        short_id = session_id[:8]
        return f"sessao_{date_str}_{slug}_{short_id}.md"

    def write_session_report(
        self,
        session_id: str,
        agent_name: str,
        task_summary: str,
        traces: list[dict[str, Any]],
        files_modified: list[str],
        skills_used: list[str],
        tokens_total: int,
        cost_usd: float,
        status: str = "completed",
    ) -> Path:
        """
        Grava relatório completo da sessão no Cofre.
        Retorna o caminho do arquivo criado.
        """
        try:
            filename = self._build_filename(session_id, task_summary)
            filepath = self.sessions_path / filename

            report = self._render_report(
                session_id=session_id,
                agent_name=agent_name,
                task_summary=task_summary,
                traces=traces,
                files_modified=files_modified,
                skills_used=skills_used,
                tokens_total=tokens_total,
                cost_usd=cost_usd,
                status=status,
            )

            filepath.write_text(report, encoding="utf-8")
            log.info(
                "Relatório de sessão gravado no Cofre",
                path=str(filepath),
                traces_count=len(traces),
                session_id=session_id,
            )
            return filepath
        except Exception as e:
            raise VaultError(f"Falha ao gravar relatório: {e}", {"session_id": session_id})

    def _render_report(self, **kwargs) -> str:
        now = datetime.now(timezone.utc)
        traces = kwargs.get("traces", [])
        files_modified = kwargs.get("files_modified", [])
        skills_used = kwargs.get("skills_used", [])

        # Conta erros
        errors = [t for t in traces if t.get("is_error")]
        tools_used = list({t.get("tool_name") for t in traces if t.get("tool_name")})

        lines = [
            f"# Sessão: {kwargs['task_summary']}",
            "",
            f"> **Data:** {now.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"> **Agente:** `{kwargs['agent_name']}`  ",
            f"> **Status:** `{kwargs['status']}`  ",
            f"> **Session ID:** `{kwargs['session_id']}`",
            "",
            "---",
            "",
            "## 📊 Métricas",
            "",
            f"| Métrica | Valor |",
            f"|---------|-------|",
            f"| Tokens Total | {kwargs['tokens_total']:,} |",
            f"| Custo (USD) | ${kwargs['cost_usd']:.4f} |",
            f"| Eventos Traced | {len(traces)} |",
            f"| Erros | {len(errors)} |",
            f"| Arquivos Modificados | {len(files_modified)} |",
            f"| Skills Usadas | {len(skills_used)} |",
            "",
            "## 📁 Arquivos Modificados",
            "",
        ]

        if files_modified:
            for f in files_modified:
                lines.append(f"- `{f}`")
        else:
            lines.append("_Nenhum arquivo modificado._")

        lines += [
            "",
            "## 🔧 Ferramentas Utilizadas",
            "",
        ]
        if tools_used:
            for t in sorted(tools_used):
                lines.append(f"- `{t}`")
        else:
            lines.append("_Nenhuma ferramenta registrada._")

        lines += [
            "",
            "## 📚 Skills Aplicadas",
            "",
        ]
        if skills_used:
            for s in skills_used:
                lines.append(f"- {s}")
        else:
            lines.append("_Nenhuma skill aplicada nesta sessão._")

        if errors:
            lines += [
                "",
                "## ⛔ Erros Detectados",
                "",
            ]
            for err in errors[:10]:  # limita a 10 para legibilidade
                lines.append(f"- **{err.get('event_type', 'error')}**: {err.get('error_message', 'sem mensagem')[:200]}")

        lines += [
            "",
            "## 📋 Timeline de Eventos",
            "",
            "| # | Tipo | Agente | Ferramenta | Tokens | Erro |",
            "|---|------|--------|------------|--------|------|",
        ]

        for i, trace in enumerate(traces[:50], 1):  # limita a 50
            lines.append(
                f"| {i} | {trace.get('event_type', '-')} | "
                f"{trace.get('agent_name', '-')} | "
                f"{trace.get('tool_name', '-') or '-'} | "
                f"{trace.get('tokens_used', 0)} | "
                f"{'❌' if trace.get('is_error') else '✅'} |"
            )

        if len(traces) > 50:
            lines.append(f"\n_... e mais {len(traces) - 50} eventos. Ver Data Lake para lista completa._")

        lines += [
            "",
            "---",
            "",
            f"_Relatório gerado automaticamente pelo Engenheiro Kothar v{settings.kothar_version}_",
        ]

        return "\n".join(lines)


class VaultReader:
    """
    Lê relatórios de sessões anteriores do Cofre.
    Permite ao agente retomar trabalho antigo com exatidão.
    """

    def __init__(self):
        self.sessions_path: Path = settings.vault_sessions_path

    def list_sessions(self, limit: int = 20) -> list[dict[str, str]]:
        """Lista sessões disponíveis no Cofre, mais recentes primeiro."""
        try:
            files = sorted(
                self.sessions_path.glob("sessao_*.md"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            return [
                {
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": str(f.stat().st_size),
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
                for f in files[:limit]
            ]
        except Exception as e:
            raise VaultError(f"Falha ao listar sessões do Cofre: {e}")

    def read_session(self, filename: str) -> str:
        """Lê o conteúdo de um relatório de sessão."""
        try:
            filepath = self.sessions_path / filename
            if not filepath.exists():
                raise VaultError(f"Relatório não encontrado: {filename}")
            return filepath.read_text(encoding="utf-8")
        except VaultError:
            raise
        except Exception as e:
            raise VaultError(f"Falha ao ler relatório: {e}", {"filename": filename})

    def find_session_by_topic(self, topic: str) -> list[dict[str, str]]:
        """
        Busca sessões cujo nome de arquivo contém o tópico.
        Busca simples por substring — RAG semântico usa o ChromaDB.
        """
        all_sessions = self.list_sessions(limit=100)
        topic_lower = topic.lower()
        return [
            s for s in all_sessions
            if topic_lower in s["filename"].lower()
        ]


# Instâncias singleton
vault_writer = VaultWriter()
vault_reader = VaultReader()
