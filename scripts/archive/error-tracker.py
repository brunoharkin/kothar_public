#!/usr/bin/env python3
"""
KOTHAR ERROR TRACKER
Sistema de rastreamento de erros e acertos
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Config
HOME = Path.home()
MEMORY_DIR = HOME / ".claude" / "projects" / "-home-bruno-kothar" / "memory"
COFRE_ERRORS_DIR = HOME / "Cofre" / "00_Memoria" / "Kothar" / "Erros"
ERROR_TRACKER_FILE = MEMORY_DIR / "erros" / "error-tracker.json"

class ErrorTracker:
    """Rastreador de erros e acertos"""

    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.errors = []
        self.acertos = []
        self.load_errors()

    def _ensure_dirs(self):
        """Garante que diretórios existem"""
        (MEMORY_DIR / "erros" / "acertos").mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "erros" / "padroes").mkdir(parents=True, exist_ok=True)
        COFRE_ERRORS_DIR.mkdir(parents=True, exist_ok=True)

    def load_errors(self):
        """Carrega erros salvos"""
        self._ensure_dirs()
        if ERROR_TRACKER_FILE.exists():
            with open(ERROR_TRACKER_FILE) as f:
                data = json.load(f)
                self.errors = data.get('errors', [])
                self.acertos = data.get('acertos', [])

    def save_errors(self):
        """Salva erros"""
        self._ensure_dirs()
        with open(ERROR_TRACKER_FILE, 'w') as f:
            json.dump({
                'errors': self.errors,
                'acertos': self.acertos,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def _run_cmd(self, cmd: str) -> str:
        """Executa comando shell"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.stdout else result.stderr.strip()
        except:
            return ""

    def register_error(self,
                      tipo: str,
                      descricao: str,
                      arquivo: str = "",
                      funcao: str = "",
                      o_que_fez: str = "",
                      projeto: str = "") -> str:
        """Registra um erro"""

        self._ensure_dirs()

        error_id = f"err-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.errors)+1:03d}"

        error = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "projeto": projeto or self._detect_project(),
            "sessao": self.session_id,
            "tipo": tipo,
            "descricao": descricao,
            "arquivo": arquivo,
            "funcao": funcao,
            "o_que_agente_fez": o_que_fez,
            "tentativas": 1,
            "status": "pendente",
            "solucao": None,
            "confianca_score": 100  # Inicia com 100%
        }

        self.errors.append(error)
        self.save_errors()

        # Salvar também no Cofre
        self._save_to_cofre(error)

        return error_id

    def register_acerto(self,
                       error_id: str,
                       solucao: str,
                       codigo_correto: str = "",
                       padroes: List[str] = None) -> bool:
        """Registra acerto de um erro"""

        # Encontrar erro
        for error in self.errors:
            if error['id'] == error_id:
                error['status'] = 'resolvido'
                error['solucao'] = solucao
                error['data_correcao'] = datetime.now().isoformat()
                error['codigo_correto'] = codigo_correto
                error['padroes_identificados'] = padroes or []

                # Mover para acertos
                acerto = error.copy()
                acerto['acerto_timestamp'] = datetime.now().isoformat()
                self.acertos.append(acerto)

                self.save_errors()
                self._save_acerto(acerto)
                return True

        return False

    def register_falso_positivo(self,
                               descricao: str,
                               arquivo: str = "",
                               o_que_falou: str = "") -> str:
        """Registra falso positivo (erro grave)"""

        # Reduzir score de confiança
        for error in reversed(self.errors):
            if error.get('sessao') == self.session_id and error['status'] == 'pendente':
                error['tentativas'] += 1
                error['confianca_score'] = max(0, error['confianca_score'] - 25)
                if error['tentativas'] >= 3:
                    error['status'] = 'bloqueado'
                    error['nota'] = 'REQUER INTERVENÇÃO HUMANA - 3 strikes'
                self.save_errors()
                break

        # Registrar falso positivo
        return self.register_error(
            tipo="FALSO_POSITIVO",
            descricao=f"FALSO POSITIVO: {descricao}",
            arquivo=arquivo,
            o_que_fez=o_que_falou
        )

    def get_session_summary(self) -> str:
        """Retorna resumo da sessão"""

        session_errors = [e for e in self.errors if e.get('sessao') == self.session_id]
        session_acertos = [a for a in self.acertos if a.get('sessao') == self.session_id]

        pendentes = [e for e in session_errors if e['status'] == 'pendente']
        resolvidos = [e for e in session_errors if e['status'] == 'resolvido']
        bloqueados = [e for e in session_errors if e['status'] == 'bloqueado']
        falsos_positivos = [e for e in session_errors if e['tipo'] == 'FALSO_POSITIVO']

        confianca = 100
        if falsos_positivos:
            confianca -= len(falsos_positivos) * 25
        if bloqueados:
            confianca -= len(bloqueados) * 10

        lines = []
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║              📊 ERROR TRACKER - SESSÃO ATUAL                ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append(f"║  Sessão: {self.session_id}")
        lines.append(f"║  Erros registrados: {len(session_errors)}")
        lines.append(f"║  Resolvidos: {len(resolvidos)} ✅")
        lines.append(f"║  Pendentes: {len(pendentes)} ⏳")
        lines.append(f"║  Bloqueados: {len(bloqueados)} 🚫")
        lines.append(f"║  Falsos positivos: {len(falsos_positivos)} ⚠️")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append("║  Score de Confiança: " + self._confianca_bar(confianca))
        lines.append("╚══════════════════════════════════════════════════════════════╝")

        if pendentes:
            lines.append("\n📝 Erros Pendentes:")
            for e in pendentes:
                lines.append(f"  • [{e['id']}] {e['tipo']}: {e['descricao'][:50]}...")

        if bloqueados:
            lines.append("\n🚫 Erros Bloqueados (3 strikes):")
            for e in bloqueados:
                lines.append(f"  • [{e['id']}] {e['descricao'][:50]}...")

        return '\n'.join(lines)

    def _confianca_bar(self, score: int) -> str:
        """Gera barra de confiança"""
        filled = score // 10
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        cor = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        return f"{cor} {bar} {score}%"

    def _detect_project(self) -> str:
        """Detecta projeto atual"""
        pwd = os.getcwd()
        if "crm-saphia" in pwd: return "crm-saphia"
        if "disparo-em-massa" in pwd: return "disparo-em-massa"
        if "bioleads" in pwd: return "bioleads"
        if "kothar" in pwd: return "kothar"
        return "projeto-desconhecido"

    def _save_to_cofre(self, error: Dict):
        """Salva erro no Cofre"""
        self._ensure_dirs()

        today = datetime.now()
        filename = COFRE_ERRORS_DIR / f"{today.strftime('%Y-%m')}-Erros.md"

        # Formatar entrada
        entry = f"""
## {error['id']} - {error['timestamp']}
**Tipo:** {error['tipo']}
**Projeto:** {error['projeto']}
**Arquivo:** {error.get('arquivo', 'N/A')}
**Função:** {error.get('funcao', 'N/A')}

**Descrição:** {error['descricao']}
**O que fez:** {error.get('o_que_agente_fez', 'N/A')}

**Status:** {error['status']}
---
"""

        # Adicionar ao arquivo
        with open(filename, 'a') as f:
            f.write(entry)

    def _save_acerto(self, acerto: Dict):
        """Salva acerto"""
        self._ensure_dirs()

        today = datetime.now()
        filename = MEMORY_DIR / "erros" / "acertos" / f"correcoes-{today.strftime('%Y-%m')}.md"

        entry = f"""
## {acerto['id']} - {acerto['acerto_timestamp']}
**Erro original:** {acerto['descricao']}
**Solução:** {acerto.get('solucao', 'N/A')}

**Código correto:**
```typescript
{acerto.get('codigo_correto', 'N/A')}
```

**Padrões identificados:**
"""
        for padrao in acerto.get('padroes_identificados', []):
            entry += f"- {padrao}\n"

        entry += "---\n"

        with open(filename, 'a') as f:
            f.write(entry)

    def should_block(self) -> bool:
        """Verifica se deve bloquear por muitos erros"""
        session_errors = [e for e in self.errors if e.get('sessao') == self.session_id]
        bloqueados = [e for e in session_errors if e['status'] == 'bloqueado']
        return len(bloqueados) > 0

def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python error-tracker.py <comando> [args]")
        print("Comandos:")
        print("  error <desc>     - Registrar erro")
        print("  acerto <id> <sol> - Registrar acerto")
        print("  falsepos <desc>  - Registrar falso positivo")
        print("  status          - Mostrar resumo da sessão")
        print("  list            - Listar erros pendentes")
        sys.exit(1)

    tracker = ErrorTracker()
    cmd = sys.argv[1]

    if cmd == "error":
        desc = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Erro reportado"
        eid = tracker.register_error(
            tipo="ERRO_REPORTADO",
            descricao=desc
        )
        print(f"✅ Erro registrado: {eid}")

    elif cmd == "acerto":
        if len(sys.argv) < 4:
            print("Uso: error-tracker.py acerto <id> <solucao>")
            sys.exit(1)
        eid = sys.argv[2]
        sol = sys.argv[3]
        if tracker.register_acerto(eid, sol):
            print(f"✅ Acerto registrado para {eid}")
        else:
            print(f"❌ Erro {eid} não encontrado")

    elif cmd == "falsepos":
        desc = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Falso positivo"
        eid = tracker.register_falso_positivo(desc)
        print(f"⚠️ Falso positivo registrado: {eid}")

        if tracker.should_block():
            print("\n🚫 ATENÇÃO: 3 strikes! Intervenção humana requerida.")

    elif cmd == "status":
        print(tracker.get_session_summary())

    elif cmd == "list":
        print(tracker.get_session_summary())

    else:
        print(f"Comando desconhecido: {cmd}")

if __name__ == "__main__":
    main()
