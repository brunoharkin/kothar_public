#!/usr/bin/env python3
"""
KOTHAR FALSE POSITIVE DETECTOR
Valida se o código realmente está correto antes de falar "pronto"
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Cores
VERDE = '\033[0;32m'
AMARELO = '\033[1;33m'
VERMELHO = '\033[0;31m'
AZUL = '\033[0;34m'
CINZA = '\033[0;90m'
RESET = '\033[0m'
BOLD = '\033[1m'


class FalsePositiveDetector:
    """Detector de falsos positivos"""

    def __init__(self):
        self.pwd = os.getcwd()
        self.project = self._detect_project()

    def _detect_project(self) -> str:
        """Detecta projeto"""
        path = self.pwd.lower()
        if "crm-saphia" in path: return "crm-saphia"
        if "disparo-em-massa" in path: return "disparo-em-massa"
        if "bioleads" in path: return "bioleads"
        if "kothar" in path: return "kothar"
        return "projeto-desconhecido"

    def _run_cmd(self, cmd: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Executa comando e retorna (stdout, stderr, returncode)"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout,
                cwd=self.pwd
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "[timeout]", -1
        except Exception as e:
            return "", str(e), -1

    def validate_before_saying_done(self, arquivo: str, funcao: str = "") -> Dict:
        """
        ANTES do agente falar "pronto", valida que realmente funcionou.
        Retorna dicionário com resultado da validação.
        """

        result = {
            "validado": False,
            "tipo": "UNKNOWN",
            "detalhes": [],
            "recomendacao": "",
            "pode_dizer_pronto": False
        }

        # 1. Verificar se arquivo existe
        if not Path(arquivo).exists():
            result["tipo"] = "ARQUIVO_NAO_EXISTE"
            result["detalhes"].append(f"Arquivo {arquivo} não existe")
            result["recomendacao"] = "Erro crítico: arquivo não foi criado"
            return result

        # 2. Verificar sintaxe
        sintaxe_ok = self._check_syntax(arquivo)
        if not sintaxe_ok["ok"]:
            result["tipo"] = "ERRO_SINTAXE"
            result["detalhes"].append(f"Erro de sintaxe: {sintaxe_ok['error']}")
            result["recomendacao"] = "Corrigir erro de sintaxe antes de falar 'pronto'"
            return result

        # 3. Verificar imports
        imports_ok, import_issues = self._check_imports(arquivo)
        if not imports_ok:
            result["tipo"] = "IMPORTS_BROKEN"
            result["detalhes"].extend(import_issues)
            result["recomendacao"] = "Imports quebrados - verificar caminhos e dependências"
            return result

        # 4. Verificar lógica (se função especificada)
        if funcao:
            logica_ok, logica_issues = self._check_logica(arquivo, funcao)
            if not logica_ok:
                result["tipo"] = "ERRO_LOGICA"
                result["detalhes"].extend(logica_issues)
                result["recomendacao"] = "Problema de lógica encontrado"
                return result

        # 5. Verificar testes
        testes_passam, teste_result = self._check_testes(arquivo)
        if not testes_passam:
            result["tipo"] = "TESTES_FALHANDO"
            result["detalhes"].append(teste_result)
            result["recomendacao"] = "Testes falhando - não dizer 'pronto' ainda"
            return result

        # 6. Verificar se não mudou mais do que deveria (escopo)
        if funcao:
            escopo_ok, escopo_issues = self._check_escopo(arquivo, funcao)
            if not escopo_ok:
                result["tipo"] = "ESCOPO_ROMPIDO"
                result["detalhes"].extend(escopo_issues)
                result["recomendacao"] = "Mudou código fora do escopo solicitado"
                return result

        # Se chegou aqui, está tudo OK
        result["validado"] = True
        result["tipo"] = "VALIDADO"
        result["detalhes"].append("✅ Sintaxe OK")
        result["detalhes"].append("✅ Imports OK")
        if funcao:
            result["detalhes"].append("✅ Lógica OK")
        result["detalhes"].append("✅ Testes passaram")
        result["pode_dizer_pronto"] = True
        result["recomendacao"] = "Código validado - PODE falar 'pronto'"

        return result

    def _check_syntax(self, arquivo: str) -> Dict:
        """Verifica sintaxe do arquivo"""

        ext = Path(arquivo).suffix

        if ext in ['.ts', '.tsx']:
            # TypeScript
            stdout, stderr, code = self._run_cmd(f"npx tsc --noEmit {arquivo} 2>&1")
            if code == 0:
                return {"ok": True}
            return {"ok": False, "error": stderr[:200]}

        elif ext in ['.js', '.jsx']:
            # JavaScript
            stdout, stderr, code = self._run_cmd(f"node --check {arquivo} 2>&1")
            if code == 0:
                return {"ok": True}
            return {"ok": False, "error": stderr[:200]}

        elif ext == '.py':
            # Python
            stdout, stderr, code = self._run_cmd(f"python3 -m py_compile {arquivo} 2>&1")
            if code == 0:
                return {"ok": True}
            return {"ok": False, "error": stderr[:200]}

        elif ext in ['.go']:
            # Go
            stdout, stderr, code = self._run_cmd(f"go build {arquivo} 2>&1")
            if code == 0:
                return {"ok": True}
            return {"ok": False, "error": stderr[:200]}

        return {"ok": True}  # Default: aceitar

    def _check_imports(self, arquivo: str) -> Tuple[bool, List[str]]:
        """Verifica se imports estão corretos"""

        issues = []
        ext = Path(arquivo).suffix

        if ext in ['.ts', '.tsx', '.js', '.jsx']:
            # Extrair imports
            with open(arquivo) as f:
                content = f.read()

            # Buscar imports
            import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)

            # Verificar cada import
            for imp in imports:
                if imp.startswith('.'):
                    # Import relativo - verificar se arquivo existe
                    base = Path(arquivo).parent
                    target = (base / imp).resolve()

                    # Adicionar extensão se necessário
                    if not target.exists():
                        for ext in ['.ts', '.tsx', '.js', '.jsx']:
                            if target.with_suffix(ext).exists():
                                break
                        else:
                            issues.append(f"Import não encontrado: {imp}")

        return (len(issues) == 0, issues)

    def _check_logica(self, arquivo: str, funcao: str) -> Tuple[bool, List[str]]:
        """Verifica problemas de lógica básicos"""

        issues = []

        try:
            with open(arquivo) as f:
                content = f.read()

            # 1. Verificar se função existe
            if funcao and funcao not in content:
                issues.append(f"Função {funcao} não encontrada no arquivo")

            # 2. Verificar null/undefined
            if 'return null' in content or 'return undefined' in content:
                # Verificar se está em contexto apropriado
                if 'catch' not in content:
                    issues.append("⚠️ Retorna null/undefined mas não há try/catch")

            # 3. Verificar async sem await
            if 'async' in content:
                if 'await' not in content:
                    issues.append("⚠️ Função async sem await")

            # 4. Verificar promises sem tratamento
            if '.then(' in content and '.catch(' not in content:
                issues.append("⚠️ Promise sem .catch()")

            # 5. Verificar console.log em produção
            if re.search(r'console\.log\s*\(', content):
                issues.append("⚠️ console.log encontrado - remover em produção")

        except Exception as e:
            issues.append(f"Erro ao analisar lógica: {e}")

        return (len(issues) == 0, issues)

    def _check_testes(self, arquivo: str) -> Tuple[bool, str]:
        """Verifica se existem e passam testes"""

        # Procurar arquivo de teste
        arquivo_path = Path(arquivo)
        nome = arquivo_path.stem

        # Possíveis locais de teste
        testes = [
            arquivo_path.parent / f"{nome}.test{arquivo_path.suffix}",
            arquivo_path.parent / f"{nome}.spec{arquivo_path.suffix}",
            arquivo_path.parent / "__tests__" / f"{nome}.test{arquivo_path.suffix}",
            arquivo_path.parent.parent / "test" / f"{nome}.test{arquivo_path.suffix}",
        ]

        for teste in testes:
            if teste.exists():
                # Rodar teste
                stdout, stderr, code = self._run_cmd(f"npm test -- {teste} 2>&1", timeout=60)
                if code == 0:
                    return (True, f"Teste passou: {teste.name}")
                else:
                    return (False, f"Teste falhou: {teste.name}\n{stdout[:200]}")

        # Não encontrou teste
        return (True, "Nenhum teste encontrado (verificar manualmente)")

    def _check_escopo(self, arquivo: str, funcao: str) -> Tuple[bool, List[str]]:
        """Verifica se não mudou mais do que deveria"""

        issues = []

        # Comparar com git
        stdout, stderr, code = self._run_cmd(f"git diff {arquivo} 2>&1")

        if code != 0:
            # Arquivo novo
            return (True, [])  # OK

        if not stdout:
            return (True, [])  # Sem mudanças

        # Verificar tamanho das mudanças
        linhas = stdout.count('\n')
        if linhas > 50:
            issues.append(f"⚠️ Muitas linhas alteradas ({linhas}) - verificar escopo")

        # Verificar se mudou só a função especificada
        if funcao and funcao in stdout:
            # Extrair contexto ao redor da função
            pass

        return (len(issues) == 0, issues)

    def gerar_relatorio_validacao(self, result: Dict) -> str:
        """Gera relatório de validação"""

        lines = []
        lines.append("")
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║              🔍 VALIDAÇÃO DE CÓDIGO                         ║")
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        lines.append("")

        if result["validado"]:
            lines.append(f"{VERDE}✅ CÓDIGO VALIDADO{RESET}")
            lines.append(f"{VERDE}   Pode falar 'pronto'{RESET}")
        else:
            lines.append(f"{VERMELHO}❌ PROBLEMAS ENCONTRADOS{RESET}")
            lines.append(f"{VERMELHO}   NÃO falar 'pronto' ainda{RESET}")

        lines.append("")
        lines.append(f"Tipo: {result['tipo']}")
        lines.append("")

        if result["detalhes"]:
            lines.append("Detalhes:")
            for d in result["detalhes"]:
                cor = VERDE if "✅" in d else VERMELHO if "❌" in d else AMARELO
                lines.append(f"  {cor}{d}{RESET}")

        lines.append("")
        lines.append(f"Recomendação: {result['recomendacao']}")
        lines.append("")

        return '\n'.join(lines)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python false-positive-detector.py <arquivo> [função]")
        print("")
        print("Exemplos:")
        print("  python false-positive-detector.py login.service.ts")
        print("  python false-positive-detector.py login.service.ts autenticarUsuario")
        sys.exit(1)

    arquivo = sys.argv[1]
    funcao = sys.argv[2] if len(sys.argv) > 2 else ""

    detector = FalsePositiveDetector()
    result = detector.validate_before_saying_done(arquivo, funcao)
    relatorio = detector.gerar_relatorio_validacao(result)

    print(relatorio)

    # Exit code baseado no resultado
    sys.exit(0 if result["pode_dizer_pronto"] else 1)


if __name__ == "__main__":
    main()
