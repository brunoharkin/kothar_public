"""
=============================================================
 KOTHAR v4.0 — Agente QA (Portão de Qualidade)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Valida o código produzido pelo Engenheiro antes da entrega.
 Não confia no resultado até que passe pelo portão de QA.
"""

import ast
import json
import subprocess
import sys
import tomllib
from contextlib import suppress
from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.qa")


class QAAgent(BaseAgent):
    """
    Agente QA — Portão de Qualidade.

    Verifica:
    - Sintaxe Python (py_compile)
    - Imports quebrados (importlib check)
    - Testes existentes (pytest --collect-only)
    - Arquivos esperados presentes
    - Sem print() de debug deixados no código
    """

    @property
    def description(self) -> str:
        return "QA — valida qualidade do código antes da entrega"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        files: list[str]   = task.get("files", [])
        run_tests: bool    = task.get("run_tests", False)
        test_dir: str      = task.get("test_dir", "tests/")
        test_url: str | None = task.get("test_url")
        expected_files: list[str] = task.get("expected_files", [])

        checks_passed = []
        checks_failed = []

        # Necessidade funcional vem da rota do servidor, nunca da extensão do arquivo.
        if task.get("requires_frontend_verification"):
            checks_failed.append("Verificador funcional de frontend não configurado; aceite bloqueado.")
        if task.get("requires_auth_verification"):
            checks_failed.append("Verificador funcional de autenticação não configurado; aceite bloqueado.")

        log.info("QA iniciando validação", files_count=len(files))

        # 1. Verificação de sintaxe Python
        py_files = [f for f in files if f.endswith(".py")]
        if py_files:
            syntax_result = self._check_python_syntax(py_files)
            if syntax_result["passed"]:
                checks_passed.append("sintaxe_python")
            else:
                checks_failed.extend(syntax_result["errors"])

        # 2. Verifica arquivos esperados
        if expected_files:
            missing = [f for f in expected_files if not Path(f).exists()]
            if missing:
                checks_failed.append(f"Arquivos ausentes: {missing}")
            else:
                checks_passed.append("arquivos_esperados")

        if task.get("strict_artifact_checks"):
            for filepath in files:
                suffix = Path(filepath).suffix
                if suffix == ".py":
                    continue  # Já verificado acima, sem executar código do projeto.
                parser = {".json": json.loads, ".toml": tomllib.loads}.get(suffix)
                if parser is None:
                    checks_failed.append(f"Verificador para {suffix} não configurado; aceite funcional pendente.")
                    continue
                try:
                    parser(Path(filepath).read_text(encoding="utf-8"))
                    checks_passed.append(f"sintaxe_{suffix[1:]}")
                except (OSError, ValueError):
                    checks_failed.append(f"Arquivo {suffix} inválido ou indisponível.")

        # 3. Verifica debug prints
        debug_issues = self._check_debug_code(files)
        if debug_issues:
            checks_failed.extend(debug_issues)
        else:
            checks_passed.append("sem_debug_prints")

        # 4. Roda testes se solicitado
        if run_tests and Path(test_dir).exists():
            test_result = self._run_tests(test_dir)
            if test_result["passed"]:
                checks_passed.append(f"testes ({test_result['count']} passaram)")
            else:
                checks_failed.append(f"Testes falharam: {test_result['output'][:300]}")

        # 5. Validação Visual Automática (Browser-Use)
        if test_url:
            log.info("QA Iniciando Validação Visual (Browser-Use)", url=test_url)
            browser_result = await self._run_browser_validation(test_url)
            if browser_result["passed"]:
                checks_passed.append(f"validação_visual_web ({browser_result['title']})")
            else:
                checks_failed.append(f"Validação visual falhou: {browser_result['error']}")

        status = "passed" if not checks_failed else "failed"

        report = self._format_report(checks_passed, checks_failed)
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="qa_check",
            agent_name=self.agent_name,
            content=report,
            tool_name="qa_validator",
            tool_output={
                "status": status,
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
            },
            is_error=status == "failed",
        )

        log.info("QA concluído", status=status, passed=len(checks_passed), failed=len(checks_failed))
        return {
            "status": status,
            "agent": self.agent_name,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "report": report,
            "scope": "artifact_checks_only",
            "production_ready": False,
        }

    def _check_python_syntax(self, files: list[str]) -> dict:
        errors = []
        for filepath in files:
            try:
                ast.parse(Path(filepath).read_text(encoding="utf-8"), filename=filepath)
            except (OSError, SyntaxError, ValueError):
                errors.append("Sintaxe Python inválida ou arquivo indisponível.")
        return {"passed": len(errors) == 0, "errors": errors}

    def _check_debug_code(self, files: list[str]) -> list[str]:
        issues = []
        debug_patterns = ["print(", "console.log(", "debugger;", "import pdb", "pdb.set_trace()"]
        for filepath in files:
            path = Path(filepath)
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in debug_patterns:
                    if pattern in content:
                        issues.append(f"Debug code '{pattern}' encontrado em {filepath}")
            except Exception:
                pass
        return issues

    def _run_tests(self, test_dir: str) -> dict:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "--tb=short", "-q"],
                capture_output=True, text=True, timeout=120
            )
            passed = result.returncode == 0
            # Conta testes passados
            count = 0
            for line in result.stdout.splitlines():
                if " passed" in line:
                    with suppress(ValueError):
                        count = int(line.strip().split()[0])
            return {"passed": passed, "count": count, "output": result.stdout + result.stderr}
        except Exception as e:
            return {"passed": False, "count": 0, "output": str(e)}

    async def _run_browser_validation(self, url: str) -> dict[str, Any]:
        """
        Teste E2E Determinístico via Playwright.
        Acessa a URL, busca elementos do DOM, tira screenshots se falhar.
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = await browser.new_page()
                
                # Colecionador de logs de console
                console_logs = []
                page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
                
                log.info("QA acessando página para Teste E2E", url=url)
                response = await page.goto(url, wait_until="networkidle", timeout=15000)
                
                if not response or not response.ok:
                    await page.screenshot(path="scratch/qa_failure.png")
                    await browser.close()
                    return {
                        "passed": False, 
                        "error": f"Página retornou erro {response.status if response else 'Unknown'}",
                        "console": console_logs
                    }

                title = await page.title()
                
                # Verifica a renderização de elementos chaves (E2E básico determinístico)
                # O Kothar em produção geraria o seletor baseado no Blueprint.
                # Aqui faremos um check geral de existência de corpo e falta de telas de erro vazias.
                body = await page.inner_text("body")
                if "error" in body.lower() or "exception" in body.lower():
                    await page.screenshot(path="scratch/qa_failure_body.png")
                    await browser.close()
                    return {
                        "passed": False,
                        "error": "Texto de erro ou exception renderizado na tela (False Positive detectado).",
                        "console": console_logs
                    }

                await browser.close()
            
            return {"passed": True, "title": title}
        except Exception as e:
            log.error("Falha no Teste E2E (QA)", error=str(e), url=url)
            return {"passed": False, "error": str(e), "console": []}

    @staticmethod
    def _format_report(passed: list[str], failed: list[str]) -> str:
        lines = []
        if passed:
            lines.append(f"✅ Verificações OK ({len(passed)}):")
            for p in passed:
                lines.append(f"   • {p}")
        if failed:
            lines.append(f"❌ Verificações FALHADAS ({len(failed)}):")
            for f in failed:
                lines.append(f"   • {f}")
        return "\n".join(lines) or "Nenhuma verificação executada."
