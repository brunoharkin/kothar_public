#!/usr/bin/env python3
"""
KOTHAR CONTEXT PLANNER
Análise contextual completa + geração de plano detalhado
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Cores
VERDE = '\033[0;32m'
AMARELO = '\033[1;33m'
VERMELHO = '\033[0;31m'
AZUL = '\033[0;34m'
CINZA = '\033[0;90m'
RESET = '\033[0m'
BOLD = '\033[1m'

class ContextPlanner:
    """Planejador de contexto completo"""

    def __init__(self):
        self.pwd = os.getcwd()
        self.project = self._detect_project()
        self.results = {}

    def _detect_project(self) -> str:
        """Detecta projeto pelo pwd"""
        path = self.pwd.lower()
        projects = {
            'disparo-em-massa': 'disparo-em-massa',
            'crm-saphia': 'crm-saphia',
            'bioleads': 'bioleads',
            'ratoflix': 'ratoflix',
            'kothar': 'kothar',
            'linkdabio': 'linkdabio',
            'chronodesk': 'chronodesk',
        }
        for key, name in projects.items():
            if key in path:
                return name
        return "projeto-desconhecido"

    def _run_cmd(self, cmd: str, timeout: int = 10) -> str:
        """Executa comando shell"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip() if result.stdout else result.stderr.strip()
        except subprocess.TimeoutExpired:
            return "[timeout]"
        except:
            return ""

    def analyze(self, prompt: str) -> str:
        """Executa análise completa"""

        output = []

        # Header
        output.append(self._header())
        output.append(f"{AZUL}📥 PROMPT ORIGINAL:{RESET}")
        output.append(f'{CINZA}"{prompt}"{RESET}')
        output.append(self._separator())

        # Classificação
        classification = self._classify(prompt)
        output.append(f"{AZUL}🎯 CLASSIFICAÇÃO:{RESET}")
        output.append(f"• Tipo: {BOLD}{classification['tipo']}{RESET}")
        output.append(f"• Complexidade: {self._complexidade_cor(classification['complexidade'])} {classification['complexidade']}{RESET}")
        output.append(f"• Urgência: {classification['urgencia']}")
        output.append(f"• Gatilho: {classification['gatilho']}")
        output.append(self._separator())

        # Mapa de arquivos
        files_map = self._find_related_files(prompt)
        self.results['files'] = files_map
        output.append(f"{AZUL}📁 MAPA DE ARQUIVOS{RESET}")
        output.append(self._map_files_output(files_map))
        output.append(self._separator())

        # Histórico
        history = self._get_history()
        output.append(f"{AZUL}🧠 CONTEXTO HISTÓRICO:{RESET}")
        output.append(history)
        output.append(self._separator())

        # Plano de ação
        plan = self._generate_plan(prompt, classification, files_map)
        output.append(f"{AZUL}✅ PLANO DE AÇÃO{RESET}")
        output.append(plan)
        output.append(self._separator())

        # Riscos
        risks = self._identify_risks(prompt, files_map)
        output.append(f"{AMARELO}⚠️ RISCOS IDENTIFICADOS:{RESET}")
        for risk in risks:
            output.append(f"• {risk}")
        output.append(self._separator())

        # Footer com aprovação
        output.append(self._footer())

        return '\n'.join(output)

    def _header(self) -> str:
        return f"""
{BOLD}{'═' * 70}{RESET}
{AZUL}{BOLD}🔍 CONTEXT PLANNER — ANÁLISE COMPLETA{RESET}
{BOLD}{'═' * 70}{RESET}
"""

    def _separator(self) -> str:
        return f"{CINZA}{'─' * 70}{RESET}"

    def _footer(self) -> str:
        return f"""
{BOLD}{'═' * 70}{RESET}
{AZUL}APROVA ESTE PLANO?{RESET}
  {VERDE}[sim]{RESET} → Executar plano completo
  {VERMELHO}[não]{RESET} → Cancelar
  {AMARELO}[editar]{RESET} → Modificar passos
{BOLD}{'═' * 70}{RESET}
"""

    def _classify(self, prompt: str) -> Dict:
        """Classifica o prompt"""
        prompt_lower = prompt.lower()

        # Tipos
        if any(w in prompt_lower for w in ['corrige', 'conserta', 'resolve', 'bug', 'erro', 'quebrou']):
            tipo = "CORREÇÃO DE BUG"
            gatilho = "corrige/bug/erro"
        elif any(w in prompt_lower for w in ['cria', 'implementa', 'adiciona', 'construa']):
            tipo = "IMPLEMENTAÇÃO DE FEATURE"
            gatilho = "cria/implementa"
        elif any(w in prompt_lower for w in ['refatora', 'migra', 'reorganiza']):
            tipo = "REFATORAÇÃO"
            gatilho = "refatora/migra"
        elif any(w in prompt_lower for w in ['analisa', 'revisa', 'audita']):
            tipo = "ANÁLISE/AUDITORIA"
            gatilho = "analisa/revisa"
        elif any(w in prompt_lower for w in ['testa', 'teste']):
            tipo = "TESTE"
            gatilho = "testa"
        else:
            tipo = "OUTRO"
            gatilho = "geral"

        # Complexidade
        words_count = len(prompt.split())
        if words_count <= 5:
            complexidade = "BAIXA"
        elif words_count <= 15:
            complexidade = "MÉDIA"
        else:
            complexidade = "ALTA"

        # Urgência
        if any(w in prompt_lower for w in ['urgente', 'agora', 'imediato']):
            urgencia = f"{VERMELHO}ALTA{RESET}"
        elif tipo == "CORREÇÃO DE BUG":
            urgencia = f"{AMARELO}MÉDIA{RESET}"
        else:
            urgencia = f"{VERDE}BAIXA{RESET}"

        return {
            'tipo': tipo,
            'gatilho': gatilho,
            'complexidade': complexidade,
            'urgencia': urgencia,
            'words_count': words_count
        }

    def _complexidade_cor(self, nivel: str) -> str:
        cores = {
            'BAIXA': VERDE,
            'MÉDIA': AMARELO,
            'ALTA': VERMELHO
        }
        return cores.get(nivel, CINZA)

    def _find_related_files(self, prompt: str) -> List[Dict]:
        """Encontra arquivos relacionados ao prompt"""
        files = []
        prompt_lower = prompt.lower()

        # Extrair palavras-chave do prompt
        keywords = []
        for word in prompt.split():
            clean = re.sub(r'[^\w]', '', word.lower())
            if len(clean) > 3 and clean not in ['para', 'esse', 'essa', 'como', 'deve', 'que', 'uma', 'fazer', 'ser', 'tem']:
                keywords.append(clean)

        # Buscar arquivos no projeto
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.java', '.cs']

        for ext in extensions:
            cmd = f'find . -type f -name "*{ext}" 2>/dev/null | head -30'
            result = self._run_cmd(cmd)

            for line in result.split('\n'):
                if not line or line.startswith('./'):
                    continue

                # Verificar se arquivo combina com keywords
                for kw in keywords:
                    if kw.lower() in line.lower():
                        files.append({
                            'path': line,
                            'keyword': kw,
                            'type': self._guess_type(line)
                        })
                        break

        # Se não encontrou, buscar por padrões comuns
        if not files:
            patterns = ['login', 'logout', 'auth', 'user', 'dashboard', 'pagina', 'servico', 'rota']
            for pattern in patterns:
                if pattern in prompt_lower:
                    cmd = f'grep -r -l "{pattern}" --include="*.ts" --include="*.tsx" --include="*.py" . 2>/dev/null | head -10'
                    result = self._run_cmd(cmd)
                    for line in result.split('\n'):
                        if line and not line.startswith('./'):
                            files.append({
                                'path': line,
                                'keyword': pattern,
                                'type': self._guess_type(line)
                            })

        # Limitado a 10 arquivos
        return files[:10]

    def _guess_type(self, path: str) -> str:
        """Adivinha o tipo do arquivo"""
        if 'service' in path or 'servico' in path:
            return "🛠️ Serviço"
        elif 'route' in path or 'rota' in path:
            return "🛤️ Rota"
        elif 'page' in path or 'pagina' in path:
            return "📄 Página"
        elif 'component' in path or 'componente' in path:
            return "🧩 Componente"
        elif 'context' in path:
            return "🔗 Context"
        elif 'hook' in path:
            return "⚓ Hook"
        elif 'model' in path or 'schema' in path:
            return "📊 Modelo"
        elif 'test' in path or 'spec' in path:
            return "🧪 Teste"
        elif 'config' in path or 'env' in path:
            return "⚙️ Config"
        elif 'middleware' in path:
            return "🔄 Middleware"
        elif 'controller' in path:
            return "🎮 Controller"
        else:
            return "📄 Arquivo"

    def _map_files_output(self, files: List[Dict]) -> str:
        """Formata saída do mapa de arquivos"""
        if not files:
            return "  Nenhum arquivo relacionado encontrado no projeto."

        output = []
        for i, f in enumerate(files, 1):
            status = self._check_file_status(f['path'])
            output.append(f"  {i}️⃣ {f['type']}: {CINZA}{f['path']}{RESET}")
            output.append(f"     └─ Keyword: {AMARELO}{f['keyword']}{RESET} {status}")
        return '\n'.join(output)

    def _check_file_status(self, path: str) -> str:
        """Verifica status do arquivo"""
        if not os.path.exists(path):
            return f"{VERDE}[NOVO]{RESET}"
        if self._run_cmd(f'git diff {path} 2>/dev/null'):
            return f"{AMARELO}[MODIFICADO]{RESET}"
        return f"{VERDE}[OK]{RESET}"

    def _get_history(self) -> str:
        """Coleta histórico relevante"""
        output = []

        # Git log
        commits = self._run_cmd("git log --oneline -5 2>/dev/null")
        if commits:
            output.append("  📅 Últimos commits:")
            for line in commits.split('\n')[:3]:
                if line:
                    output.append(f"     • {CINZA}{line}{RESET}")

        # Git status
        status = self._run_cmd("git status --short 2>/dev/null")
        if status:
            output.append(f"  📦 Status: {AMARELO}{status.count(chr(10))+1} arquivo(s) modificado(s){RESET}")

        # Branch
        branch = self._run_cmd("git branch --show-current 2>/dev/null")
        if branch:
            output.append(f"  🌿 Branch: {AZUL}{branch}{RESET}")

        # Diário
        diary = self._get_diary()
        if diary:
            output.append(f"  📝 Diário do dia:")
            for line in diary.split('\n')[:3]:
                if line.strip():
                    output.append(f"     {line}")

        return '\n'.join(output) if output else "  Sem histórico disponível."

    def _get_diary(self) -> str:
        """Busca diário do dia"""
        home = Path.home()
        today = datetime.now()
        diary_path = home / "Cofre" / "00_Memoria" / "Diarias" / today.strftime("%Y-%m") / f"{today.strftime('%Y-%m-%d')}.md"

        if diary_path.exists():
            with open(diary_path) as f:
                lines = f.readlines()
                # Pegar primeiras linhas significativas
                content = []
                for line in lines[:10]:
                    if line.strip() and not line.startswith('#'):
                        content.append(line.strip())
                        if len(content) >= 3:
                            break
                return '\n'.join(content)
        return ""

    def _generate_plan(self, prompt: str, classification: Dict, files: List[Dict]) -> str:
        """Gera plano de ação"""

        tipo = classification['tipo']
        output = []

        if tipo == "CORREÇÃO DE BUG":
            steps = [
                ("Reproduzir o erro", "Testar o fluxo que apresenta o bug", files[0]['path'] if files else ""),
                ("Identificar causa raiz", "Analisar logs e código-fonte", files[0]['path'] if files else ""),
                ("Corrigir código", "Implementar correção no arquivo identificado", files[0]['path'] if files else ""),
                ("Testar correção", "Executar o mesmo fluxo para validar", files[0]['path'] if files else ""),
                ("Commitar changes", "git add + commit + push", "commits"),
            ]
        elif tipo == "IMPLEMENTAÇÃO DE FEATURE":
            steps = [
                ("Analisar requisitos", "Ler spec do projeto e entender necessidade", "specs/"),
                ("Mapear estrutura", "Identificar onde criar/modificar arquivos", "arquitetura"),
                ("Implementar backend", "Criar API/roteiro se necessário", files[0]['path'] if files else ""),
                ("Implementar frontend", "Criar interface se necessário", files[0]['path'] if files else ""),
                ("Testar feature", "Validar fluxo completo", "testes"),
                ("Commitar changes", "git add + commit + push", "commits"),
            ]
        elif tipo == "REFATORAÇÃO":
            steps = [
                ("Mapear código atual", "Identificar arquivos a refatorar", files[0]['path'] if files else ""),
                ("Planejar mudanças", "Definir nova estrutura", "arquitetura"),
                ("Implementar refatoração", "Reescrever código", files[0]['path'] if files else ""),
                ("Testar", "Validar que funcionalidad permanece", "testes"),
                ("Commitar", "git add + commit", "commits"),
            ]
        else:
            steps = [
                ("Analisar contexto", "Entender necessidade", ""),
                ("Executar ação", "Implementar conforme classificação", ""),
                ("Validar resultado", "Testar resultado", ""),
            ]

        for i, (title, action, file) in enumerate(steps, 1):
            output.append(f"  {i}️⃣ [ ] {BOLD}{title}{RESET}")
            output.append(f"      • Ação: {action}")
            if file:
                output.append(f"      • Arquivo: {CINZA}{file}{RESET}")

        return '\n'.join(output)

    def _identify_risks(self, prompt: str, files: List[Dict]) -> List[str]:
        """Identifica riscos"""
        risks = []

        if not files:
            risks.append("Nenhum arquivo encontrado - pode ser projeto novo ou path incorreto")

        if self._run_cmd("git status --short 2>/dev/null"):
            risks.append("Há mudanças não commitadas - podem ser sobrescritas")

        if self._classify(prompt)['complexidade'] == 'ALTA':
            risks.append("Alta complexidade - pode afetar mais arquivos que o esperado")

        return risks if risks else ["Nenhum risco identificado"]

def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python context-planner.py \"seu prompt aqui\"")
        sys.exit(1)

    prompt = ' '.join(sys.argv[1:])
    planner = ContextPlanner()
    result = planner.analyze(prompt)
    print(result)

if __name__ == "__main__":
    main()
