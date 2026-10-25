#!/usr/bin/env python3
"""
KOTHAR PROMPT ENRICHER
Busca contexto em múltiplas fontes e injeta no prompt
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Config
KOTHAR_DIR = Path.home() / "kothar"
MEMORY_DIR = Path.home() / ".claude" / "projects"
COFRE_DIR = Path.home() / "Cofre"

class PromptEnricher:
    """Enriquecedor de prompts com busca contextual"""

    def __init__(self):
        self.project = self._detect_project()
        self.context = {}

    def _detect_project(self) -> str:
        """Detecta o projeto atual pelo pwd"""
        pwd = os.getcwd()
        if "disparo-em-massa" in pwd:
            return "disparo-em-massa"
        elif "crm-saphia" in pwd:
            return "crm-saphia"
        elif "bioleads" in pwd:
            return "bioleads"
        elif "ratoflix" in pwd:
            return "ratoflix"
        elif "kothar" in pwd:
            return "kothar"
        return "desconhecido"

    def _run_cmd(self, cmd: str) -> str:
        """Executa comando shell"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip()
        except:
            return ""

    def enrich(self, prompt: str) -> str:
        """Enriquece o prompt com contexto"""

        # Coleta contexto de todas as fontes
        self._collect_git_context()
        self._collect_project_structure()
        self._collect_memory_context()
        self._collect_specs()
        self._collect_diario()

        # Monta prompt enriquecido
        enriched = self._build_enriched_prompt(prompt)
        return enriched

    def _collect_git_context(self):
        """Coleta contexto do git"""
        self.context['git'] = {
            'branch': self._run_cmd("git branch --show-current 2>/dev/null"),
            'status': self._run_cmd("git status --short 2>/dev/null"),
            'remote': self._run_cmd("git remote -v 2>/dev/null"),
            'last_commit': self._run_cmd("git log -1 --format='%h - %s' 2>/dev/null"),
        }

    def _collect_project_structure(self):
        """Coleta estrutura do projeto"""
        # Lista arquivos principais (limitado)
        structure = self._run_cmd("find . -maxdepth 3 -type f \\( -name '*.ts' -o -name '*.tsx' -o -name '*.py' -o -name '*.md' \\) 2>/dev/null | head -50")
        self.context['structure'] = structure

        # package.json ou requirements.txt
        if Path("package.json").exists():
            with open("package.json") as f:
                data = json.load(f)
                self.context['stack'] = data.get('dependencies', {}).keys()
        elif Path("requirements.txt").exists():
            with open("requirements.txt") as f:
                self.context['stack'] = f.read().strip().split('\n')

    def _collect_memory_context(self):
        """Coleta contexto das memórias"""
        memory_path = MEMORY_DIR / f"-home-bruno-{self.project}"
        if memory_path.exists():
            memories = list(memory_path.glob("*.md"))[-3:]  # Últimas 3
            self.context['memories'] = []
            for m in memories:
                with open(m) as f:
                    self.context['memories'].append(f.read()[:500])
        else:
            self.context['memories'] = []

    def _collect_specs(self):
        """Coleta specs do projeto"""
        spec_path = KOTHAR_DIR / "specs" / "internos" / self.project
        if spec_path.exists():
            specs = list(spec_path.glob("*.md"))
            self.context['specs'] = [s.name for s in specs]
        else:
            self.context['specs'] = []

    def _collect_diario(self):
        """Coleta diário do dia"""
        today = datetime.now()
        diario_path = COFRE_DIR / "00_Memoria" / "Diarias" / today.strftime("%Y-%m") / today.strftime("%Y-%m-%d.md")
        if diario_path.exists():
            with open(diario_path) as f:
                content = f.read()
                self.context['diario'] = content[:1000]
        else:
            self.context['diario'] = ""

    def _build_enriched_prompt(self, prompt: str) -> str:
        """Monta prompt enriquecido"""

        lines = []
        lines.append("═" * 70)
        lines.append("📥 PROMPT ORIGINAL")
        lines.append("═" * 70)
        lines.append(f'"{prompt}"')
        lines.append("")

        # Contexto do projeto
        lines.append("═" * 70)
        lines.append("🎯 CONTEXTO DO PROJETO")
        lines.append("═" * 70)
        lines.append(f"**Projeto:** {self.project}")
        lines.append(f"**pwd:** {os.getcwd()}")

        if self.context.get('git', {}).get('branch'):
            lines.append(f"**Branch:** {self.context['git']['branch']}")
        if self.context.get('git', {}).get('last_commit'):
            lines.append(f"**Último commit:** {self.context['git']['last_commit']}")
        lines.append("")

        # Stack tecnológica
        if self.context.get('stack'):
            lines.append(f"**Stack:** {', '.join(list(self.context['stack'])[:5])}")
            lines.append("")

        # Estrutura
        if self.context.get('structure'):
            lines.append("**Estrutura (excerpt):**")
            lines.append("```")
            for line in self.context['structure'].split('\n')[:20]:
                lines.append(line)
            lines.append("```")
            lines.append("")

        # Specs
        if self.context.get('specs'):
            lines.append("**Specs disponíveis:**")
            for spec in self.context['specs']:
                lines.append(f"  - {spec}")
            lines.append("")

        # Histórico / Diário
        if self.context.get('diario'):
            lines.append("═" * 70)
            lines.append("📅 DIÁRIO DO DIA (excerpt)")
            lines.append("═" * 70)
            lines.append(self.context['diario'][:500])
            lines.append("")

        # Memórias recentes
        if self.context.get('memories'):
            lines.append("═" * 70)
            lines.append("🧠 MEMÓRIAS RELEVANTES")
            lines.append("═" * 70)
            for i, mem in enumerate(self.context['memories'], 1):
                lines.append(f"**Memória {i}:**")
                lines.append(mem[:200] + "...")
                lines.append("")
            lines.append("")

        # Git status
        if self.context.get('git', {}).get('status'):
            status = self.context['git']['status']
            if status:
                lines.append("═" * 70)
                lines.append("📦 GIT STATUS")
                lines.append("═" * 70)
                lines.append(status)
                lines.append("")

        # Prompt enriquecido
        lines.append("═" * 70)
        lines.append("✅ PROMPT ENRIQUECIDO")
        lines.append("═" * 70)
        lines.append(f'"{prompt}"')
        lines.append("")
        lines.append("Com base no contexto acima, execute a ação com:")
        lines.append("- Foco no projeto: " + self.project)
        lines.append("- Estrutura: backend/frontend/")
        lines.append("- Nomenclatura: Português, PascalCase para componentes")

        return '\n'.join(lines)

def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python prompt-enricher.py \"seu prompt aqui\"")
        sys.exit(1)

    prompt = ' '.join(sys.argv[1:])
    enricher = PromptEnricher()
    result = enricher.enrich(prompt)
    print(result)

if __name__ == "__main__":
    main()
