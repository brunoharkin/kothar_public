#!/usr/bin/env python3
"""
Serviço Micro-API de Síntese Neural Kokoro pt-BR com Remoção de Silêncio e Fade Rápido
Porta: 5050
"""

import sys
import os
import io
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import soundfile as sf
import numpy as np
from kokoro import KPipeline

print("[Kokoro Engine] Carregando pipeline de fala pt-BR...")
pipeline = KPipeline(lang_code='p')
print("[Kokoro Engine] Pipeline neural pronta!")

PORT = 5050

def strip_silence(audio, threshold=0.015, margin=1200):
    """
    Remove o silêncio morto do início e do final do bloco de áudio gerado pela rede neural,
    mantendo uma margem sutil para transição imperceptível (crossfade/gapless).
    """
    if len(audio) == 0:
        return audio
    
    non_zero = np.where(np.abs(audio) > threshold)[0]
    if len(non_zero) == 0:
        return audio

    start_idx = max(0, non_zero[0] - margin)
    end_idx = min(len(audio), non_zero[-1] + margin)
    
    trimmed = audio[start_idx:end_idx]
    
    # Aplicar fade-in e fade-out rápido (10ms = 240 samples) para evitar estalos (clipping)
    fade_len = min(240, len(trimmed) // 4)
    if fade_len > 0:
        fade_in = np.linspace(0.0, 1.0, fade_len)
        fade_out = np.linspace(1.0, 0.0, fade_len)
        trimmed[:fade_len] *= fade_in
        trimmed[-fade_len:] *= fade_out

    return trimmed

class VoiceHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == '/sintetizar':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                texto = data.get('texto', '').strip()
                voz = data.get('voz', 'pm_alex')
                velocidade = float(data.get('velocidade', 1.05))

                if not texto:
                    self.send_response(400)
                    self._set_cors()
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'erro': 'Texto vazio'}).encode('utf-8'))
                    return

                generator = pipeline(texto, voice=voz, speed=velocidade)
                audios = []
                for _, _, audio in generator:
                    trimmed_chunk = strip_silence(audio)
                    if len(trimmed_chunk) > 0:
                        audios.append(trimmed_chunk)

                if not audios:
                    raise Exception('Nenhum segmento gerado')

                full_audio = np.concatenate(audios)
                
                # Gravação em WAV puro 24kHz
                byte_io = io.BytesIO()
                sf.write(byte_io, full_audio, 24000, format='WAV')
                wav_bytes = byte_io.getvalue()

                self.send_response(200)
                self._set_cors()
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(wav_bytes)))
                self.end_headers()
                self.wfile.write(wav_bytes)

            except Exception as e:
                print(f"[Erro Kokoro]: {e}")
                self.send_response(500)
                self._set_cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'erro': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'online', 'motor': 'Kokoro-82M pt-BR (Gapless)'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    server = HTTPServer(('127.0.0.1', PORT), VoiceHandler)
    print(f"[Kokoro Engine] Servidor de voz rodando em http://127.0.0.1:{PORT}")
    server.serve_forever()

if __name__ == '__main__':
    run()
