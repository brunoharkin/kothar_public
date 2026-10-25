#!/usr/bin/env python3
"""
Transcritor Kothar - Transcrição pura de áudio/vídeo
Extrai texto exato sem estruturação
"""

import os
import sys
import json
import glob
from pathlib import Path

# Carregar .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

import whisper

# Configuração padrão
OUTPUT_DIR = Path("/home/bruno/transcricoes")


def transcribe_file(audio_path: str, output_dir: Path = None, language: str = "pt") -> str:
    """Transcreve um arquivo de áudio/vídeo e salva apenas o .txt puro"""

    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Carregar modelo
    print(f"🔄 Carregando modelo Whisper...")
    model = whisper.load_model("base", device="cpu")

    # Nome do arquivo de saída
    input_name = Path(audio_path).stem
    output_path = output_dir / f"{input_name}_transcricao.txt"

    print(f"🎤 Transcrevendo: {Path(audio_path).name}")
    result = model.transcribe(str(audio_path), language=language, verbose=False)

    # Salvar apenas transcrição pura
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())

    # Salvar segmentos (opcional, para referência de tempo)
    segments_path = output_dir / f"{input_name}_segmentos.json"
    with open(segments_path, "w", encoding="utf-8") as f:
        json.dump(result["segments"], f, ensure_ascii=False, indent=2)

    print(f"✅ Salvo: {output_path.name}")
    return str(output_path)


def transcribe_folder(folder_path: str, output_dir: Path = None, language: str = "pt",
                       extensions: tuple = (".mp4", ".mp3", ".wav", ".m4a", ".avi", ".mkv", ".flac")):
    """Transcreve todos os arquivos de uma pasta"""

    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Encontrar arquivos
    folder = Path(folder_path)
    files = []
    for ext in extensions:
        files.extend(glob.glob(str(folder / f"*{ext}")))

    if not files:
        print(f"⚠️ Nenhum arquivo de mídia encontrado em: {folder_path}")
        return []

    print(f"📁 Encontrados {len(files)} arquivos")

    # Carregar modelo uma vez
    print(f"🔄 Carregando modelo Whisper...")
    model = whisper.load_model("base", device="cpu")

    results = []
    for i, file_path in enumerate(sorted(files), 1):
        input_name = Path(file_path).stem
        output_path = output_dir / f"{input_name}_transcricao.txt"
        segments_path = output_dir / f"{input_name}_segmentos.json"

        print(f"\n[{i}/{len(files)}] Transcrevendo: {Path(file_path).name}")
        result = model.transcribe(file_path, language=language, verbose=False)

        # Salvar apenas transcrição pura
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())

        with open(segments_path, "w", encoding="utf-8") as f:
            json.dump(result["segments"], f, ensure_ascii=False, indent=2)

        print(f"   ✅ Salvo: {output_path.name}")
        results.append(str(output_path))

    return results


def limpar_segmentos(output_dir: Path = None):
    """Remove arquivos .segmentos.json, mantém apenas .txt"""
    if output_dir is None:
        output_dir = OUTPUT_DIR

    segmentos = list(output_dir.glob("*_segmentos.json"))
    for seg in segmentos:
        seg.unlink()
        print(f"🗑️ Removido: {seg.name}")

    print(f"\n✅ Limpeza concluída! Mantidos {len(list(output_dir.glob('*_transcricao.txt')))} arquivos .txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python transcritor.py <arquivo.mp4>           # Transcreve um arquivo")
        print("  python transcritor.py <pasta> --folder       # Transcreve todos de uma pasta")
        print("  python transcritor.py --limpar               # Remove arquivos _segmentos.json")
        sys.exit(1)

    arg1 = sys.argv[1]

    if arg1 == "--limpar":
        limpar_segmentos()
    elif arg1 == "--folder" and len(sys.argv) > 2:
        transcribe_folder(sys.argv[2])
    else:
        transcribe_file(arg1)
