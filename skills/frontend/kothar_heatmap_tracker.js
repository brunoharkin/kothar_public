/**
 * KOTHAR v4.0 - Heatmap Tracker
 * Coleta coordenadas X, Y e envia em lotes de forma assíncrona.
 */

(function(window) {
    'use strict';
    
    // Configurações Padrão
    const config = {
        endpoint: 'http://localhost:8080/api/heatmaps/track',
        projectId: window.KOTHAR_PROJECT_ID || 'default_project',
        batchSize: 50,
        flushIntervalMs: 5000
    };

    let buffer = [];
    const sessionId = localStorage.getItem('kothar_trace_session') || 
                      'anon-' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('kothar_trace_session', sessionId);

    // Função de Flush (envio para o servidor)
    function flushBuffer() {
        if (buffer.length === 0) return;

        const payload = {
            project_id: config.projectId,
            session_id: sessionId,
            url: window.location.pathname,
            screen_width: window.innerWidth,
            screen_height: window.innerHeight,
            points: buffer.splice(0, buffer.length) // limpa buffer e pega itens
        };

        if (navigator.sendBeacon) {
            navigator.sendBeacon(config.endpoint, JSON.stringify(payload));
        } else {
            fetch(config.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true
            }).catch(err => console.error("Kothar Tracker falhou:", err));
        }
    }

    // Coleta de Cliques
    window.addEventListener('click', function(e) {
        buffer.push({
            x: e.pageX,
            y: e.pageY,
            value: 1,
            time: Date.now(),
            type: 'click'
        });

        if (buffer.length >= config.batchSize) {
            flushBuffer();
        }
    });

    // Coleta de Mouse Move (Throttle para não pesar)
    let lastMove = 0;
    window.addEventListener('mousemove', function(e) {
        const now = Date.now();
        if (now - lastMove > 200) { // grava a cada 200ms
            buffer.push({
                x: e.pageX,
                y: e.pageY,
                value: 0.1, // Peso menor que clique
                time: now,
                type: 'hover'
            });
            lastMove = now;
        }
    });

    // Envio periódico e no fechamento da página
    setInterval(flushBuffer, config.flushIntervalMs);
    window.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') flushBuffer();
    });

})(window);
