#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Extração e Transcrição Automática do YouTube
Salva transcrições completas e brutas no Cofre em /home/bruno-harkin/Cofre/base-de-conhecimento/videos/
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Importações do ecossistema de extração
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

DIRETORIO_DESTINO = Path("/home/bruno-harkin/Cofre/base-de-conhecimento/videos")

def limpar_nome_arquivo(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = re.sub(r'[\s_-]+', '-', texto)
    return texto.strip('-')[:80]

def extrair_id_video(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path.lstrip('/')
    if parsed.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            qs = parse_qs(parsed.query)
            return qs.get('v', [None])[0]
        if parsed.path.startswith(('/embed/', '/v/', '/shorts/')):
            return parsed.path.split('/')[2]
    return url

def obter_metadados(url: str) -> dict:
    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'titulo': info.get('title', 'Sem Título'),
            'canal': info.get('uploader', 'Canal Desconhecido'),
            'duracao_segundos': info.get('duration', 0),
            'url': url,
            'id': info.get('id', extrair_id_video(url)),
            'descricao': info.get('description', ''),
            'data_publicacao': info.get('upload_date', '')
        }

def obter_transcricao(video_id: str) -> tuple[str, str]:
    """
    Tenta obter transcrições (manuais ou automáticas) via youtube-transcript-api.
    Retorna (idioma_encontrado, texto_bruto_formatado).
    """
    try:
        api = YouTubeTranscriptApi()
        lista_transcricoes = api.list(video_id)
        
        # Prioridade: pt, pt-BR, en, ou qualquer disponível
        transcricao = None
        try:
            transcricao = lista_transcricoes.find_transcript(['pt', 'pt-BR'])
        except Exception:
            try:
                transcricao = lista_transcricoes.find_transcript(['en', 'en-US'])
            except Exception:
                # Pega a primeira que estiver disponível
                for t in lista_transcricoes:
                    transcricao = t
                    break

        if not transcricao:
            raise RuntimeError("Nenhuma legenda ou transcrição encontrada no YouTube para este vídeo.")

        dados = transcricao.fetch()
        idioma = transcricao.language_code

        linhas_formatadas = []
        for entrada in dados:
            inicio = int(entrada.start)
            minutos = inicio // 60
            segundos = inicio % 60
            tempo = f"[{minutos:02d}:{segundos:02d}]"
            linhas_formatadas.append(f"{tempo} {entrada.text}")

        texto_completo = "\n".join(linhas_formatadas)
        return idioma, texto_completo

    except Exception as e:
        raise RuntimeError(f"Falha ao obter transcrição do YouTube: {e}")

def processar_video(url: str) -> str:
    video_id = extrair_id_video(url)
    if not video_id:
        raise ValueError(f"Não foi possível extrair o ID do vídeo da URL: {url}")

    print(f"[*] Extraindo metadados do vídeo: {url}")
    metadados = obter_metadados(url)
    
    print(f"[*] Obtendo transcrição completa para o vídeo ID: {video_id}")
    idioma, transcricao_bruta = obter_transcricao(video_id)

    DIRETORIO_DESTINO.mkdir(parents=True, exist_ok=True)
    nome_slug = limpar_nome_arquivo(metadados['titulo'])
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"{data_hoje}-{video_id}-{nome_slug}.md"
    caminho_final = DIRETORIO_DESTINO / nome_arquivo

    conteudo_md = f"""---
titulo: "{metadados['titulo']}"
canal: "{metadados['canal']}"
url: "{metadados['url']}"
video_id: "{video_id}"
duracao_segundos: {metadados['duracao_segundos']}
idioma: "{idioma}"
data_extracao: "{datetime.now().isoformat()}"
tipo: "transcricao-bruta-youtube"
tags:
  - base-de-conhecimento
  - youtube
  - transcricao
  - kothar-treinamento
---

# {metadados['titulo']}

- **Canal / Autor:** {metadados['canal']}
- **URL Original:** {metadados['url']}
- **Data de Coleta:** {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
- **Idioma Detectado:** {idioma}

---

## Descrição do Vídeo

```text
{metadados['descricao']}
```

---

## Transcrição Completa e Bruta

{transcricao_bruta}
"""

    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(conteudo_md)

    print(f"[OK] Transcrição salva com sucesso em: {caminho_final}")
    return str(caminho_final)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python transcritor.py <URL_DO_YOUTUBE>")
        sys.exit(1)

    url_input = sys.argv[1].strip()
    try:
        arquivo_gerado = processar_video(url_input)
        print(f"ARQUIVO_GERADO:{arquivo_gerado}")
    except Exception as erro:
        print(f"[ERRO] {erro}", file=sys.stderr)
        sys.exit(1)

