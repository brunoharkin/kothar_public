---
name: ouvinte-whatsapp
description: >-
  Conectar ao WhatsApp, ouvir mensagens e extrair demandas de texto, áudio, imagem e vídeo
---

# Habilidade: Ouvinte WhatsApp

## Funcionalidade
Conecta ao WhatsApp via Baileys (sem browser), ouve mensagens em tempo real e processa cada tipo de mídia com contexto da conversa anterior e posterior.

## Iniciar
```bash
bash /home/bruno/whatsapp-listener/iniciar.sh
```
Na primeira vez: escanear o QR Code exibido no terminal com o WhatsApp.

## Processamento por tipo

### Texto
- Registra remetente, hora e conteúdo
- Documenta em `00_Memoria/WhatsApp/YYYY-MM-DD/numero.md`

### Áudio
- Transcreve com OpenAI Whisper (modelo whisper-1)
- Documenta transcrição completa

### Imagem
- Aguarda 30s pela mensagem posterior (contexto)
- Envia para GPT-4o com: mensagens anteriores + imagem + mensagem posterior
- Extrai o que a imagem mostra e qual é a demanda do cliente

### Vídeo
- Usa thumbnail como frame representativo
- Analisa com GPT-4o com contexto anterior e posterior
- Extrai demanda relatada no vídeo

## Sessão persistente
- Credenciais salvas em `/home/bruno/whatsapp-listener/sessao/`
- `iniciar.sh` reinicia automaticamente se o processo cair
- Para rodar 24/7: executar `iniciar.sh` em um terminal separado

## Documentação gerada
```
00_Memoria/WhatsApp/
└── 2026-05-24/
    ├── 5511999999999.md   ← conversa por contato
    └── ...
```

## Configuração (.env)
- `OPENAI_API_KEY` — chave OpenAI para Whisper e GPT-4o
- `ESPERA_PROXIMA_MENSAGEM_MS` — tempo de espera pela msg posterior (padrão: 30000ms)
- `TAMANHO_BUFFER_CONTEXTO` — mensagens mantidas em memória por conversa (padrão: 10)

← [[catalogo-habilidades]]
