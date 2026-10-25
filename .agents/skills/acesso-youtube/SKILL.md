---
name: acesso-youtube
description: >-
  Extrair título, descrição e transcrição de vídeos do YouTube
---

# Habilidade: Acesso ao YouTube

## Funcionalidade
Extrai conteúdo completo de vídeos do YouTube — título, descrição e transcrição — usando legendas disponíveis ou conversão de áudio via yt-dlp.

## Ferramenta

### `extract-youtube`
Extrai conteúdo de um vídeo a partir da URL.

**Parâmetros**:
```
extract-youtube(
  url="https://www.youtube.com/watch?v=VIDEO_ID",
  incluirTitulo=true,
  incluirDescricao=true,
  incluirTranscricao=true
)
```

**Retorna**:
```
{
  titulo: "Nome do vídeo",
  descricao: "Descrição completa...",
  transcricao: "Texto falado no vídeo..."
}
```

## Quando Usar

- Resumir um vídeo sem assistir
- Buscar informações específicas dentro de um vídeo
- Registrar aprendizados de vídeos no Obsidian
- Comparar conteúdo de múltiplos vídeos

## Workflow com Memória

```
Usuário envia URL do YouTube
    ↓
extract-youtube(url)
    ↓
Processar conteúdo relevante
    ↓
Registrar resumo em 00_Memoria/Diarias/
    ↓
Retornar resposta ao usuário
```

## Limitações
- Vídeos sem legenda automática dependem do yt-dlp para transcrição por áudio
- Vídeos privatizados ou com restrição de idade não são acessíveis
- Respeitar os termos de uso do YouTube

← [[catalogo-habilidades]]
