# 🌐 Como Obter a URL do Túnel

## 🎉 ATUALIZAÇÃO: Agora usa Cloudflare Tunnel (GRÁTIS, sem token!)

O script `colab_gpu_spinup.sh` v2.0+ usa **Cloudflare Tunnel** automaticamente, que é 100% gratuito e **não precisa de cadastro ou token**!

---

## 🚀 Passo a Passo Simplificado

### 1. Rodar o Script
```bash
~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b
# (Sem precisar de token!)
```

### 2. Pegar a URL do Output
A URL aparece automaticamente no log:
```
[TUNNEL] 🚀 ENDPOINT DA API PRONTO: https://controversy-sao-heart-tent.trycloudflare.com
[TUNNEL] Copie e cole a URL acima no campo BASE_URL do Kothar Local AI!
```

**Copie essa URL!**

### 3. Configurar no Kothar
1. Abra http://localhost:5180
2. Vá em **"Local AI"**
3. Clique em ⚙️ (engrenagem)
4. Cole a URL (ex: `https://controversy-sao-heart-tent.trycloudflare.com`)
5. Clique em **"Atualizar Conexão"**
6. Status muda para **Online** ✅

---

## ⚠️ Nota sobre "TooManyAssignmentsError"

Se você ver esse erro:
```
TooManyAssignmentsError: ... Precondition Failed
```

**Significa que o Google Colab recusou a alocação.** Possíveis causas:
- Muitas sessões abertas na sua conta
- Limite diário de GPU atingido
- Conta precisa fazer logout/login

**Solução:**
```bash
# Limpar sessões antigas
colab stop --all

# Aguardar 5-10 minutos
# Tentar novamente
~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b
```

Se persistir, tente:
```bash
# Logout e login novamente
colab logout
colab login
```

---

## 🔧 Alternativas de Túnel

### Cloudflare (atual - padrão) ✅
- **Grátis**
- **Sem token**
- **Sem cadastro**
- URL: `https://xxxx.trycloudflare.com`
- ⚠️ URL muda a cada sessão (temporária)

### Ngrok (antigo - opcional)
Se quiser URL fixa e persistente:
1. Criar conta: https://dashboard.ngrok.com/signup
2. Pegar token: https://dashboard.ngrok.com/get-started/your-authtoken
3. Rodar com token:
```bash
~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b SEU_TOKEN_NGROK
```

---

## 📋 Resumo Ultra-Rápido

```bash
# 1. Rodar
~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b

# 2. Copiar URL que aparecer (ex: https://abc.trycloudflare.com)

# 3. Colar no painel → Local AI → ⚙️ → Atualizar

# Pronto! ✅
```

---

## 🧪 Testando

Depois de configurar, teste:
```bash
curl https://sua-url.trycloudflare.com/api/tags
```

Deve retornar JSON com a lista de modelos instalados.
