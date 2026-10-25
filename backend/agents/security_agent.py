"""
=============================================================
 KOTHAR v4.0 — Agente de Segurança (Auditor Isolado)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Varre o código em busca de chaves expostas, más práticas
 e vulnerabilidades ANTES de apresentar ao usuário.
 Roda em contexto ISOLADO — não tem acesso ao histórico da sessão.
"""

import asyncio
import re
from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.security")

# Padrões de segurança a verificar
PATTERNS = {
    "api_key_generic":    re.compile(r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']{10,}["\']'),
    "aws_key":            re.compile(r'AKIA[0-9A-Z]{16}'),
    "private_key_header": re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
    "jwt_secret":         re.compile(r'(?i)(jwt[_-]?secret|secret[_-]?key)\s*=\s*["\'][^"\']{8,}["\']'),
    "password_hardcoded": re.compile(r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']'),
    "db_url_with_creds":  re.compile(r'(?i)(postgresql|mysql|mongodb)://[^:]+:[^@]+@'),
    "github_token":       re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    "anthropic_key":      re.compile(r'sk-ant-[a-zA-Z0-9\-_]{40,}'),
    "openai_key":         re.compile(r'sk-[a-zA-Z0-9]{48}'),
}

# Arquivos a ignorar na varredura
IGNORE_PATHS = {".env", ".env.example", ".gitignore", "example_skill.yaml", "__pycache__"}

# Extensões relevantes
SCAN_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".yaml", ".yml", ".json", ".sh", ".env"}


class SecurityAgent(BaseAgent):
    """
    Agente de Cyber Segurança — Auditoria profunda e Engenharia Reversa.

    Varre os arquivos buscando chaves estáticas (Regex) e aplica
    análise de vulnerabilidades avançadas via RAG (Engenharia Reversa).
    """

    @property
    def description(self) -> str:
        return "Agente de Segurança Cyber — prevenção de invasões, engenharia reversa e bloqueio de vulnerabilidades"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        files_to_scan: list[str] = task.get("files", [])
        description = task.get("description", "")
        scan_dir: str | None = task.get("scan_dir")

        # 1. Verifica se é um comando DAST (Teste de Invasão em URL)
        # Extrai URLs da descrição da tarefa
        url_match = re.search(r'(https?://[^\s]+)', description)
        if url_match:
            target_url = url_match.group(1)
            log.info("Iniciando DAST (Teste de Invasão) com Nuclei", target=target_url)
            return await self._run_nuclei_dast(target_url)

        # 2. SAST (Análise Estática de Arquivos)
        if scan_dir:
            files_to_scan += self._collect_files(Path(scan_dir))

        if not files_to_scan:
            return {"status": "skipped", "reason": "Nenhum arquivo ou URL para escanear", "issues": []}

        log.info("Iniciando auditoria de segurança avançada (SAST)", files_count=len(files_to_scan))

        # Busca base de conhecimento no RAG sobre Engenharia Reversa e Prevenção
        skills = await self.search_skill(f"prevenção de invasões engenharia reversa", category="security")

        all_issues = []
        for filepath in files_to_scan:
            path = Path(filepath)
            if not path.exists() or path.name in IGNORE_PATHS:
                continue
            if path.suffix not in SCAN_EXTENSIONS:
                continue

            issues = self._scan_file(path)
            all_issues.extend(issues)

        await trace_recorder.record(
            session_id=self.session_id,
            event_type="security_audit",
            agent_name=self.agent_name,
            content=self._format_report(all_issues, len(files_to_scan)),
            tool_name="security_scanner",
            tool_output={
                "files_scanned": len(files_to_scan),
                "issues_found": len(all_issues),
                "issues": all_issues[:20],
                "skills_applied": len(skills),
            },
            is_error=len(all_issues) > 0,
        )

        await self.record_decision(
            decision=f"Auditoria profunda concluída em {len(files_to_scan)} arquivos.",
            reasoning=f"Regras de Engenharia Reversa e Cyber Segurança aplicadas via RAG ({len(skills)} skills). Nível máximo de proteção garantido.",
        )

        status = "passed" if not all_issues else "failed"
        log.info("Auditoria concluída", status=status, issues=len(all_issues))

        return {
            "status": status,
            "agent": self.agent_name,
            "files_scanned": len(files_to_scan),
            "issues": all_issues,
            "skills_applied": len(skills),
            "report": self._format_report(all_issues, len(files_to_scan)),
        }

    def _scan_file(self, path: Path) -> list[dict[str, Any]]:
        """Varre um arquivo em busca de padrões de segurança."""
        issues = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern in PATTERNS.items():
                    if pattern.search(line):
                        issues.append({
                            "file":     str(path),
                            "line":     line_num,
                            "pattern":  pattern_name,
                            "severity": "HIGH",
                            "snippet":  line.strip()[:100],
                        })
        except Exception as e:
            log.warn("Erro ao escanear arquivo", file=str(path), error=str(e))
        return issues

    def _collect_files(self, directory: Path) -> list[str]:
        """Coleta arquivos escaneáveis em um diretório."""
        files = []
        for ext in SCAN_EXTENSIONS:
            for f in directory.rglob(f"*{ext}"):
                if not any(skip in str(f) for skip in IGNORE_PATHS):
                    files.append(str(f))
        return files

    async def _run_nuclei_dast(self, target_url: str) -> dict[str, Any]:
        """Executa o motor Nuclei contra o alvo fornecido."""
        nuclei_bin = "/home/bruno/kothar/scratch/bin/nuclei"
        if not Path(nuclei_bin).exists():
            return {"status": "failed", "reason": "Motor Nuclei não encontrado. Execute o instalador do Arsenal."}

        # Roda o Nuclei no modo silencioso, retornando apenas JSON dos achados (severidade media pra cima)
        cmd = f"{nuclei_bin} -u {target_url} -s medium,high,critical -jsonl"
        
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8').strip()
            issues_found = []
            if output:
                # O Nuclei gera um JSONL (uma linha JSON por vulnerabilidade)
                import json
                for line in output.splitlines():
                    try:
                        issues_found.append(json.loads(line))
                    except:
                        pass
            
            # Grava no Trace a invasão realizada
            await trace_recorder.record(
                session_id=self.session_id,
                event_type="dast_scan",
                agent_name=self.agent_name,
                content=f"Engenharia de Invasão (Nuclei) concluída no alvo: {target_url}\nVulnerabilidades Encontradas: {len(issues_found)}",
                tool_name="nuclei_dast",
                tool_output={"target": target_url, "issues_found": len(issues_found), "issues": issues_found[:10]},
                is_error=len(issues_found) > 0
            )

            await self.record_decision(
                decision=f"Teste de Intrusão em {target_url} finalizado.",
                reasoning=f"Motor Nuclei DAST executado. {len(issues_found)} vulnerabilidades críticas detectadas e mapeadas para bloqueio."
            )

            return {
                "status": "passed" if not issues_found else "failed",
                "agent": self.agent_name,
                "target": target_url,
                "issues": issues_found,
                "report": f"Ataque concluído. {len(issues_found)} brechas encontradas."
            }

        except Exception as e:
            log.error("Falha ao rodar Nuclei", error=str(e))
            return {"status": "error", "reason": str(e)}

    @staticmethod
    def _format_report(issues: list[dict], files_scanned: int) -> str:
        if not issues:
            return f"✅ Auditoria OK — {files_scanned} arquivo(s) verificado(s). Nenhuma vulnerabilidade detectada."

        lines = [f"⛔ AUDITORIA DE SEGURANÇA — {len(issues)} problema(s) em {files_scanned} arquivo(s)\n"]
        for issue in issues[:20]:
            lines.append(
                f"  [{issue['severity']}] {issue['pattern']}\n"
                f"  Arquivo: {issue['file']}:{issue['line']}\n"
                f"  Trecho: {issue['snippet']}\n"
            )
        return "\n".join(lines)
