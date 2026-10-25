# Kothar Local AI — Guia de Reprodução

## Objetivo
Permitir recriar o Kothar local **em qualquer ambiente** (Colab, servidor, máquina local) com um único comando.

## Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 8GB | 16GB+ |
| GPU | Opcional (CPU funciona) | NVIDIA 8GB+ VRAM |
| Disco | 5GB | 10GB+ |
| SO | Linux/Mac/WSL | Linux |

**Importante:** Ollama funciona 100% em CPU. GPU só acelera.

## Instalação (5 minutos)

### 1. Instalar Ollama

```bash
# Linux/WSL
curl -fsSL https://ollama.ai/install.sh | sh

# Mac
brew install ollama

# Colab
!curl -fsSL https://ollama.ai/install.sh | sh
!ollama serve &  # Inicia servidor em background
```

### 2. Baixar modelo base

```bash
ollama pull gemma2:2b      # 1.6GB - funciona em qualquer máquina
# ou
ollama pull gemma2:9b      # 5.5GB - requer 8GB+ RAM ou GPU
```

### 3. Criar Kothar a partir deste Modelfile

```bash
# Copiar Modelfile deste repo
curl -O https://raw.githubusercontent.com/seu-repo/kothar-local/main/Modelfile.kothar-gemma

# Criar modelo customizado
ollama create kothar-gemma -f Modelfile.kothar-gemma
```

### 4. Testar

```bash
ollama run kothar-gemma "Qual seu nome?"
```

Resposta esperada: "Sou Kothar v3.0, orquestrador de desenvolvimento. Mais alguma coisa?"

## Arquivos deste Repositório

```
kothar-local/
├── Modelfile.kothar-gemma    # System prompt + few-shot curado
├── Modelfile.kothar-llama    # Modelo alternativo (llama3.2:3b)
├── Modelfile.kothar-coder    # Modelo para código (qwen2.5-coder:7b)
├── README.md                 # Este arquivo
├── training/
│   ├── generate_training_dataset.py  # Gera dataset JSONL para fine-tuning
│   ├── TRAINING_QUESTIONS.md         # 66 perguntas curadas
│   └── kothar-finetune-v2.jsonl      # Dataset gerado (82 exemplos)
└── scripts/
    ├── benchmark.sh          # Compara modelos
    └── test-modelfile.sh     # Valida Modelfile
```

## Reproduzir no Colab

```python
# No Colab
!curl -fsSL https://ollama.ai/install.sh | sh
!ollama serve &

!mkdir kothar-local
!git clone https://github.com/seu-repo/kothar-local
!cd kothar-local
!ollama pull gemma2:2b
!ollama create kothar-gemma -f Modelfile.kothar-gemma

# Testar
import requests
r = requests.post('http://localhost:11434/api/chat', json={
    'model': 'kothar-gemma:latest',
    'messages': [{'role': 'user', 'content': 'Qual seu nome?'}],
    'stream': False
})
print(r.json()['message']['content'])
```

## Versionamento dos Modelfiles

Cada mudança no system prompt deve ser **versionada**:

```
v1.0 — Versão inicial (12 exemplos few-shot)
v1.1 — Poucos exemplos, regras mais duras
v1.2 — Versão atual (8 exemplos + conhecimento do Kothar)
v2.0 — Quando tiver fine-tuning real (LoRA)
```

## Próximos Passos

1. Versionar este repositório (git init + commit)
2. Publicar no GitHub
3. Adicionar CI/CD para validar Modelfile em cada PR
4. Criar script de benchmark automático
5. Fine-tuning real (quando tiver GPU dedicada)
