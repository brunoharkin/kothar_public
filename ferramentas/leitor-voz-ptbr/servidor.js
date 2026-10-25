#!/usr/bin/env node

/**
 * Kothar Voice Server - Painel de Debate Auditivo de Planos (War Room)
 * Porta: 3344
 * 
 * Funcionalidades:
 * 1. Síntese Neural Contínua (Kokoro pt-BR)
 * 2. Gestão de Plano Ativo (Leitura, Debate e Aprovação)
 * 3. Motor de Debate Auditivo Kothar (Análise de Risco, Contrapropostas e Ajuste de Plano)
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { processarDebateKothar, processarDuvidaTextoLivre } = require('./debate-engine.js');

const PORT = 3344;
const KOKORO_PORT = 5050;
const HTML_FILE = path.join(__dirname, 'pagina-leitor.html');
const PLANO_FILE = path.join(__dirname, 'plano-ativo.json');

const audioCache = new Map();

function fetchFromKokoro(texto, voz = 'pm_alex', velocidade = 1.05) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ texto, voz, velocidade });
    const req = http.request({
      hostname: '127.0.0.1',
      port: KOKORO_PORT,
      path: '/sintetizar',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`Kokoro error HTTP ${res.statusCode}`));
        return;
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

function fetchAudioFromGoogle(text) {
  return new Promise((resolve, reject) => {
    const encoded = encodeURIComponent(text);
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=pt-BR&total=1&idx=0&textlen=${text.length}&client=tw-ob&prev=input&ttsspeed=1`;

    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'audio/mpeg, */*'
      }
    }, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`Google TTS status code: ${res.statusCode}`));
        return;
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://localhost:${PORT}`);

  // 1. Interface Web
  if (parsedUrl.pathname === '/' || parsedUrl.pathname === '/index.html') {
    fs.readFile(HTML_FILE, 'utf8', (err, content) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Erro ao carregar a interface do Kothar Voice.');
        return;
      }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache' });
      res.end(content);
    });
  } 
  // 2. Obter Plano Ativo
  else if (parsedUrl.pathname === '/api/plano' && req.method === 'GET') {
    if (fs.existsSync(PLANO_FILE)) {
      const planoData = fs.readFileSync(PLANO_FILE, 'utf8');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(planoData);
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ erro: 'Nenhum plano ativo no momento.' }));
    }
  }
  // 3. Debater Plano (Receber fala/texto do usuário)
  else if (parsedUrl.pathname === '/api/debate' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        const falaUsuario = (payload.mensagem || '').trim();

        if (!falaUsuario) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ erro: 'Mensagem vazia.' }));
          return;
        }

        let plano = {};
        if (fs.existsSync(PLANO_FILE)) {
          plano = JSON.parse(fs.readFileSync(PLANO_FILE, 'utf8'));
        }

        const { respostaVoz, respostaMarkdown } = processarDebateKothar(plano, falaUsuario);
        fs.writeFileSync(PLANO_FILE, JSON.stringify(plano, null, 2), 'utf8');

        // Pré-sintetizar o áudio da resposta do Kothar para tocar de imediato
        let audioBuffer;
        try {
          audioBuffer = await fetchFromKokoro(respostaVoz, 'pm_alex', 1.05);
        } catch (e) {
          audioBuffer = await fetchAudioFromGoogle(respostaVoz);
        }

        const audioId = `debate_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        audioCache.set(audioId, {
          buffer: audioBuffer,
          contentType: 'audio/wav',
          criadoEm: Date.now()
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          sucesso: true,
          respostaTexto: respostaMarkdown,
          respostaVoz: respostaVoz,
          audioUrl: `/api/audio/${audioId}`,
          planoAtualizado: plano
        }));

      } catch (err) {
        console.error('Erro no debate:', err);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ erro: err.message }));
      }
    });
  }
  // 4. Tirar Dúvidas sobre Texto Livre (Debate/Explicação de Texto Colado)
  else if (parsedUrl.pathname === '/api/duvida-texto' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        const textoContexto = (payload.textoContexto || '').trim();
        const pergunta = (payload.pergunta || '').trim();

        if (!pergunta) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ erro: 'Pergunta não informada.' }));
          return;
        }

        const { respostaVoz, respostaMarkdown } = processarDuvidaTextoLivre(textoContexto, pergunta);

        let audioBuffer;
        try {
          audioBuffer = await fetchFromKokoro(respostaVoz, 'pm_alex', 1.05);
        } catch (e) {
          audioBuffer = await fetchAudioFromGoogle(respostaVoz);
        }

        const audioId = `duvida_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        audioCache.set(audioId, {
          buffer: audioBuffer,
          contentType: 'audio/wav',
          criadoEm: Date.now()
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          sucesso: true,
          respostaTexto: respostaMarkdown,
          respostaVoz: respostaVoz,
          audioUrl: `/api/audio/${audioId}`
        }));

      } catch (err) {
        console.error('Erro ao tirar dúvida de texto:', err);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ erro: err.message }));
      }
    });
  }
  // 5. Aprovar Plano
  else if (parsedUrl.pathname === '/api/aprovar' && req.method === 'POST') {
    if (fs.existsSync(PLANO_FILE)) {
      const plano = JSON.parse(fs.readFileSync(PLANO_FILE, 'utf8'));
      plano.status = 'APROVADO_PELO_BRUNO';
      plano.aprovadoEm = new Date().toISOString();
      fs.writeFileSync(PLANO_FILE, JSON.stringify(plano, null, 2), 'utf8');

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ sucesso: true, mensagem: 'Plano aprovado com sucesso! Kothar pronto para implementar.' }));
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ erro: 'Nenhum plano ativo para aprovar.' }));
    }
  }
  // 5. Síntese Genérica de Texto
  else if (parsedUrl.pathname === '/api/sintetizar' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        const texto = (payload.texto || '').trim();
        const motor = payload.motor || 'kokoro-alex';
        const velocidade = parseFloat(payload.velocidade || 1.05);

        if (!texto) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ erro: 'Texto vazio.' }));
          return;
        }

        let voiceId = 'pm_alex';
        if (motor === 'kokoro-dora') voiceId = 'pf_dora';
        else if (motor === 'kokoro-santa') voiceId = 'pm_santa';

        let audioBuffer;
        let contentType = 'audio/wav';

        if (motor === 'fallback-google') {
          audioBuffer = await fetchAudioFromGoogle(texto);
          contentType = 'audio/mpeg';
        } else {
          try {
            audioBuffer = await fetchFromKokoro(texto, voiceId, velocidade);
            contentType = 'audio/wav';
          } catch (eKokoro) {
            audioBuffer = await fetchAudioFromGoogle(texto);
            contentType = 'audio/mpeg';
          }
        }

        const audioId = `audio_full_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        audioCache.set(audioId, {
          buffer: audioBuffer,
          contentType: contentType,
          criadoEm: Date.now()
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          sucesso: true,
          audioUrl: `/api/audio/${audioId}`
        }));

      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ erro: err.message }));
      }
    });
  } 
  // 6. Endpoint de Áudio
  else if (parsedUrl.pathname.startsWith('/api/audio/')) {
    const id = parsedUrl.pathname.replace('/api/audio/', '');
    const item = audioCache.get(id);

    if (!item || !item.buffer) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Áudio não encontrado ou expirado.');
      return;
    }

    res.writeHead(200, {
      'Content-Type': item.contentType,
      'Content-Length': item.buffer.length,
      'Cache-Control': 'public, max-age=3600'
    });
    res.end(item.buffer);
  } 
  // 7. Status
  else if (parsedUrl.pathname === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'online', porta: PORT, modo: 'Kothar War Room Auditivo' }));
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Não encontrado.');
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[Kothar War Room] Servidor rodando em http://localhost:${PORT}`);
});
