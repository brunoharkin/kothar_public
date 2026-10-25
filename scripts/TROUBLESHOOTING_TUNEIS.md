# 🌐 Como Resolver Problemas de Túnel

## ❌ Problemas Encontrados

1. **Cloudflare Tunnel** (`*.trycloudflare.com`): HTTP 403 para clientes
2. **Ngrok com Token**: `ERR_NGROK_15013` - precisa de domínio customizado registrado
3. **Ngrok sem Token**: Limite de 2h, domínio aleatório

## ✅ Solução Recomendada: LocalTunnel (sem autenticação)

O **LocalTunnel** é uma alternativa gratuita que:
- ✅ Não precisa de cadastro
- ✅ Não bloqueia requisições
- ✅ URL fixa (enquanto a sessão estiver ativa)

### Instalação:
```bash
npm install -g localtunnel
```

### Uso no Colab:
```python
import subprocess
subprocess.run(["npx", "localtunnel", "--port", "11434"])
```

---

## 🔧 Workaround Imediato: Proxy Local

Se nenhum túnel funcionar, use o **proxy do backend Kothar** que faz relay:

### Backend tem suporte nativo:
```
GET http://localhost:8080/api/ollama/proxy/tags?ollama_url=<TUNNEL_URL>
POST http://localhost:8080/api/ollama/proxy/chat
```

### Mas se o túnel não funciona, precisamos de outra abordagem...

---

## 🚀 Solução Definitiva: SSH Reverse Tunnel

Se você tem um servidor VPS acessível:
```bash
# No Colab:
ssh -R 11434:localhost:11434 user@your-server.com

# No servidor:
# A porta 11434 fica disponível para você
curl http://your-server.com:11434/api/tags
```

---

## 💡 Melhor Opção: Bore Tunnel (Grátis, Leve, Sem Auth)

```bash
# No Colab:
curl -fsSL https://raw.githubusercontent.com/anderspitman/awesome-tunneling/main/notes.txt > /dev/null 2>&1
wget https://github.com/ekzhang/bore/releases/latest/download/bore-x86_64-unknown-linux-musl.tar.gz
tar -xzf bore-x86_64-unknown-linux-musl.tar.gz
nohup ./bore local 11434 --to bore.pub > /tmp/bore.log 2>&1 &
```

Fornece URL como `bore.pub:XXXXX` que conecta direto.

---

## 📋 Recomendação Final

**Para resolver AGORA:**
1. Tente rodar sem token: `~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b ""`
2. Se der 403 do Cloudflare, abra a URL no navegador primeiro (resolve o interstitial)
3. Depois disso, a URL pode funcionar de outros lugares via API direta

**Para resolver DEFINITIVAMENTE:**
- Configure uma VPS própria (~$5/mês) e use SSH reverse tunnel
- Ou compre um domínio no Ngrok ($8/mês) e registre na conta
