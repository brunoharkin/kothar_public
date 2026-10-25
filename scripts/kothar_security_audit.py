#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 - AUDITOR DE SEGURANÇA AUTOMÁTICO
 Engenheiro Kothar | Ugarit Digital
=============================================================

 Este script verifica violações de segurança em código
 antes de commits, alterações ou qualquer modificação.

 Uso:
   python kothar_security_audit.py <arquivo|directory>

 Exit codes:
   0 = Aprovado (sem violações)
   1 = Violações encontradas
   2 = Erro no script
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Padrões de violação CRÍTICA (apenas para código real, não documentação)
CRITICAL_PATTERNS = [
    # Credenciais hardcoded (IGNORAR documentação/strings de exemplo)
    (r'(?:["\']?api[_-]?key["\']?)\s*[:=]\s*["\'][a-zA-Z0-9_-]{8,}', "API Key hardcoded"),
    (r'["\']secret[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}', "Secret Key hardcoded"),
    (r'["\']password["\']?\s*[:=]\s*["\'][a-zA-Z0-9@#$%]{8,}', "Password hardcoded"),
    (r'["\']token["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{20,}', "Token hardcoded"),
    # Keys reais (não em documentação)
    (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key exposta"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Token exposto"),
    (r'AKIA[A-Z0-9]{16}', "AWS Access Key exposta"),

    # localStorage com dados sensíveis
    (r'localStorage\.(setItem|getItem)\s*\(\s*["\'][^"\']*(?:token|key|secret|password|credential)',
     "localStorage para dados sensíveis"),

    # Console log com dados sensíveis (apenas log, não documentação)
    (r'console\.(log|debug|info)\s*\([^)]*(?:password|token|secret|key)[^)]*\)',
     "Console log com dado sensível"),
]

# Padrões de violação ALTA
HIGH_PATTERNS = [
    # IPS/Portas internas
    (r'(?:localhost|127\.0\.0\.1):\d{4,5}', "Porta interna exposta"),
    (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}', "IP:Porta exposto"),

    # Session storage
    (r'sessionStorage\.setItem\s*\([^,]+,\s*(?:token|key|secret|password)',
     "sessionStorage para dados sensíveis"),

    # Comentários com secrets
    (r'#.*(?:password|token|secret|key)\s*[=:]\s*\S+', "Comentário com segredo"),
    (r'//.*(?:password|token|secret|key)\s*[=:]\s*\S+', "Comentário com segredo"),
]

# Arquivos permitidos (nãoAuditar)
EXEMPT_PATTERNS = [
    r'\.git/',
    r'node_modules/',
    r'__pycache__/',
    r'\.venv/',
    r'coverage/',
    r'dist/',
    r'build/',
    r'\.pyc$',
    r'\.pyo$',
    r'\.env$',
    r'\.env\.example$',
    r'migrations/',
    r'seeders/',
]

# Extensões de arquivo para auditar
AUDIT_EXTENSIONS = [
    '.py', '.ts', '.tsx', '.js', '.jsx',
    '.sh', '.bash', '.yaml', '.yml', '.json'
]


# ============================================================
# CLASSE DE AUDITORIA
# ============================================================

class SecurityAuditor:
    """Auditor de segurança para código Kothar."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.violations: List[Dict] = []
        self.files_audited = 0

    def should_audit(self, file_path: Path) -> bool:
        """Verifica se o arquivo deve ser auditado."""
        path_str = str(file_path)

        # Verificar isenções
        for pattern in EXEMPT_PATTERNS:
            if re.search(pattern, path_str):
                return False

        # Verificar extensão
        return file_path.suffix in AUDIT_EXTENSIONS

    def audit_file(self, file_path: Path) -> None:
        """Audita um arquivo específico."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            self.files_audited += 1

            # Verificar padrões críticos
            for line_num, line in enumerate(lines, 1):
                # Ignorar comentários e strings em arquivos de exemplo
                if '.env.example' in str(file_path) or 'sample' in str(file_path):
                    continue

                for pattern, description in CRITICAL_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.violations.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': 'CRITICAL',
                            'description': description,
                            'code': line.strip()[:100]
                        })

                # Verificar padrões altos
                for pattern, description in HIGH_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.violations.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': 'HIGH',
                            'description': description,
                            'code': line.strip()[:100]
                        })

        except Exception as e:
            print(f"  ⚠️ Erro ao auditar {file_path}: {e}")

    def audit_directory(self, directory: Path) -> None:
        """Audita um diretório recursivamente."""
        print(f"\n🔍 Auditando: {directory}")

        for item in directory.rglob('*'):
            if item.is_file() and self.should_audit(item):
                self.audit_file(item)

    def audit(self) -> Tuple[bool, str]:
        """
        Executa a auditoria completa.
        Retorna (aprovado, mensagem).
        """
        print("=" * 60)
        print("🔒 KOTHAR AUDITOR DE SEGURANÇA v4.0")
        print("=" * 60)

        if self.path.is_file():
            print(f"\n📄 Arquivo: {self.path}")
            self.audit_file(self.path)
        elif self.path.is_dir():
            self.audit_directory(self.path)
        else:
            return False, f"Caminho não encontrado: {self.path}"

        # Relatório
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE AUDITORIA")
        print("=" * 60)
        print(f"\n📁 Arquivos auditados: {self.files_audited}")

        if not self.violations:
            print("\n✅ NENHUMA VIOLAÇÃO ENCONTRADA")
            print("   Código aprovado para commit.")
            return True, "Aprovado"

        # Violações encontradas
        critical = [v for v in self.violations if v['type'] == 'CRITICAL']
        high = [v for v in self.violations if v['type'] == 'HIGH']

        print(f"\n🚨 VIOLAÇÕES ENCONTRADAS: {len(self.violations)}")
        print(f"   🔴 Críticas: {len(critical)}")
        print(f"   🟠 Altas: {len(high)}")

        if critical:
            print("\n" + "=" * 60)
            print("🔴 VIOLAÇÕES CRÍTICAS (DEVEM SER CORRIGIDAS)")
            print("=" * 60)
            for v in critical:
                print(f"\n⚠️ {v['description']}")
                print(f"   📁 {v['file']}")
                print(f"   📍 Linha {v['line']}")
                print(f"   📝 {v['code']}")

        if high:
            print("\n" + "=" * 60)
            print("🟠 VIOLAÇÕES ALTAS (REVISAR)")
            print("=" * 60)
            for v in high[:10]:  # Limitar a 10
                print(f"\n⚠️ {v['description']}")
                print(f"   📁 {v['file']}")
                print(f"   📍 Linha {v['line']}")

        if len(high) > 10:
            print(f"\n   ... e mais {len(high) - 10} violações altas")

        # Salvar relatório
        self._save_report()

        if critical:
            return False, f"REPROVADO: {len(critical)} violações críticas"
        return False, f"REVISAR: {len(high)} violações altas"

    def _save_report(self) -> None:
        """Salva relatório de auditoria."""
        report_dir = Path("/home/bruno/cofre/auditorias")
        report_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"audit_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'files_audited': self.files_audited,
            'violations': self.violations,
            'summary': {
                'total': len(self.violations),
                'critical': len([v for v in self.violations if v['type'] == 'CRITICAL']),
                'high': len([v for v in self.violations if v['type'] == 'HIGH']),
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Relatório salvo: {report_file}")


# ============================================================
# HOOK DE PRE-COMMIT
# ============================================================

def run_pre_commit_hook():
    """Executa auditoria antes do commit."""
    # Pega arquivos staged
    import subprocess

    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True, text=True, cwd='/home/bruno/kothar'
        )
        files = result.stdout.strip().split('\n')
    except Exception as e:
        print(f"⚠️ Erro ao obter arquivos staged: {e}")
        return 0

    if not files or files == ['']:
        print("Nenhum arquivo para auditar.")
        return 0

    print(f"\n📁 Arquivos para auditar: {len(files)}")

    # Auditar cada arquivo
    auditor = SecurityAuditor('/home/bruno/kothar')
    all_clean = True

    for file in files:
        if file:
            file_path = Path('/home/bruno/kothar') / file
            if file_path.exists() and auditor.should_audit(file_path):
                auditor.audit_file(file_path)

    # Resultado
    if not auditor.violations:
        print("\n✅ TODOS OS ARQUIVOS APROVADOS")
        return 0

    print(f"\n🚨 {len(auditor.violations)} VIOLAÇÕES ENCONTRADAS")
    print("❌ COMMIT BLOQUEADO")
    print("\nCorrija as violações antes de commitar.")
    print("Ou use --no-verify para pular (NÃO RECOMENDADO)")

    return 1


# ============================================================
# MAIN
# ============================================================

def main():
    """Função principal."""
    if len(sys.argv) > 1:
        # Modo CLI
        path = sys.argv[1]
        auditor = SecurityAuditor(path)
        approved, message = auditor.audit()

        if approved:
            print(f"\n✅ {message}")
            sys.exit(0)
        else:
            print(f"\n❌ {message}")
            sys.exit(1)
    else:
        # Modo hook
        exit_code = run_pre_commit_hook()
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
