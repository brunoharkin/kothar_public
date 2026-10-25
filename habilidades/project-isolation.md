---
name: project-isolation
versao: 1.0
data: 2026-06-28
projeto: kothar
tipo: correcao
descricao: Sistema de isolamento rígido de projetos - só altera na pasta raiz
---

# 🚫 ISOLAMENTO RÍGIDO DE PROJETOS v2.1.2

> **Problema:** O Kothar mistura projetos, usando o mesmo banco de dados e código entre diferentes projetos

## Regra de Ouro

```
🎯 PRINCÍPIO BÁSICO:
- CADA PROJETO TEM SUA PRÓPRIA PASTA RAIZ
- SÓ ALTERA ARQUIVOS DENTRO DA PASTA RAIZ DO PROJETO ATUAL
- PODE BUSCAR REFERÊNCIAS, MAS NÃO PODE MODIFICAR OUTROS PROJETOS
```

## Sistema de Controle

### 1. Detecção de Projeto Atual

```bash
# Verificar pasta raiz autorizada
PROJECT_ROOT=$(pwd)
AUTHORIZED_ROOTS="/home/bruno/Cofre/chronodesk /home/bruno/Cofre/orby /home/bruno/Cofre/ugarit"

if [[ ! "$AUTHORIZED_ROOTS" =~ "$PROJECT_ROOT" ]]; then
    echo "❌ Bruno: entre na pasta do projeto para trabalhar nele"
    exit 1
fi
```

### 2. Hooks de Isolamento

#### pre-project-isolation.sh
```bash
#!/bin/bash
# Verifica se está na pasta raiz do projeto

PROJECT_NAME=$(basename "$PWD")
PROJECT_ROOT="$PWD"

# Lista de projetos autorizados
AUTHORIZED_PROJECTS=("chronodesk" "orby" "ugarit" "farmacia" "agents-portfolio" "portfolio-agentes")

if [[ ! " ${AUTHORIZED_PROJECTS[@]} " =~ " $PROJECT_NAME " ]]; then
    echo "❌ Projeto não autorizado: $PROJECT_NAME"
    echo "📋 Projetos autorizados: ${AUTHORIZED_PROJECTS[*]}"
    exit 1
fi

# Salvar estado atual
echo "$PROJECT_ROOT" > ~/.kothar/state/current-project-root
echo "$PROJECT_NAME" > ~/.kothar/state/current-project-name

echo "✅ Projeto detectado: $PROJECT_NAME (raiz: $PROJECT_ROOT)"
```

#### post-file-access.sh
```bash
#!/bin/bash
# Verifica se o arquivo acessado está no projeto atual

PROJECT_ROOT=$(cat ~/.kothar/state/current-project-root 2>/dev/null || echo "")
FILE_PATH="$1"

if [[ -n "$PROJECT_ROOT" && "$FILE_PATH" != "$PROJECT_ROOT"* ]]; then
    echo "❌ ACESSO FORA DO PROJETO!"
    echo "📁 Tentou acessar: $FILE_PATH"
    echo "📁 Projeto atual: $PROJECT_ROOT"
    echo "🚫 Bruno: Kothar tentou acessar arquivo fora do projeto atual!"
    exit 1
fi
```

### 3. Sistema de Busca Isolada

```python
# project-reference-searcher.py
import os
import json
from pathlib import Path

def search_reference(project_name, component_name):
    """
    Busca referência em outro projeto SEM modificar
    Retorna cópia do componente para uso no projeto atual
    """
    
    # Projetos disponíveis para busca
    projects_root = "/home/bruno/Cofre"
    available_projects = ["chronodesk", "orby", "ugarit"]
    
    if project_name not in available_projects:
        raise ValueError(f"Projeto não encontrado: {project_name}")
    
    # Buscar componente
    source_path = Path(projects_root) / project_name / component_name
    
    if not source_path.exists():
        raise FileNotFoundError(f"Componente não encontrado: {source_path}")
    
    # Retornar cópia (não modificar original)
    return source_path.read_text()

# Uso seguro
def safe_clone_reference(source_project, component_name, target_project):
    """
    Clona referência de forma segura
    """
    try:
        reference_content = search_reference(source_project, component_name)
        
        # Criar no projeto atual (não no fonte)
        target_path = Path("/home/bruno/Cofre") / target_project / component_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar cópia
        target_path.write_text(reference_content)
        
        return f"✅ Referência clonada de {source_project} para {target_project}"
        
    except Exception as e:
        return f"❌ Erro ao clonar referência: {str(e)}"
```

### 4. Regras de Acesso

```markdown
✅ PERMITIDO:
- Ler arquivos dentro da pasta raiz do projeto atual
- Buscar referências de outros projetos (somente leitura)
- Criar arquivos dentro da pasta raiz do projeto atual
- Modificar arquivos dentro da pasta raiz do projeto atual

❌ PROIBIDO:
- Modificar arquivos fora da pasta raiz do projeto atual
- Acessar banco de dados de outros projetos
- Compartilhar código entre projetos (exceto via APIs)
- Criar arquivos fora da pasta raiz do projeto atual

🚫 EXCEÇÕES (apenas com aprovação explícita):
- Conexão via API entre projetos (ex: chron ↔ orby)
- Compartilhamento de configurações globais
```

### 5. Monitoramento de Acesso

```bash
#!/bin/bash
# access-monitor.sh - Monitora acessos a arquivos

LOG_FILE="$HOME/.kothar/logs/access-monitor.jsonl"
PROJECT_ROOT=$(cat ~/.kothar/state/current-project-root 2>/dev/null || echo "unknown")

log_access() {
    local action="$1"
    local file="$2"
    local timestamp=$(date -Iseconds)
    
    echo "[$timestamp] {\"action\": \"$action\", \"file\": \"$file\", \"project\": \"$PROJECT_ROOT\"}" >> "$LOG_FILE"
}

# Verificar acesso
if [[ "$1" == "read" ]]; then
    if [[ "$2" != "$PROJECT_ROOT"* ]]; then
        echo "🚫 TENTATIVA DE LEITURA FORA DO PROJETO!"
        log_access "READ_ATTEMPT_OUTSIDE" "$2"
        exit 1
    fi
    log_access "READ" "$2"
fi

if [[ "$1" == "write" ]]; then
    if [[ "$2" != "$PROJECT_ROOT"* ]]; then
        echo "🚫 TENTATIVA DE ESCRITA FORA DO PROJETO!"
        log_access "WRITE_ATTEMPT_OUTSIDE" "$2"
        exit 1
    fi
    log_access "WRITE" "$2"
fi
```

### 6. Configuração do Hook

Adicionar ao settings.json:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit|Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "/home/bruno/.kothar/hooks/pre-project-isolation.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/home/bruno/.kothar/hooks/post-file-access.sh {toolCallResult}"
          }
        ]
      }
    ]
  }
}
```

### 7. Fluxo de Trabalho

```markdown
1. INÍCIO DA SESSÃO
   - Entrar na pasta raiz do projeto
   - Kothar detecta e valida projeto
   - Salva estado do projeto atual

2. DURANTE O TRABALHO
   - Só pode acessar/criar/modificar arquivos do projeto atual
   - Pode pedir para buscar referências de outros projetos
   - Qualquer tentativa de acesso fora é bloqueada

3. BUSCA DE REFERÊNCIA
   - "Kothar, busca a função X do projeto Y"
   - Kothar busca e retorna cópia
   - Pode clonar para o projeto atual com aprovação

4. CONEXÃO ENTRE PROJETOS
   - Apenas via APIs (ex: criar endpoint em chronodesk que acessa orby)
   - Cada projeto mantém seu próprio banco de dados
   - Código isolado, só compartilha dados via APIs
```

### 8. Script de Validação

```bash
#!/bin/bash
# validate-project-isolation.sh

echo "🔍 Validando isolamento de projetos..."

# Verificar arquivos fora do projeto
PROJECT_ROOT=$(cat ~/.kothar/state/current-project-root)
VIOLATIONS=$(find /home/bruno/Cofre -type f -name "*.py" -o -name "*.js" -o -name "*.md" | grep -v "$PROJECT_ROOT" | head -10)

if [[ -n "$VIOLATIONS" ]]; then
    echo "❌ VIOLAÇÕES DETECTADAS:"
    echo "$VIOLATIONS"
    exit 1
fi

echo "✅ Isolamento validado - nenhum arquivo fora do projeto atual"
```

## Implementação Imediata

1. Criar scripts de isolamento
2. Adicionar hooks ao settings.json
3. Criar sistema de busca de referências
4. Documentar regras para Bruno
5. Criar validação periódica