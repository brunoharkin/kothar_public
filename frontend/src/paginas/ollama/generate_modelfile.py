#!/usr/bin/env python3
"""
Kothar Modelfile Generator
Converte dataset JSONL em Modelfile do Ollama (com system prompt + few-shot).

Usage:
  python3 generate_modelfile.py \
      --dataset kothar-dataset.jsonl \
      --base gemma2:2b \
      --output Modelfile.kothar-gemma

Depois:
  ollama create kothar-gemma-ft -f Modelfile.kothar-gemma
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict


def load_dataset(dataset_path: str) -> list:
    examples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def build_system_prompt(examples: list, use_few_shot: bool = True, max_few_shot: int = 3) -> str:
    """Constrói system prompt consolidado com exemplos few-shot."""

    # Extrair system prompt base (do primeiro exemplo que tenha)
    base_system = ""
    for ex in examples:
        for msg in ex.get("messages", []):
            if msg.get("role") == "system":
                base_system = msg["content"]
                break
        if base_system:
            break

    if not base_system:
        base_system = """Você é Kothar v3.0, o Maestro do Orquestro Digital. Assistente técnico especializado em desenvolvimento, análise de código, arquitetura e planejamento. Responda em português brasileiro, de forma técnica e direta."""

    if not use_few_shot:
        return base_system

    # Selecionar exemplos few-shot (priorizar qualidade alta e diversidade)
    by_quality = defaultdict(list)
    for ex in examples:
        q = ex.get("quality", "low")
        by_quality[q].append(ex)

    # Pegar os melhores (high quality primeiro)
    few_shot_candidates = by_quality.get("high", [])[:max_few_shot]

    if not few_shot_candidates:
        return base_system

    # Construir seção de few-shot
    few_shot_section = "\n\n## Exemplos de Conversas (Siga Este Estilo)\n\n"

    for i, ex in enumerate(few_shot_candidates, 1):
        messages = ex["messages"]
        # Pega system
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        # Pega primeiro user/assistant
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        assistant_msg = next((m["content"] for m in messages if m["role"] == "assistant"), "")

        if user_msg and assistant_msg:
            few_shot_section += f"### Exemplo {i}\n"
            few_shot_section += f"**Usuário:** {user_msg[:200]}\n\n"
            few_shot_section += f"**Kothar:** {assistant_msg[:500]}\n\n"

    return base_system + few_shot_section


def generate_modelfile(base_model: str, system_prompt: str, model_name: str) -> str:
    """Gera conteúdo do Modelfile Ollama."""

    # Escapar aspas duplas para Ollama
    escaped = system_prompt.replace('"""', '\\"\\"\\"')

    modelfile = f"""# Kothar v3.0 Fine-Tuned Model
# Base: {base_model}
# Gerado automaticamente via build_finetune_dataset.py

FROM {base_model}

# Temperature baixa = respostas mais determinísticas e alinhadas com Kothar
PARAMETER temperature 0.7

# Top-p para diversidade controlada
PARAMETER top_p 0.9

# Top-k para evitar tokens aleatórios
PARAMETER top_k 40

# Repetition penalty (evita loops)
PARAMETER repeat_penalty 1.1

# Num_ctx: contexto suficiente para few-shot
PARAMETER num_ctx 4096

# Stop sequences (para não gerar diálogos infinitos)
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER stop "User:"
PARAMETER stop "Human:"

# System prompt consolidado com few-shot
SYSTEM \"\"\"{escaped}\"\"\"
"""
    return modelfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="JSONL gerado por build_finetune_dataset.py")
    parser.add_argument("--base", required=True, help="Modelo base (ex: gemma2:2b, qwen2.5-coder:1.5b)")
    parser.add_argument("--output", required=True, help="Caminho do Modelfile de saída")
    parser.add_argument("--name", default=None, help="Nome do modelo customizado (auto se omitido)")
    parser.add_argument("--no-few-shot", action="store_true", help="Não incluir few-shot no system prompt")
    parser.add_argument("--max-few-shot", type=int, default=3, help="Máximo de exemplos few-shot")
    args = parser.parse_args()

    print(f"🔨 Gerando Modelfile para base={args.base}...")

    # Carregar dataset
    examples = load_dataset(args.dataset)
    print(f"   📚 {len(examples)} exemplos carregados")

    # Construir system prompt
    system_prompt = build_system_prompt(
        examples,
        use_few_shot=not args.no_few_shot,
        max_few_shot=args.max_few_shot
    )
    print(f"   ✍️  System prompt: {len(system_prompt)} chars")
    if not args.no_few_shot:
        print(f"   🎯 Few-shot: {min(args.max_few_shot, len([e for e in examples if e.get('quality') == 'high']))} exemplos")

    # Nome do modelo
    name = args.name or f"kothar-{args.base.split(':')[0]}-ft"
    print(f"   🏷️  Nome do modelo: {name}")

    # Gerar Modelfile
    modelfile_content = generate_modelfile(args.base, system_prompt, name)

    # Salvar
    output_path = Path(args.output)
    output_path.write_text(modelfile_content, encoding="utf-8")

    print(f"\n✅ Modelfile salvo em: {output_path}")
    print(f"\n📋 Próximo passo:")
    print(f"   ollama create {name} -f {output_path}")
    print(f"\n🧪 Testar:")
    print(f"   ollama run {name} \"Olá, qual o seu nome?\"")


if __name__ == "__main__":
    main()