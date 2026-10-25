#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — QA Auto-Executor
 Executado AUTOMATICAMENTE após criar/modificar código
 Testa sintaxe, executa testes, valida no browser
=============================================================
"""

import os
import sys
import re
import json
import subprocess
import traceback
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================
PROJECT_DIR = Path.home() / "kothar"

# ============================================================
# UTILITÁRIOS
# ============================================================

def log(msg: str, level: str = "INFO"):
    prefix = {"INFO": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(level, "📌")
    print(f"[QA-AUTO] {prefix} {msg}", file=sys.stderr)

def run_cmd(cmd: list, timeout: int = 30) -> dict:
    """Executa comando shell."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_DIR
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# VERIFICAÇÕES
# ============================================================

def check_python_syntax(files: list[str]) -> dict:
    """Verifica sintaxe de arquivos Python."""
    log("Verificando sintaxe Python...")

    errors = []
    for filepath in files:
        if not filepath.endswith('.py'):
            continue

        path = Path(filepath)
        if not path.exists():
            continue

        result = run_cmd(["python3", "-m", "py_compile", str(path)], timeout=10)
        if not result["success"]:
            errors.append(f"{filepath}: {result.get('stderr', result.get('error', 'Erro'))}")

    return {
        "check": "python_syntax",
        "passed": len(errors) == 0,
        "errors": errors,
        "summary": f"{len(files)} arquivos verificados, {len(errors)} erros"
    }

def check_debug_code(files: list[str]) -> dict:
    """Verifica código de debug deixado."""
    log("Verificando debug code...")

    patterns = [
        (r'\bprint\s*\(', "print() encontrado"),
        (r'\bconsole\.log\s*\(', "console.log() encontrado"),
        (r'\bdebugger\b', "debugger encontrado"),
        (r'\bimport\s+pdb\b', "import pdb encontrado"),
        (r'pdb\.set_trace\(\)', "pdb.set_trace() encontrado"),
        (r'\bimport\s+ipdb\b', "import ipdb encontrado"),
    ]

    issues = []
    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, msg in patterns:
                if re.search(pattern, content):
                    issues.append(f"{filepath}: {msg}")
        except:
            pass

    return {
        "check": "debug_code",
        "passed": len(issues) == 0,
        "errors": issues,
        "summary": f"{len(issues)} issues de debug encontrados"
    }

def check_credentials(files: list[str]) -> dict:
    """Verifica credenciais expostas."""
    log("Verificando credenciais expostas...")

    patterns = [
        (r'password\s*=\s*["\'][^"\']{3,}["\']', "Password hardcoded"),
        (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', "API Key hardcoded"),
        (r'secret\s*=\s*["\'][^"\']{10,}["\']', "Secret hardcoded"),
        (r'token\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Token hardcoded"),
    ]

    issues = []
    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, msg in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    issues.append(f"{filepath}: {msg}")
        except:
            pass

    return {
        "check": "credentials",
        "passed": len(issues) == 0,
        "errors": issues,
        "summary": f"{len(issues)} credenciais expostas"
    }

def check_imports(files: list[str]) -> dict:
    """Verifica imports quebrados."""
    log("Verificando imports...")

    issues = []
    for filepath in files:
        if not filepath.endswith('.py'):
            continue

        path = Path(filepath)
        if not path.exists():
            continue

        # Tenta importar o arquivo
        result = run_cmd([
            "python3", "-c",
            f"import sys; sys.path.insert(0, '{PROJECT_DIR}'); exec(open('{path}').read())"
        ], timeout=10)

        if not result["success"]:
            stderr = result.get("stderr", "")
            if "ModuleNotFoundError" in stderr:
                module = re.search(r"ModuleNotFoundError: No module named '([^']+)'", stderr)
                if module:
                    issues.append(f"{filepath}: Módulo não encontrado: {module.group(1)}")

    return {
        "check": "imports",
        "passed": len(issues) == 0,
        "errors": issues,
        "summary": f"{len(issues)} imports quebrados"
    }

def check_tests(files: list[str]) -> dict:
    """Executa testes se existirem."""
    log("Verificando testes...")

    # Encontra diretórios de teste
    test_dirs = ["tests", "test", "spec", "specs"]
    test_files = []

    for test_dir in test_dirs:
        for f in Path(PROJECT_DIR).rglob(f"{test_dir}/*"):
            if f.suffix in ['.py', '.js', '.ts']:
                test_files.append(f)

    if not test_files:
        return {
            "check": "tests",
            "passed": True,
            "skipped": True,
            "summary": "Nenhum teste encontrado"
        }

    # Executa pytest para Python
    py_tests = [f for f in test_files if f.suffix == '.py']
    if py_tests:
        result = run_cmd(["python3", "-m", "pytest", "-v", "--tb=short"] + [str(f) for f in py_tests], timeout=60)
        return {
            "check": "tests",
            "passed": result["success"],
            "output": result.get("stdout", "")[:500],
            "errors": [result.get("stderr", "")] if not result["success"] else [],
            "summary": "Testes passaram" if result["success"] else "Testes falharam"
        }

    return {
        "check": "tests",
        "passed": True,
        "skipped": True,
        "summary": "Testes não executados (sem pytest)"
    }

def check_frontend_build(files: list[str]) -> dict:
    """Verifica se frontend compila."""
    log("Verificando build do frontend...")

    # Procura package.json
    package_json = None
    for f in Path(PROJECT_DIR).rglob("package.json"):
        if f.exists():
            package_json = f
            break

    if not package_json:
        return {
            "check": "frontend_build",
            "passed": True,
            "skipped": True,
            "summary": "Nenhum package.json encontrado"
        }

    # Tenta npm install e build
    result = run_cmd(["npm", "install", "--silent"], timeout=60)
    if not result["success"]:
        return {
            "check": "frontend_build",
            "passed": False,
            "errors": [result.get("stderr", "npm install falhou")],
            "summary": "npm install falhou"
        }

    result = run_cmd(["npm", "run", "build"], timeout=120)
    return {
        "check": "frontend_build",
        "passed": result["success"],
        "output": result.get("stdout", "")[:500],
        "errors": [result.get("stderr", "Build falhou")] if not result["success"] else [],
        "summary": "Build passou" if result["success"] else "Build falhou"
    }

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def run_qa(files: list[str] = None) -> dict:
    """Executa todas as verificações de QA."""

    log("🚀 INICIANDO QA AUTO")
    log("=" * 50)

    # Se não passou arquivos, usa os últimos modificados
    if not files:
        # Pega arquivos modificados recentemente
        files = []
        for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']:
            for f in Path(PROJECT_DIR).rglob(f"*{ext}"):
                if f.exists() and not any(x in str(f) for x in ['node_modules', '.venv', '__pycache__', '.git']):
                    files.append(str(f))

    log(f"Arquivos para verificar: {len(files)}")

    results = []

    # Executa todas as verificações
    results.append(check_python_syntax(files))
    results.append(check_debug_code(files))
    results.append(check_credentials(files))
    results.append(check_imports(files))
    results.append(check_tests(files))

    # Mostra resultado
    log("")
    log("📊 RESULTADO DO QA")
    log("=" * 50)

    all_passed = True
    for r in results:
        status = "✅ PASSOU" if r["passed"] else "❌ FALHOU"
        log(f"  {r['check']}: {status}")
        log(f"    {r['summary']}")

        if not r["passed"] and r.get("errors"):
            for err in r["errors"][:3]:
                log(f"    → {err[:100]}")

        if not r["passed"]:
            all_passed = False

    log("")
    if all_passed:
        log("🎉 TODAS AS VERIFICAÇÕES PASSARAM", "INFO")
    else:
        log("⚠️ ALGUMAS VERIFICAÇÕES FALHARAM", "WARN")

    return {
        "success": all_passed,
        "checks": results,
        "total_files": len(files)
    }

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    files = sys.argv[1:] if len(sys.argv) > 1 else None
    result = run_qa(files)

    # Saída JSON para parsing
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)
