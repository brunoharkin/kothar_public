---
name: skill-gestao-portas
description: >-
  Skill obrigatória para gestão de portas - SEMPRE verificar antes de subir servidor
---

# Skill: Gestão de Portas (OBRIGATÓRIA)

## 🚫 Regra de Ouro

**ANTES de iniciar QUALQUER servidor ou serviço, SEMPRE verificar porta:**

```bash
~/.kothar/ports/check-port.sh <PORTA>
```

**Portas em uso NO REGISTRO ATUAL:**

| Porta | Projeto | Serviço |
|-------|---------|---------|
| 2785 | crm-saphia | Evolution API |
| 2786 | disparo-em-massa | Evolution API |
| 5432 | disparo-em-massa | PostgreSQL |
| 5433 | crm-saphia | PostgreSQL |
| 6380 | crm-saphia | Redis |

---

## Fluxo Obrigatório

```
1. PLANEJAR → Definir porta desejada para o serviço
         ↓
2. VERIFICAR → ~/.kothar/ports/check-port.sh <PORTA>
         ↓
3. SE OCUPADA → ~/.kothar/ports/free-port.sh <RANGE_INICIO> <RANGE_FIM>
         ↓
4. REGISTRAR → check-port.sh <PORTA> <projeto> <servico>
         ↓
5. INICIAR → Só então subir o servidor
```

---

## Scripts Disponíveis

### check-port.sh
Verifica se porta está disponível:
```bash
~/.kothar/ports/check-port.sh 4000
# Retorna: ✅ Porta 4000 disponível
# ou: ❌ Porta 4000 já está em uso pelo projeto: crm-saphia
```

Registrar porta em uso:
```bash
~/.kothar/ports/check-port.sh 4000 chronodesk backend
# Retorna: ✅ Porta 4000 registrada para chronodesk/backend
```

### free-port.sh
Encontra próxima porta livre em um range:
```bash
~/.kothar/ports/free-port.sh 3000 3999
# Retorna: 3456 (primeira porta livre)
```

---

## Convenção de Ranges por Projeto

| Projeto | Range |
|---------|-------|
| disparo-em-massa | 2700-2899 |
| crm-saphia | 2700-2899 |
| chronodesk | 4000-4099 |
| kothar-dashboard | 5000-5099 |
| Frontend geral | 3000-3999 |
| Backend geral | 4000-4999 |
| Dev/Teste | 5000-5999 |

---

## Nomes de Serviços Padrão

- `evolution-api` — Gateway WhatsApp
- `backend` — API Node/Express
- `frontend` — Servidor web (Next.js, Vite, etc.)
- `postgresql` — Banco de dados PostgreSQL
- `mysql` — Banco de dados MySQL/MariaDB
- `redis` — Cache Redis
- `mongodb` — Banco MongoDB
- `websocket` — Servidor WebSocket
- `grpc` — Servidor gRPC

---

## Exemplo Completo

```bash
# Quero subir servidor do ChronoDesk na porta 4000

# 1. Verificar se está livre
~/.kothar/ports/check-port.sh 4000
# Resultado: ❌ Porta 4000 já está em uso pelo projeto: crm-saphia

# 2. Encontrar porta livre no range do ChronoDesk
~/.kothar/ports/free-port.sh 4000 4099
# Resultado: 4005

# 3. Registrar a porta que será usada
~/.kothar/ports/check-port.sh 4005 chronodesk backend

# 4. Iniciar o servidor na porta 4005
PORT=4005 npm start
```

---

## Erros Comuns (NUNCA FAZER)

❌ **NUNCA** iniciar servidor sem verificar porta
❌ **NUNCA** hardcodar porta sem consultar registry
❌ **NUNCA** usar porta já registrada por outro projeto

---

*Skill obrigatória — Kothar v2.2.0*
