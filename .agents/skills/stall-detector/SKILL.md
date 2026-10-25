---
name: stall-detector
description: >-
  Skill do Kothar: Stall Detector. Ativar quando necessário para execução da habilidade stall-detector.
---

# Stall Detector

> **Skill:** Kothar Stall Detector  
> **Versão:** 1.1 (CORRIGIDO)  
> **Data:** 2026-06-28  
> **Status:** ✅ Sem JavaScript executável  
> **Dependência:** Hooks do sistema

---
## 🎯 Objetivo

Sistema de detecção de sessões "travadas" — processamento longo sem progresso.

**Problema resolvido:** Kothar não sabe quando está travado, não notifica Bruno.

---
## 🚧 IMPLEMENTAÇÃO REAL (via Hooks)

**Atenção:** Esta NÃO é uma skill executável. É uma especificação para os hooks.

### Funcionamento Real:

O monitoramento é feito pelos hooks existentes:
- `post-tool-stall-detector.sh` monitora tempo entre tool calls
- Calcula idle time baseado em timestamps
- Notifica quando thresholds são atingidos

### Estados Detectáveis (passivo):

```
┌─────────────────────────────────────────────────────────────┐
│ ESTADOS DETECTADOS PELOS HOOKS                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  HEALTHY      ←  Tool calls < 30s apart                     │
│  LONG-RUNNING ←  Tool call > 2min                          │  
│  STALLED      ←  No response > 5min                        │
│  STUCK        ←  No response > 10min                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Importante:** Não há código JavaScript executável aqui. O sistema funciona puramente através dos hooks que monitoram timestamps das tools.

---
## 📡 Métricas Monitoradas

| Métrica | Limiar | Ação |
|---------|--------|------|
| Idle Time | > 5min | Notificar STALLED |
| Tool Duration | > 2min | Logar LONG-RUNNING |
| No Response | > 10min | Oferecer abort |

---
## 🔧 Como os Hooks Funcionam

```bash
# Exemplo do hook real
post-tool-stall-detector.sh:
  1. Pega timestamp da última tool
  2. Calcula diferença para agora
  3. Compara com thresholds
  4. Escreve log se necessário
```

---
## 📊 Logs Gerados

Os logs aparecem em `~/.kothar/logs/stall-detector.jsonl`:

```json
{"timestamp": "2026-06-28T13:30:00Z", "status": "stalled", "idle_time": 320000}
{"timestamp": "2026-06-28T13:32:00Z", "status": "stuck", "idle_time": 610000}
```

---
## ✅ Verificação

Para testar:
```bash
# Simular sessão travada
sleep 300  # 5 minutos
# O hook deve detectar e notificar
```

---
**Status:** ✅ IMPLEMENTADO VIA HOOKS (sem JavaScript)
