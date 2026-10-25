---
name: markitdown-extractor
description: Extração de documentos limpos (PDF, DOCX, PPTX, XLSX, HTML) em Markdown para consumo LLM. Economiza tokens vs. extração via Claude native. Usa MarkItDown (Microsoft) v0.1.6.
metadata:
  tipo: ferramenta
  criticidade: alta
  data: 2026-06-12
  economia: token
  dependencia: markitdown-venv (/home/bruno/.claude/skills/kothar/markitdown-venv/)
---

# Skill: MarkItDown Extractor

> **Objetivo:** Extrair documentos de qualquer formato em texto Markdown limpo,
> otimizado para consumo por LLMs — economia massiva de tokens vs. Claude native.
>
> **Baseado em:** MarkItDown (Microsoft) v0.1.6
> **Venv:** `/home/bruno/.claude/skills/kothar/markitdown-venv/`
> **Gatilho:** Bruno pedir "ler", "extrair", "processar" documento

---

## Quando Usar

| Cenário | Ferramenta | Por quê |
|---|---|---|
| PDF com texto selecionável | ✅ MarkItDown CLI | Limpo, rápido, grátis |
| DOCX / PPTX / XLSX | ✅ MarkItDown CLI | Preserva estrutura |
| HTML / URL | ✅ MarkItDown CLI | Converte pra Markdown |
| CSV / JSON / XML | ✅ MarkItDown CLI | Texto estruturado |
| EPUB | ✅ MarkItDown CLI | Converte estrutura |
| ZIP (múltiplos arquivos) | ✅ MarkItDown CLI | Itera conteúdo |
| Screenshot / imagem scanned | ❌ Claude native (Read) | Visão nativa |
| PDF scanned (sem texto) | ⏳ MarkItDown + OCR plugin | Precisa OpenAI key |
| YouTube URL | ⏳ MarkItDown --youtube | Transcrição automática |

---

## Comando Principal

```bash
VENV="/home/bruno/.claude/skills/kothar/markitdown-venv"
$VENV/bin/markitdown "<arquivo>" -o "<saida.md>"
```

**Aliases de conveniência (adicionar ao ~/.bashrc se quiser):**
```bash
# Extrair e mostrar no terminal
extract-md() {
  VENV="/home/bruno/.claude/skills/kothar/markitdown-venv"
  $VENV/bin/markitdown "$1" -o /tmp/extracted.md && cat /tmp/extracted.md
}
```

---

## Fluxo de Uso (padrão Kothar)

### Passo 1 — Identificar arquivo
Perguntar a Bruno o caminho do arquivo, ou usar o caminho fornecido.

### Passo 2 — Extrair
```bash
VENV="/home/bruno/.claude/skills/kothar/markitdown-venv"
OUTPUT=$(mktemp /tmp/markitdown-XXXXXX.md)
$VENV/bin/markitdown "$CAMINHO_ARQUIVO" -o "$OUTPUT"
echo "Linhas: $(wc -l < $OUTPUT)"
head -30 "$OUTPUT"
```

### Passo 3 — Mostrar preview
Exibir primeiras 30-50 linhas e perguntar se quer o documento completo.

### Passo 4 — Resumo + Ação
Aplicar o que Bruno pediu (análise, comparação, resumo, extração de dados, etc.)

---

## Flags Úteis

| Flag | Uso |
|---|---|
| `-o <arquivo>` | Saída para arquivo específico |
| `--list-plugins` | Listar plugins instalados |
| `--help` | Ajuda completa |

---

## API Python (para integração avançada)

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("documento.pdf")

# Texto puro (otimizado LLM)
print(result.text_content)

# Markdown completo (com estrutura de headings/tabelas)
print(result.markdown)
```

---

## Comparação: MarkItDown vs Alternativas

| Critério | MarkItDown | Claude native | textract |
|---|---|---|---|
| Custo | Gratuito | Tokens API | Freemium |
| Estrutura headings/tabelas | ✅ Preserva | ✅ | ❌ |
| Texto limpo LLM | ✅ Otimizado | ✅ | ❌ |
| Velocidade | ⚡ Local (seg) | 🐢 API | 🐢 Local |
| Formatos | 15+ nativos | Imagens | 100+ |
| PDF scanned | ⏳ c/ OCR plugin | ✅ Visão | ✅ |

---

## Manutenção

```bash
# Atualizar MarkItDown
~/.claude/skills/kothar/markitdown-venv/bin/pip install --upgrade markitdown

# Atualizar todas as dependências
~/.claude/skills/kothar/markitdown-venv/bin/pip install --upgrade 'markitdown[all]'

# Verificar plugins
~/.claude/skills/kothar/markitdown-venv/bin/markitdown --list-plugins

# Testar instalação
~/.claude/skills/kothar/markitdown-venv/bin/markitdown --version
```

---

## Erros Conhecidos

| Erro | Solução |
|---|---|
| `markitdown: command not found` | Usar path completo: `$VENV/bin/markitdown` |
| `python3-venv` não existe | `sudo apt install python3.12-venv python3-full` |
| PDF scanned não extrai texto | Usar Claude native (Read) ou plugin `markitdown-ocr` + OpenAI key |
| Permission denied em venv | `chmod +x ~/.claude/skills/kothar/markitdown-venv/bin/*` |
