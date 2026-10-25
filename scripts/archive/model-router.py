#!/usr/bin/env python3
"""
KOTHAR MODEL ROUTER
Roteamento inteligente de modelos de IA
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Cores
VERDE = '\033[0;32m'
AMARELO = '\033[1;33m'
VERMELHO = '\033[0;31m'
AZUL = '\033[0;34m'
CINZA = '\033[0;90m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ═══════════════════════════════════════════════════════════════════════
# MODEL TIERS
# ═══════════════════════════════════════════════════════════════════════

TIER_MODELS = {
    "tier1": {
        "anthropic": os.getenv("MODEL_TIER1", "claude-haiku-4-20250514"),
        "openai": os.getenv("MODEL_TIER1_GPT", "gpt-4o-mini"),
        "google": "gemini-flash-1.5"
    },
    "tier2": {
        "anthropic": os.getenv("MODEL_TIER2", "claude-sonnet-5-20250514"),
        "openai": os.getenv("MODEL_TIER2_GPT", "gpt-4o"),
        "google": "gemini-1.5-pro"
    },
    "tier3": {
        "anthropic": os.getenv("MODEL_TIER3", "claude-opus-5-20250514"),
        "openai": os.getenv("MODEL_TIER3_GPT", "gpt-5"),
        "google": "gemini-ultra-1.0"
    }
}

TIER_COSTS = {
    "tier1": float(os.getenv("MODEL_TIER1_COST", "0.00025")),
    "tier2": float(os.getenv("MODEL_TIER2_COST", "0.003")),
    "tier3": float(os.getenv("MODEL_TIER3_COST", "0.015"))
}

TIER_NAMES = {
    "tier1": "🟢 FAST & CHEAP",
    "tier2": "🟡 BALANCED",
    "tier3": "🔴 PREMIUM"
}

TIER_COLORS = {
    "tier1": VERDE,
    "tier2": AMARELO,
    "tier3": VERMELHO
}

# ═══════════════════════════════════════════════════════════════════════
# COMPLEXITY PATTERNS
# ═══════════════════════════════════════════════════════════════════════

PATTERNS = {
    "critical": [
        "produção", "crítico", "crítica", "urgent", "urgente",
        "imediato", "architeto", "projeta", "arquitetura",
        "deadlock", "vazamento", "security", "ataque"
    ],
    "high": [
        "bug", "corrige", "conserta", "resolve", "erro",
        "refatora", "migra", "reorganiza", "sincroniza",
        "debug", "profiling", "performance", "otimiza"
    ],
    "medium": [
        "cria", "implementa", "adiciona", "construa", "adiciona",
        "integra", "conecta", "configura", "modifica", "altera"
    ],
    "low": [
        "mostra", "lista", "explica", "traduz", "formata",
        "le", "busca", "pesquise", "verifica", "check"
    ]
}

# ═══════════════════════════════════════════════════════════════════════
# MODEL ROUTER CLASS
# ═══════════════════════════════════════════════════════════════════════

class ModelRouter:
    """Roteador de modelos de IA"""

    def __init__(self):
        self.history = []
        self.stats = {
            "tier1": 0,
            "tier2": 0,
            "tier3": 0,
            "total_cost": 0.0
        }
        self._load_history()

    def _load_history(self):
        """Carrega histórico de roteamento"""
        history_file = Path.home() / ".claude" / "projects" / "-home-bruno-kothar" / "memory" / "model-router-history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    self.stats = data.get("stats", self.stats)
            except:
                pass

    def _save_history(self):
        """Salva histórico de roteamento"""
        history_file = Path.home() / ".claude" / "projects" / "-home-bruno-kothar" / "memory" / "model-router-history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        with open(history_file, 'w') as f:
            json.dump({
                "history": self.history[-100:],  # Keep last 100
                "stats": self.stats,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)

    def classify(self, prompt: str, context: Dict = None) -> str:
        """
        Classifica a complexidade do pedido e retorna o tier.
        """

        prompt_lower = prompt.lower()
        context = context or {}
        files = context.get("arquivos_afetados", 0)

        # CRITICAL: Sempre Tier 3
        if any(kw in prompt_lower for kw in PATTERNS["critical"]):
            return "tier3"

        # HIGH: Bugs e refatorações
        if any(kw in prompt_lower for kw in PATTERNS["high"]):
            if files > 2:
                return "tier3"
            return "tier2"

        # MEDIUM: Features e implementações
        if any(kw in prompt_lower for kw in PATTERNS["medium"]):
            if files > 5:
                return "tier3"
            return "tier2"

        # LOW: Comandos simples
        if any(kw in prompt_lower for kw in PATTERNS["low"]):
            return "tier1"

        # Comando direto
        words = prompt.split()
        if len(words) <= 3:
            return "tier1"

        # Default
        return "tier2"

    def route(self, prompt: str, context: Dict = None, provider: str = None) -> Dict:
        """
        Roteia para o modelo apropriado baseado no prompt.
        """

        context = context or {}
        provider = provider or os.getenv("PREFERRED_PROVIDER", "anthropic")
        tier = self.classify(prompt, context)

        # Selecionar modelo
        model = TIER_MODELS[tier].get(provider, TIER_MODELS[tier]["anthropic"])

        # Estimar custo (assumindo ~500 tokens por requisição)
        estimated_tokens = 500
        cost = TIER_COSTS[tier] * estimated_tokens

        # Gerar razão
        reason = self._get_reason(tier, prompt)

        # Registrar
        result = {
            "tier": tier,
            "tier_name": TIER_NAMES[tier],
            "model": model,
            "provider": provider,
            "cost_estimate": cost,
            "reason": reason,
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "timestamp": datetime.now().isoformat()
        }

        # Atualizar stats
        self.stats[tier] += 1
        self.stats["total_cost"] += cost
        self.history.append(result)
        self._save_history()

        return result

    def _get_reason(self, tier: str, prompt: str) -> str:
        """Gera razão para seleção do tier"""
        prompt_lower = prompt.lower()

        if tier == "tier1":
            for kw in PATTERNS["low"]:
                if kw in prompt_lower:
                    return f"Comando simples: '{kw}'"
            return "Comando direto (< 3 palavras)"

        elif tier == "tier2":
            for kw in PATTERNS["medium"]:
                if kw in prompt_lower:
                    return f"Implementação: '{kw}'"
            for kw in PATTERNS["high"]:
                if kw in prompt_lower:
                    return f"Correção/Refatoração simples: '{kw}'"
            return "Tarefa média (padrão)"

        else:  # tier3
            for kw in PATTERNS["critical"]:
                if kw in prompt_lower:
                    return f"Tarefa CRÍTICA: '{kw}'"
            for kw in PATTERNS["high"]:
                if kw in prompt_lower:
                    return f"Correção/Refatoração COMPLEXA: '{kw}'"
            return "Alta complexidade ou múltiplos arquivos"

    def print_result(self, result: Dict):
        """Imprime resultado do roteamento"""

        tier_color = TIER_COLORS[result["tier"]]

        print("")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              🤖 MODEL ROUTER                              ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  {tier_color}{BOLD}{result['tier_name']}{RESET}")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  Modelo: {AZUL}{result['model']}{RESET}")
        print(f"║  Provider: {result['provider']}")
        print(f"║  Custo estimado: ${result['cost_estimate']:.4f}")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  {CINZA}{result['reason']}{RESET}")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("")

    def print_stats(self):
        """Imprime estatísticas de uso"""

        total = sum([self.stats.get(t, 0) for t in ["tier1", "tier2", "tier3"]])

        print("")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              📊 MODEL ROUTER - ESTATÍSTICAS              ║")
        print("╠══════════════════════════════════════════════════════════════╣")

        if total == 0:
            print("║  Nenhum roteamento registrado ainda.")
        else:
            # Barra de distribuição
            t1 = self.stats.get("tier1", 0)
            t2 = self.stats.get("tier2", 0)
            t3 = self.stats.get("tier3", 0)

            t1_pct = (t1 / total) * 100
            t2_pct = (t2 / total) * 100
            t3_pct = (t3 / total) * 100

            bar = (
                f"{VERDE}{'█' * int(t1_pct / 5)}{RESET}"
                f"{AMARELO}{'█' * int(t2_pct / 5)}{RESET}"
                f"{VERMELHO}{'█' * int(t3_pct / 5)}{RESET}"
            )

            print(f"║  {bar}  {total} requests{RESET}")
            print("╠══════════════════════════════════════════════════════════════╣")
            print(f"║  🟢 Tier 1 (Fast):  {t1:4d} ({t1_pct:5.1f}%)")
            print(f"║  🟡 Tier 2 (Medium): {t2:4d} ({t2_pct:5.1f}%)")
            print(f"║  🔴 Tier 3 (Premium): {t3:4d} ({t3_pct:5.1f}%)")
            print("╠══════════════════════════════════════════════════════════════╣")
            print(f"║  💰 Custo total estimado: ${self.stats['total_cost']:.4f}")

            # Economia vs usar sempre Sonnet
            always_sonnet_cost = total * TIER_COSTS["tier2"] * 500
            economy = always_sonnet_cost - self.stats['total_cost']
            economy_pct = (economy / always_sonnet_cost) * 100 if always_sonnet_cost > 0 else 0

            print(f"║  💡 Economia vs usar Sonnet sempre: ${economy:.4f} ({economy_pct:.1f}%)")

        print("╚══════════════════════════════════════════════════════════════╝")
        print("")

    def print_config(self):
        """Imprime configuração atual"""

        print("")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              ⚙️  MODEL ROUTER - CONFIGURAÇÃO             ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  Provider padrão: {os.getenv('PREFERRED_PROVIDER', 'anthropic')}")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║  Modelos por tier:")
        print(f"║    🟢 Tier 1: {TIER_MODELS['tier1']['anthropic']}")
        print(f"║    🟡 Tier 2: {TIER_MODELS['tier2']['anthropic']}")
        print(f"║    🔴 Tier 3: {TIER_MODELS['tier3']['anthropic']}")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║  Custos por 1K tokens:")
        print(f"║    🟢 Tier 1: ${TIER_COSTS['tier1']:.6f}")
        print(f"║    🟡 Tier 2: ${TIER_COSTS['tier2']:.6f}")
        print(f"║    🔴 Tier 3: ${TIER_COSTS['tier3']:.6f}")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("")

        # Verificar API keys
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              🔑 API KEYS STATUS                            ║")
        print("╠══════════════════════════════════════════════════════════════╣")

        keys = [
            ("ANTHROPIC_API_KEY", "Claude"),
            ("OPENAI_API_KEY", "GPT"),
            ("GOOGLE_API_KEY", "Gemini")
        ]

        for env_var, name in keys:
            key = os.getenv(env_var, "")
            if key:
                masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                print(f"║  ✅ {name}: {masked}")
            else:
                print(f"║  ❌ {name}: Não configurado")

        print("╚══════════════════════════════════════════════════════════════╝")
        print("")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python model-router.py <comando> [args]")
        print("")
        print("Comandos:")
        print("  route \"seu prompt aqui\"  - Roteia um prompt")
        print("  stats                    - Mostra estatísticas")
        print("  config                   - Mostra configuração")
        print("  test                     - Testa com prompts de exemplo")
        sys.exit(1)

    router = ModelRouter()
    cmd = sys.argv[1]

    if cmd == "route":
        if len(sys.argv) < 3:
            print("Uso: python model-router.py route \"seu prompt\"")
            sys.exit(1)

        prompt = ' '.join(sys.argv[2:])
        context = {}

        # Parse context if provided
        # Ex: route "prompt" --files 5
        if "--files" in sys.argv:
            idx = sys.argv.index("--files")
            if idx + 1 < len(sys.argv):
                context["arquivos_afetados"] = int(sys.argv[idx + 1])

        result = router.route(prompt, context)
        router.print_result(result)

    elif cmd == "stats":
        router.print_stats()

    elif cmd == "config":
        router.print_config()

    elif cmd == "test":
        print("\n🧪 Testando Model Router...\n")

        test_prompts = [
            ("ls", "Comando simples"),
            ("mostra logs de erro", "Leitura"),
            ("explica o que esse código faz", "Análise"),
            ("cria endpoint de users", "Feature simples"),
            ("implementa autenticação JWT", "Feature média"),
            ("corrige bug no login", "Bug simples"),
            ("corrige bug crítico de autenticação", "Bug crítico"),
            ("refatora código de auth", "Refatoração"),
            ("projeta arquitetura de microsserviços", "Arquitetura"),
            ("debug deadlock em produção", "Debug crítico"),
        ]

        print("Prompt".ljust(50) + "Tier".ljust(20) + "Modelo")
        print("=" * 100)

        for prompt, desc in test_prompts:
            result = router.route(prompt)
            tier_emoji = "🟢" if result["tier"] == "tier1" else "🟡" if result["tier"] == "tier2" else "🔴"
            model_short = result["model"].replace("claude-", "").replace("-20250514", "")
            print(f"{prompt[:48]:50} {tier_emoji} {result['tier']:15} {model_short}")

        print("")
        router.print_stats()

    else:
        print(f"Comando desconhecido: {cmd}")


if __name__ == "__main__":
    main()
