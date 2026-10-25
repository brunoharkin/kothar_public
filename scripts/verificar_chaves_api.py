#!/usr/bin/env python3
"""
Assistente de Verificação e Configuração de Chaves de API do Kothar.
Executado durante a instalação para alertar sobre a falta de chaves
e evitar que o usuário julgue o agente com capacidade reduzida.
"""
import os
import sys
from pathlib import Path

LLM_SERVICES = [
    {
        "nome": "Anthropic Claude (ANTHROPIC_API_KEY)",
        "var": "ANTHROPIC_API_KEY",
        "impacto": "Essencial para raciocínio analítico profundo, arquitetura e Claude Code",
        "critico": False
    },
    {
        "nome": "Google Gemini (GEMINI_API_KEY / GOOGLE_API_KEY)",
        "var": "GEMINI_API_KEY",
        "alias": "GOOGLE_API_KEY",
        "impacto": "Essencial para Gemini CLI, leitura de grandes janelas de contexto e multimodal",
        "critico": False
    },
    {
        "nome": "OpenAI (OPENAI_API_KEY)",
        "var": "OPENAI_API_KEY",
        "impacto": "Recomendado para embeddings avançados, Codex e fallback",
        "critico": False
    },
    {
        "nome": "Hugging Face (HF_TOKEN)",
        "var": "HF_TOKEN",
        "impacto": "Necessário para download de modelos locais e embeddings",
        "critico": False
    }
]

def verificar_chaves():
    print("\n" + "="*65)
    print(" 🔑 AUDITORIA DE CAPACIDADE DE IA & CHAVES DE API")
    print("="*65)
    
    # Carregar do .env se existir
    env_path = Path.cwd() / ".env"
    env_vars = dict(os.environ)
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip("'\"")

    chaves_encontradas = 0
    chaves_faltantes = []

    for svc in LLM_SERVICES:
        val = env_vars.get(svc["var"]) or (env_vars.get(svc.get("alias")) if svc.get("alias") else None)
        if val and not val.startswith("sk-ant-...") and not val.startswith("sk-...") and not val.startswith("AIzaSy..."):
            print(f" ✅ {svc['nome']}: CONFIGURADA")
            chaves_encontradas += 1
        else:
            print(f" ⚠️  {svc['nome']}: NÃO CONFIGURADA")
            print(f"    └─ Impacto: {svc['impacto']}")
            chaves_faltantes.append(svc)

    print("-" * 65)
    if chaves_faltantes:
        print("\n📢 AVISO DE CAPACIDADE DO AGENTE:")
        print(" O Kothar foi arquitetado para orquestração em alto desempenho.")
        print(" Sem as chaves de API apropriadas, certas ferramentas ou subagentes")
        print(" operarão em modo de fallback local/degradado, reduzindo o potencial")
        print(" de raciocínio da suíte.")
        print("\n💡 Dica: Você pode preencher as chaves no arquivo `.env` a qualquer momento.")
    else:
        print("\n🚀 EXCELENTE: Todas as chaves principais estão configuradas para capacidade máxima.")

    print("="*65 + "\n")
    return chaves_encontradas, len(chaves_faltantes)

if __name__ == "__main__":
    verificar_chaves()
