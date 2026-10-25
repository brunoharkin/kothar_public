---
name: acesso-youtube
description: >-
  Extrair título, descrição e transcrição de vídeos do YouTube
---

# Habilidade: Acesso ao YouTube

## Funcionalidade
Extrai conteúdo completo de vídeos do YouTube — título, descrição e transcrição — usando legendas disponíveis ou conversão de áudio via yt-dlp.

## Ferramenta Executável

O extrator e transcritor oficial está implementado em:
`backend/servicos/youtube/transcritor.py`

**Execução via Python (.venv):**
```bash
/home/bruno-harkin/kothar/.venv/bin/python /home/bruno-harkin/kothar/backend/servicos/youtube/transcritor.py "<URL_DO_YOUTUBE>"
```

**Destino Canônico:**
`/home/bruno-harkin/Cofre/base-de-conhecimento/videos/YYYY-MM-DD-<VIDEO_ID>-<SLUG>.md`

## Formato do Arquivo Gerado no Cofre
O arquivo gerado é um Markdown completo contendo:
- Frontmatter com metadados estruturados (título, canal, duração, tags, url, id).
- Descrição original do vídeo.
- Transcrição completa bruta com timestamps `[MM:SS]`.

## Workflow Automático
1. Usuário envia URL do YouTube.
2. Kothar aciona o script `/home/bruno-harkin/kothar/backend/servicos/youtube/transcritor.py`.
3. Metadados e transcrição com timestamps são gerados em segundos.
4. O arquivo é persistido em `/home/bruno-harkin/Cofre/base-de-conhecimento/videos/`.
5. Kothar confirma o salvamento e apresenta o resumo/link do arquivo criado.

← [[catalogo-habilidades]]

