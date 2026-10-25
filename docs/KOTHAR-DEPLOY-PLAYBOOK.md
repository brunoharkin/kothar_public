# KOTHAR DEPLOY PLAYBOOK v1.0
> Gerado em: 2026-09-13 — Aprendido na prática. Nao repetir esses erros.

## O QUE E ISSO

Protocolo operacional de deploy de projetos em producao na VPS iContainer.
Baseado nos erros e acertos reais da sessao de 2026-09-13 (ChronoDesk).

---

## INFRAESTRUTURA DA VPS UGARIT DIGITAL

```
Provider:   iContainer (MTL-02)
IP Publico: 184.107.115.190
OS:         Ubuntu 26.04 LTS x86_64
Hardware:   8 vCPU AMD EPYC 2.6Ghz | 24 GB RAM | 300 GB NVMe
UUID:       20328
Vencimento: 14/10/2026 - R$ 159,90/mes
Alias SSH:  vps-icontainer
```

### Acesso SSH local
```bash
ssh vps-icontainer
# Config em ~/.ssh/config:
# Host vps-icontainer
#     HostName 184.107.115.190
#     User root
#     IdentityFile ~/.ssh/vps-icontainer/id_ed25519
```

---

## TRAEFIK - CONFIGURACAO E REGRAS

### Localizacao na VPS
```
/opt/apps/traefik/
├── docker-compose.yml
└── data/
    ├── traefik.yml       # config estatica
    ├── dynamic_conf.yml  # middlewares (security-headers, redirect-to-https)
    └── acme.json         # certificados Let's Encrypt (chmod 600)
```

### docker-compose.yml do Traefik (producao atual)
```yaml
services:
  traefik:
    image: traefik:latest
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - traefik_public
    ports:
      - 80:80
      - 443:443
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data/traefik.yml:/traefik.yml:ro
      - ./data/dynamic_conf.yml:/dynamic_conf.yml:ro
      - ./data/acme.json:/acme.json
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.rule=Host(`traefik.ugaritdigital.com`)"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.middlewares.traefik-auth.basicauth.users=${TRAEFIK_DASHBOARD_AUTH}"
      - "traefik.http.routers.traefik.middlewares=traefik-auth"
    env_file:
      - .env

networks:
  traefik_public:
    external: true
```

### REGRAS DO TRAEFIK - NUNCA ESQUECER

**1. A rede traefik_public DEVE existir antes de subir qualquer container:**
```bash
docker network create traefik_public
```

**2. So as portas 80 e 443 ficam expostas na internet.** Nenhuma app expoe porta diretamente.

**3. Let's Encrypt** emite SSL automaticamente. acme.json DEVE ter permissao 600:
```bash
touch /opt/apps/traefik/data/acme.json
chmod 600 /opt/apps/traefik/data/acme.json
```

**4. Dashboard Traefik:** traefik.ugaritdigital.com/dashboard/ (com a barra no final)
- Protegido por BasicAuth via variavel TRAEFIK_DASHBOARD_AUTH no .env
- Hash gerado com:
```bash
echo $(htpasswd -nb usuario senha) | sed -e 's/\$/\$\$/g'
```
- Credenciais salvas em: /home/bruno/cofre/.env e /opt/apps/traefik/.env

**5. Adicionar novo projeto ao Traefik (SEM reiniciar o Traefik):**
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.NOME.rule=Host(`dominio.ugaritdigital.com`)"
  - "traefik.http.routers.NOME.entrypoints=websecure"
  - "traefik.http.routers.NOME.tls.certresolver=letsencrypt"
  - "traefik.http.services.NOME.loadbalancer.server.port=PORTA_INTERNA"
networks:
  - traefik_public
```

E no nivel de networks do compose:
```yaml
networks:
  traefik_public:
    external: true
```

---

## GITHUB ACTIONS - DEPLOY AUTOMATICO

### Localizacao do workflow
```
.github/workflows/deploy.yml
```

### Template final (que funcionou no ChronoDesk)
```yaml
name: Deploy to VPS

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: 184.107.115.190       # HARDCODED - nao usar secret para isso
          username: root              # HARDCODED - nao usar secret para isso
          key: ${{ secrets.VPS_SSH_KEY }}
          port: 22
          script: |
            set -e
            cd /opt/apps/NOME_PROJETO
            git reset --hard
            git pull origin main
            docker compose up -d --build
            echo "Deploy concluido."
```

---

## LICOES APRENDIDAS - ERROS REAIS COMETIDOS

### ERRO 1: Chave SSH ed25519 no GitHub Secrets
**Problema:** A chave ed25519 no formato OPENSSH PRIVATE KEY quebra no parser do GitHub Actions.
O appleboy/ssh-action falha silenciosamente com erro de autenticacao.

**Solucao correta:** Sempre usar chave RSA classica formato PEM para GitHub Actions:
```bash
ssh-keygen -t rsa -m PEM -b 4096 -f ~/.ssh/vps-icontainer/id_rsa_github_action -C "github-actions-deploy" -N ""
# Instalar na VPS:
ssh-copy-id -i ~/.ssh/vps-icontainer/id_rsa_github_action.pub vps-icontainer
# Testar conexao ANTES de configurar no GitHub:
ssh -i ~/.ssh/vps-icontainer/id_rsa_github_action root@184.107.115.190 "echo CONEXAO OK"
```

Formato correto (funciona no GitHub Actions):
```
-----BEGIN RSA PRIVATE KEY-----
(corpo)
-----END RSA PRIVATE KEY-----
```

NUNCA usar (quebra no GitHub Actions):
```
-----BEGIN OPENSSH PRIVATE KEY-----
```

### ERRO 2: Usar secrets do GitHub para HOST e USERNAME
**Problema:** Espacos invisiveis no painel do GitHub fazem o action tentar conectar num endereco quebrado.
**Solucao:** IP e USERNAME sempre hardcoded no deploy.yml. So a chave SSH fica em secret.

### ERRO 3: Nao ter newline no final da chave RSA no GitHub Secrets
**Solucao:** Apos colar a chave, pressionar Enter uma vez para garantir newline no final.

### ERRO 4: Deploy puxando branch errada
**Problema:** O workflow dizia git pull origin main mas o trabalho estava em outra branch.
**Solucao:** Sempre fazer merge na main antes do deploy definitivo:
```bash
git checkout main
git merge release/v3.0.0-feature
git push origin main
```

### ERRO 5: Certificado SSL em cache no browser
**Problema:** Na primeira subida, o Let's Encrypt demora ~30s. O browser cacheia o certificado temporario.
**Solucao:** Usar janela anonima (Ctrl+Shift+N) ou Ctrl+F5 para limpar cache.

### ERRO 6: Node.js dependency conflict no Dockerfile
**Solucao:** Adicionar flag --legacy-peer-deps no npm install do Dockerfile:
```dockerfile
RUN npm install --legacy-peer-deps
```

---

## CONFIGURACAO DE SECRETS NO GITHUB

**Onde configurar:**
GitHub -> Repositorio -> Settings -> Secrets and variables -> Actions -> New repository secret

| Secret Name   | Valor                                                    |
|---------------|----------------------------------------------------------|
| VPS_SSH_KEY   | Conteudo inteiro da chave RSA PEM (BEGIN + corpo + END + Enter no final) |

IP e USERNAME vao hardcoded no deploy.yml. NAO criar secrets para eles.

---

## DEPLOY INICIAL - CLONE NA VPS

Para fazer o clone inicial de um projeto privado na VPS via SSH Agent Forwarding:

```bash
# Na maquina local (seu PC):
ssh-add ~/.ssh/id_ed25519_PROJETO   # Adiciona chave ao agente local
ssh -A vps-icontainer               # Conecta com ForwardAgent ativado

# Dentro da VPS (ja conectado):
mkdir -p /opt/apps
cd /opt/apps
git clone git@github.com-USUARIO:USUARIO/REPOSITORIO.git NOME_PROJETO
```

Isso usa a chave local temporariamente para clonar, sem expor nada na VPS.

---

## ESTRUTURA DE DIRETORIOS NA VPS

```
/opt/apps/
├── traefik/
│   ├── docker-compose.yml
│   ├── .env                    # TRAEFIK_DASHBOARD_AUTH
│   └── data/
│       ├── traefik.yml
│       ├── dynamic_conf.yml
│       └── acme.json (chmod 600)
├── chronodesk/                 # Clonado do GitHub
│   ├── docker-compose.yml
│   ├── .env                    # Secrets de producao (NAO versionado)
│   └── ...
└── PROXIMO_PROJETO/
    └── ...
```

---

## PROTOCOLO DE DEPLOY DE NOVO PROJETO

### PRE-REQUISITOS (verificar antes de comecar)

```bash
# 1. VPS online
ssh vps-icontainer "echo 'VPS OK'"

# 2. Traefik rodando
ssh vps-icontainer "docker ps | grep traefik"

# 3. Rede traefik_public existe
ssh vps-icontainer "docker network ls | grep traefik_public"

# 4. DNS apontado para 184.107.115.190 (verificar no Cloudflare)
# Criar registro A: dominio.ugaritdigital.com -> 184.107.115.190
# Tipo: DNS Only (nuvem cinza), nao proxied
```

### PASSO A PASSO COMPLETO

**1. Gerar chaves SSH**
```bash
# Chave RSA para GitHub Actions (OBRIGATORIO RSA, nao ed25519)
ssh-keygen -t rsa -m PEM -b 4096 -f ~/.ssh/vps-icontainer/id_rsa_github_action -C "github-actions-PROJETO" -N ""
ssh-copy-id -i ~/.ssh/vps-icontainer/id_rsa_github_action.pub vps-icontainer
ssh -i ~/.ssh/vps-icontainer/id_rsa_github_action root@184.107.115.190 "echo CONEXAO OK"
```

**2. Clone do projeto na VPS**
```bash
ssh-add ~/.ssh/id_ed25519_PROJETO
ssh -A vps-icontainer "mkdir -p /opt/apps && cd /opt/apps && git clone git@github.com-USUARIO:USUARIO/REPO.git NOME"
```

**3. Criar .env de producao na VPS**
```bash
scp .env.production vps-icontainer:/opt/apps/PROJETO/.env
```

**4. Criar docker-compose com labels Traefik**
Obrigatorio no container que deve ser exposto:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.NOME.rule=Host(`dominio.ugaritdigital.com`)"
  - "traefik.http.routers.NOME.entrypoints=websecure"
  - "traefik.http.routers.NOME.tls.certresolver=letsencrypt"
  - "traefik.http.services.NOME.loadbalancer.server.port=PORTA_INTERNA"
networks:
  - traefik_public
```

**5. Subir containers na VPS**
```bash
ssh vps-icontainer "cd /opt/apps/PROJETO && docker compose up -d --build"
```

**6. Configurar GitHub Actions**
- Criar .github/workflows/deploy.yml (usar template acima)
- GitHub -> Settings -> Secrets -> VPS_SSH_KEY (chave RSA PEM + Enter no final)
- Push para main para disparar

**7. Verificacao final**
```bash
ssh vps-icontainer "docker ps"
ssh vps-icontainer "docker logs traefik --tail 30"
curl -I https://dominio.ugaritdigital.com
```

---

## DOCUMENTACAO QUE DEVE SER CRIADA A CADA PROJETO

Sempre criar/atualizar:
1. ~/cofre/empresa/DOCUMENTOS-MESTRES/INFRAESTRUTURA-VPS-TRAEFIK.md (adicionar nova entrada)
2. ~/cofre/empresa/DOCUMENTOS-MESTRES/NOME_PROJETO-PRODUCAO.md (doc de producao)
3. ~/cofre/empresa/Financeiro_Saidas.md (se houver custo)

---

## MENSAGENS DE COMMIT (OBRIGATORIO)

- Sempre em Portugues Brasileiro
- Descritivo da alteracao tecnica (nao do agente)
- Sem assinaturas de bot/IA
- Corretos:
  - "Configura GitHub Actions para deploy automatico via SSH"
  - "Adiciona Traefik com SSL Let's Encrypt para ambiente de producao"
  - "Corrige Dockerfile do frontend com flag --legacy-peer-deps"

---

## COMANDOS DE VERIFICACAO RAPIDA

```bash
# Status geral da VPS
ssh vps-icontainer "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Logs de um servico
ssh vps-icontainer "docker logs CONTAINER --tail 50"

# Rebuild completo manual
ssh vps-icontainer "cd /opt/apps/PROJETO && git reset --hard && git pull && docker compose up -d --build"

# Verificar se traefik pegou o servico
ssh vps-icontainer "docker logs traefik --tail 30 2>&1 | grep -i NOME_PROJETO"
```

---

## PROJETOS EM PRODUCAO NA VPS

| Projeto    | URL                                  | Diretorio VPS        | Branch |
|------------|--------------------------------------|----------------------|--------|
| ChronoDesk | https://chronodesk.ugaritdigital.com | /opt/apps/chronodesk | main   |
| Traefik    | https://traefik.ugaritdigital.com    | /opt/apps/traefik    | -      |

---

*Ultima atualizacao: 2026-09-13 - Kothar v3.0*

---

## SESSAO 2 — ORBYTWIN (2026-09-13) — ERROS NOVOS

### ERRO 7: Usar ed25519 para GitHub Actions (repetido — CRITICO)
**O que aconteceu:** O agente entregou a chave `~/.ssh/vps-icontainer/id_ed25519` (formato OPENSSH) como SSH_PRIVATE_KEY.
O usuario corrigiu: "esse modelo de chave nao serve, use o mesmo que criou no ChronoDesk".
**O agente nao releu o playbook antes de agir.**

**REGRA ABSOLUTA:**
ANTES de qualquer deploy, ler: `~/kothar/docs/KOTHAR-DEPLOY-PLAYBOOK.md`
Chave para GitHub Actions = SEMPRE `id_rsa_github_action` (RSA PEM, BEGIN RSA PRIVATE KEY).
Chave de acesso pessoal = `id_ed25519` (ed25519, apenas para ssh manual).

### ERRO 8: Usar SSH_HOST e SSH_USER como secrets
**O que aconteceu:** O agente criou 3 secrets: SSH_PRIVATE_KEY, SSH_HOST, SSH_USER.
SSH_HOST e SSH_USER nunca devem ser secrets. Espacos invisiveis causam falha de conexao.
**Correto:** host e username hardcoded no deploy.yml. SO a chave SSH vai em secret.

### ERRO 9: Nao verificar se VPS tem acesso SSH ao GitHub antes de criar workflow de clone
**O que aconteceu:** O agente criou workflow com `git clone git@github.com:...` dentro da VPS,
sem verificar se a VPS tem Deploy Key ou acesso SSH ao GitHub. Resultado: Permission denied.
Depois tentou PAT (GH_PAT), adicionando complexidade desnecessaria.

**REGRA:** Jamas fazer clone na VPS via GitHub Actions. O padrao correto e:
- Actions conecta na VPS via SSH
- Na VPS, roda `git pull` (o repo JA esta clonado previamente via SSH Agent Forwarding)
- O `git pull` funciona porque o remote usa HTTPS com token embutido no clone inicial OU
  porque a VPS tem acesso ao GitHub via chave dedicada na pasta do projeto

**Template correto para repositorio privado na VPS:**
Clone inicial:
```bash
# Local com agent forwarding
ssh-add ~/.ssh/id_ed25519_PROJETO
ssh -A vps-icontainer "cd /opt/apps && GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_PROJETO' git clone git@github.com-USUARIO:USUARIO/REPO.git NOME"
```

Ou via HTTPS com token no clone inicial (mais simples):
```bash
ssh vps-icontainer "cd /opt/apps && git clone https://ghp_TOKEN@github.com/USUARIO/REPO.git NOME"
```
Depois do clone, `git pull` dentro da VPS funciona sem precisar de chave.

### ERRO 10: Diretório de deploy inconsistente
**O que aconteceu:** O agente usou /opt/aplicativo/orbytwin em vez de /opt/apps/PROJETO.
**Padrao definido:** SEMPRE /opt/apps/NOME_PROJETO. Nunca /opt/aplicativo.

### ERRO 11: Nome da rede Docker inconsistente
**O que aconteceu:** O docker-compose do Orbytwin usava rede chamada `proxy` em vez de `traefik_public`.
O Traefik da VPS usa a rede `traefik_public`.
**Regra:** A rede external que conecta ao Traefik SEMPRE se chama `traefik_public`.
Se o projeto vier com outro nome (proxy, web, etc.), RENOMEAR para traefik_public.

### ERRO 12: .env local copiado para VPS sem validacao
**O que aconteceu:** O agente usou rsync para copiar o .env local (desenvolvimento) para a VPS.
O .env local tinha PORT=3002 (desenvolvimento). A VPS precisava de PORT=3001 (producao).
O backend subiu na porta errada. Traefik tentou 3001. Bad Gateway por horas.

**Regra:** Antes de copiar .env para a VPS:
1. Verificar cada variavel critica: PORT, DATABASE_URL, REDIS_URL
2. PORT deve ser a MESMA configurada no docker-compose (label loadbalancer.server.port)
3. Nunca usar o .env de desenvolvimento diretamente. Criar um .env.production especifico.

### ERRO 13: .env do backend copiado para dentro do container via Docker COPY
**O que aconteceu:** O Dockerfile fez COPY do backend/.env para dentro da imagem.
Isso faz o dotenv do Node carregar o .env interno (porta errada) ignorando as variaveis do compose.
**Regra:** Adicionar *.env ao .dockerignore do projeto. .env NUNCA deve entrar na imagem Docker.
Variaveis de ambiente entram EXCLUSIVAMENTE via docker-compose env_file ou environment.

### ERRO 14: Porta do backend no Traefik label nao sincronizada com PORT do .env
**Regra:** A porta no label `traefik.http.services.NOME.loadbalancer.server.port=PORTA`
deve ser IDENTICA ao valor de PORT no .env de producao.
Verificar sempre:
```bash
grep PORT /opt/apps/PROJETO/.env
# deve ser igual a:
grep loadbalancer.server.port /opt/apps/PROJETO/docker-compose.yml
```

### ERRO 15: Migracao de banco nao gerada antes do deploy
**O que aconteceu:** SessionConfirmation foi adicionada ao schema.prisma mas a migration .sql nao foi gerada.
Backend crashou ao tentar usar a tabela que nao existia no banco da VPS.

**Regra para projetos com Prisma/ORM:**
ANTES de fazer deploy:
```bash
# Gerar migration pendente
npx prisma migrate dev --name DESCRICAO_DA_MUDANCA

# Verificar que o arquivo SQL foi gerado em prisma/migrations/
ls prisma/migrations/

# Commitar a migration junto com o codigo
git add prisma/migrations/
```

Na VPS, o deploy.yml deve rodar migrate antes de restart:
```bash
docker exec BACKEND npx prisma migrate deploy
```

---

## CHECKLIST ANTI-ERROS (ANTES DE COMECAR QUALQUER DEPLOY)

```
[ ] Li o ~/kothar/docs/KOTHAR-DEPLOY-PLAYBOOK.md completo
[ ] A chave para GitHub Actions e RSA (BEGIN RSA PRIVATE KEY), nao ed25519
[ ] Testei a chave RSA: ssh -i id_rsa_github_action root@IP "echo OK"
[ ] Host e username estao HARDCODED no deploy.yml (nao em secrets)
[ ] Rede Docker do projeto e traefik_public (nao proxy, web, etc)
[ ] Diretorio na VPS e /opt/apps/NOME (nao /opt/aplicativo)
[ ] PORT no .env de producao == porta no label loadbalancer.server.port
[ ] .dockerignore contem *.env e .env
[ ] Migrations pendentes foram geradas e commitadas
[ ] Clone inicial foi feito na VPS (projeto ja existe em /opt/apps/NOME)
[ ] docker network create traefik_public (se ainda nao existir)
[ ] DNS apontado para 184.107.115.190 (tipo A, DNS Only no Cloudflare)
```

*Atualizado: 2026-09-13 — sessao Orbytwin*
