# 🧠 Guia de Modelos Ollama - Colab T4 (16GB VRAM)

## ✅ Modelos RECOMENDADOS (rodam sem travar)

### Tier 1: Ultra Leves (1-3B) - Mais rápidos, menos travamentos
| Modelo | VRAM | Uso | Contexto |
|--------|------|-----|----------|
| `llama3.2:1b` | ~1GB | Rascunhos rápidos | 8K |
| `llama3.2:3b` | ~2GB | Conversas gerais | 8K |
| `phi3:mini` | ~2.3GB | Código e lógica | 4K |
| `gemma2:2b` | ~1.5GB | Instruções | 8K |

### Tier 2: Leves (7-8B) - Bom equilíbrio
| Modelo | VRAM | Uso | Contexto |
|--------|------|-----|----------|
| `llama3.1:8b` | ~5GB | Geral, código | 128K |
| `qwen2.5:7b` | ~5GB | Código, matemática | 32K |
| `mistral:7b` | ~4.5GB | Raciocínio | 32K |
| `gemma2:9b` | ~5.5GB | Instruções | 8K |

### Tier 3: Médios (12-13B) - Podem travar com contexto grande
| Modelo | VRAM | Uso | Contexto |
|--------|------|-----|----------|
| `mistral-nemo` | ~7GB | Geral | 128K |
| `qwen2.5:14b` | ~9GB | Código complexo | 32K |

## ⚠️ Modelos PESADOS (podem travar no T4)

| Modelo | VRAM | Risco |
|--------|------|-------|
| `llama3.1:70b` | ~40GB | ❌ Não roda |
| `mixtral:8x7b` | ~26GB | ❌ Não roda |
| `codellama:34b` | ~19GB | ❌ Não roda |
| `deepseek-coder:33b` | ~18GB | ❌ Não roda |

## 🎯 Recomendações para Kothar

### Para PLANOS e IDEIAS (rápido):
```bash
~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b <ngrok_token>
```

### Para CÓDIGO e ANÁLISE (equilibrado):
```bash
~/kothar/scripts/colab_gpu_spinup.sh qwen2.5:7b <ngrok_token>
```

### Para RACIOCÍNIO COMPLEXO (com cuidado):
```bash
~/kothar/scripts/colab_gpu_spinup.sh mistral-nemo <ngrok_token>
# ⚠️ Use contexto menor (< 8K tokens)
```

## 🛡️ Dicas Anti-Travamento

1. **Sempre use `--timeout 1800`** para download de modelos
2. **Use `ollama pull`** ao invés de `ollama run` (não bloqueia)
3. **Mantenha contexto < 50% do máximo** do modelo
4. **Use `num_ctx` reduzido** se travar:
   ```bash
   ollama run llama3.2:3b --num_ctx 4096
   ```
5. **Monitore com**:
   ```bash
   colab exec -s kothar-gpu-worker 'nvidia-smi'
   ```
