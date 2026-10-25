#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingestor em Lote para Canais do YouTube
Processa todos os vídeos de um canal e salva transcrições completas na base de conhecimento do Cofre.
"""

import sys
import os
import re
import time
import json
from pathlib import Path
from datetime import datetime
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

DIRETORIO_DESTINO = Path("/home/bruno-harkin/Cofre/base-de-conhecimento/videos")
ARQUIVO_ESTADO = DIRETORIO_DESTINO / ".canal-ingestao-status.json"

def limpar_nome_arquivo(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = re.sub(r'[\s_-]+', '-', texto)
    return texto.strip('-')[:80]

def carregar_estado() -> dict:
    if ARQUIVO_ESTADO.exists():
        try:
            with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"concluidos": [], "falhas": [], "total": 0}

def salvar_estado(estado: dict):
    DIRETORIO_DESTINO.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

def obter_transcricao(video_id: str) -> tuple[str, str]:
    api = YouTubeTranscriptApi()
    lista_transcricoes = api.list(video_id)
    
    transcricao = None
    try:
        transcricao = lista_transcricoes.find_transcript(['pt', 'pt-BR'])
    except Exception:
        try:
            transcricao = lista_transcricoes.find_transcript(['en', 'en-US'])
        except Exception:
            for t in lista_transcricoes:
                transcricao = t
                break

    if not transcricao:
        raise RuntimeError("Nenhuma legenda disponível.")

    dados = transcricao.fetch()
    idioma = transcricao.language_code

    linhas = []
    for entrada in dados:
        inicio = int(entrada.start)
        minutos = inicio // 60
        segundos = inicio % 60
        linhas.append(f"[{minutos:02d}:{segundos:02d}] {entrada.text}")

    return idioma, "\n".join(linhas)

def processar_canal(url_canal: str):
    DIRETORIO_DESTINO.mkdir(parents=True, exist_ok=True)
    estado = carregar_estado()
    concluidos = set(estado.get("concluidos", []))

    # Identificar se já existem arquivos no disco para vídeos já processados
    for f in DIRETORIO_DESTINO.glob("*.md"):
        partes = f.name.split("-")
        if len(partes) >= 4 and len(partes[3]) == 11:
            concluidos.add(partes[3])

    print(f"[*] Coletando lista de vídeos de: {url_canal}")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(url_canal, download=False)
        entries = res.get('entries', [])

    total = len(entries)
    estado["total"] = total
    print(f"[*] Encontrados {total} vídeos no canal.")
    print(f"[*] Já processados anteriormente: {len(concluidos)}")

    sucessos = 0
    falhas = 0

    for idx, entrada in enumerate(entries, start=1):
        vid_id = entrada.get('id')
        titulo = entrada.get('title', 'Sem Titulo')
        url_video = f"https://www.youtube.com/watch?v={vid_id}"

        if not vid_id:
            continue

        if vid_id in concluidos:
            print(f"[{idx}/{total}] [PULADO - JÁ EXISTE] {titulo} ({vid_id})")
            continue

        print(f"[{idx}/{total}] Processando: {titulo} ({vid_id})...")
        try:
            # Obter metadados completos
            with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl_single:
                info = ydl_single.extract_info(url_video, download=False)

            idioma, transcricao = obter_transcricao(vid_id)

            nome_slug = limpar_nome_arquivo(titulo)
            data_hoje = datetime.now().strftime("%Y-%m-%d")
            nome_arquivo = f"{data_hoje}-{vid_id}-{nome_slug}.md"
            caminho_final = DIRETORIO_DESTINO / nome_arquivo

            conteudo_md = f"""---
titulo: "{info.get('title', titulo)}"
canal: "{info.get('uploader', 'Ronnald Hawk | Engenharia de IA')}"
url: "{url_video}"
video_id: "{vid_id}"
duracao_segundos: {info.get('duration', 0)}
idioma: "{idioma}"
data_extracao: "{datetime.now().isoformat()}"
tipo: "transcricao-bruta-youtube"
tags:
  - base-de-conhecimento
  - youtube
  - transcricao
  - kothar-treinamento
  - ronnald-hawk
---

# {info.get('title', titulo)}

- **Canal / Autor:** {info.get('uploader', 'Ronnald Hawk | Engenharia de IA')}
- **URL Original:** {url_video}
- **Data de Coleta:** {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
- **Idioma Detectado:** {idioma}

---

## Descrição do Vídeo

```text
{info.get('description', '')}
```

---

## Transcrição Completa e Bruta

{transcricao}
"""
            with open(caminho_final, "w", encoding="utf-8") as f:
                f.write(conteudo_md)

            concluidos.add(vid_id)
            estado["concluidos"] = list(concluidos)
            salvar_estado(estado)
            sucessos += 1
            print(f"    -> [OK] Salvo em: {nome_arquivo}")
            time.sleep(1.0) # Rate limiting suave para evitar bloqueio por IP

        except Exception as e:
            print(f"    -> [ERRO] Falha ao processar {vid_id}: {e}")
            estado["falhas"].append({"id": vid_id, "titulo": titulo, "erro": str(e)})
            salvar_estado(estado)
            falhas += 1
            time.sleep(1.5)

    print("\n" + "="*50)
    print(f"Ingestão concluída. Sucessos: {sucessos} | Falhas: {falhas} | Total processados: {len(concluidos)}/{total}")
    print("="*50)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/@ronnaldhawk/videos"
    processar_canal(url)

