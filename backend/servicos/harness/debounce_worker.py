#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Worker de Debounce e Fila de Mensagens para Agentes de WhatsApp
Agrupa mensagens em rajada (bursts) em uma única janela de contexto antes de despachar para o orquestrador.
"""

import time
import threading
from typing import Dict, List, Callable, Optional
from datetime import datetime

class MensagemEntrada:
    def __init__(self, remetente: str, texto: str, timestamp: float = None):
        self.remetente = remetente
        self.texto = texto
        self.timestamp = timestamp or time.time()

class DebounceWorker:
    def __init__(self, janela_debounce_segundos: float = 3.0, processador_callback: Optional[Callable[[str, str], None]] = None):
        self.janela_debounce = janela_debounce_segundos
        self.processador = processador_callback
        self.buffers: Dict[str, List[MensagemEntrada]] = {}
        self.timers: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()

    def receber_mensagem(self, remetente: str, texto: str):
        """
        Recebe mensagem instantaneamente. Retorna confirmação (ACK) imediata e agenda o processamento.
        """
        with self.lock:
            if remetente not in self.buffers:
                self.buffers[remetente] = []

            self.buffers[remetente].append(MensagemEntrada(remetente, texto))

            # Cancela timer anterior se houver nova mensagem na janela
            if remetente in self.timers:
                self.timers[remetente].cancel()

            # Agenda novo disparo para quando o remetente parar de digitar
            timer = threading.Timer(self.janela_debounce, self._disparar_processamento, args=[remetente])
            self.timers[remetente] = timer
            timer.start()

    def _disparar_processamento(self, remetente: str):
        with self.lock:
            mensagens = self.buffers.pop(remetente, [])
            self.timers.pop(remetente, None)

        if not mensagens:
            return

        # Consolida as mensagens em ordem cronológica
        texto_consolidado = "\n".join(m.texto.strip() for m in mensagens if m.texto.strip())

        if self.processador:
            self.processador(remetente, texto_consolidado)

