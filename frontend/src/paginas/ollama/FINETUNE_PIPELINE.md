# Pipeline de Fine-Tuning Kothar

## Visão Geral

```
[Cofre] + [Traces DB] + [ChromaDB] + [Sintéticos]
                    ↓
        build_finetune_dataset.py
                    ↓
        kothar-dataset.jsonl (12+ exemplos)
                    ↓
        Gerar Modelfile (Ollama)
                    ↓
        ollama create kothar-gemma-ft
                    ↓
        Testar e iterar
```

## Passo 1: Construir Dataset

```bash
cd ~/tracing/frontend/src/paginas/ollama
python3 build_finetune_dataset.py --output ~/kothar/datasets/kothar-v1.jsonl
```

**Saída atual:** 12 exemplos de alta qualidade (8 do cofre + 4 sintéticos). À medida que você conversar com Ollama, os traces vão sendo salvos e alimentam o dataset automaticamente.

## Passo 2: Gerar Modelfile (Ollama)

O Ollama não suporta fine-tuning clássico (LoRA/full), mas permite criar **modelfiles com exemplos de System Prompt + Few-shot** que ensinam o estilo:

```bash
# Gerar Modelfile a partir do dataset
python3 generate_modelfile.py \
    --dataset ~/kothar/datasets/kothar-v1.jsonl \
    --base gemma2:2b \
    --output ~/kothar/Modelfile.kothar-gemma
```

## Passo 3: Criar Modelo Customizado

```bash
ollama create kothar-gemma-ft -f ~/kothar/Modelfile.kothar-gemma
```

## Passo 4: Testar e Iterar

```bash
# Smoke test
ollama run kothar-gemma-ft "Olá, qual o seu nome?"

# Comparar com base
ollama run gemma2:2b "Olá, qual o seu nome?"
```

## Próximos Passos (quando dataset crescer)

### LoRA Fine-Tuning (real, não só prompt)
Quando você tiver 100+ exemplos e GPU com 8GB+ VRAM:

1. **Usar llama.cpp + LoRA adapters:**
   ```bash
   # Converter modelo Ollama para GGUF
   ollama show --modelfile gemma2:2b > Modelfile.base
   
   # Fine-tune com datasets customizados
   python3 -m llamafactory.train \
       --model_name_or_path gemma2:2b \
       --dataset kothar-v1.jsonl \
       --finetuning_type lora \
       --lora_rank 8 \
       --output_dir ./kothar-lora
   ```

2. **Ou Unsloth (mais leve):**
   ```bash
   pip install unsloth
   python3 train_unsloth.py --model gemma2:2b --dataset kothar-v1.jsonl
   ```

## Estado Atual

- ✅ System prompt injetado automaticamente em `ollama.api.ts`
- ✅ Bug visual corrigido (mostra "resposta vazia" em vez de balão em branco)
- ✅ Dataset builder funcional (12 exemplos)
- ⏳ Modelfile generator (próximo passo)
- ⏳ Comparação A/B entre modelos base vs fine-tuned