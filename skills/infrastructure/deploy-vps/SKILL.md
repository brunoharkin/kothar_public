---
name: deploy-vps
description: Protocolo completo de deploy de projetos em producao na VPS iContainer com Traefik, Git sync e GitHub Actions. Usar quando for colocar qualquer projeto em producao. Endurecido apos 2 sessoes de erros reais (ChronoDesk + Orbytwin em 2026-09-13).
---

# SKILL: Deploy VPS iContainer (v2.0)

## LEITURA OBRIGATORIA ANTES DE AGIR
```bash
cat ~/kothar/docs/KOTHAR-DEPLOY-PLAYBOOK.md
```

## CHECKLIST — EXECUTAR PRIMEIRO, SEM EXCECAO

```
[ ] Li o KOTHAR-DEPLOY-PLAYBOOK.md completo
[ ] Chave para GitHub Actions eh RSA (BEGIN RSA PRIVATE KEY), nao ed25519
[ ] Testei a chave: ssh -i ~/.ssh/vps-icontainer/id_rsa_github_action root@184.107.115.190 "echo OK"
[ ] Host e username estao HARDCODED no deploy.yml (nao em secrets)
[ ] Rede do projeto eh traefik_public (nao proxy, web, traefik, etc)
[ ] Diretorio na VPS sera /opt/apps/NOME (nao /opt/aplicativo)
[ ] PORT no .env de producao == porta no label loadbalancer.server.port
[ ] .dockerignore contem .env (nao copiar .env para dentro da imagem)
[ ] Migrations pendentes foram geradas e commitadas
[ ] Clone inicial ja existe em /opt/apps/NOME na VPS
[ ] docker network traefik_public existe: ssh vps-icontainer "docker network ls | grep traefik_public"
[ ] DNS apontado para 184.107.115.190 (Cloudflare, tipo A, DNS Only)
[ ] Traefik rodando: ssh vps-icontainer "docker ps | grep traefik"
```

---

## REGRAS DE FERRO (APRENDIDAS NA PRATICA — NAO NEGOCIAVEIS)

### REGRA #1: CHAVE SSH PARA GITHUB ACTIONS
A unica chave correta eh `~/.ssh/vps-icontainer/id_rsa_github_action`
Formato: `-----BEGIN RSA PRIVATE KEY-----`
PROIBIDO usar ed25519 (OPENSSH PRIVATE KEY).

Gerar se nao existir:
```bash
ssh-keygen -t rsa -m PEM -b 4096 -f ~/.ssh/vps-icontainer/id_rsa_github_action -C "github-actions" -N ""
ssh-copy-id -i ~/.ssh/vps-icontainer/id_rsa_github_action.pub vps-icontainer
ssh -i ~/.ssh/vps-icontainer/id_rsa_github_action root@184.107.115.190 "echo CONEXAO OK"
```

No GitHub Secrets: apos colar, pressionar Enter uma vez (newline obrigatorio no final).

### REGRA #2: GITHUB ACTIONS — NUNCA FAZER CLONE NA VPS VIA ACTIONS
O Actions se conecta na VPS e executa git pull. O repo JA deve estar clonado.
NUNCA colocar git clone no script do Actions.

Secrets do GitHub: SOMENTE VPS_SSH_KEY.
Host e username vao hardcoded no deploy.yml.

### REGRA #3: REDE DOCKER SEMPRE traefik_public
Se o projeto veio com nome diferente (proxy, web, etc): renomear antes de subir.

### REGRA #4: DIRETORIO SEMPRE /opt/apps/NOME
Nunca /opt/aplicativo, /srv, /home, etc.

### REGRA #5: PORT sincronizado
PORT no .env de producao = porta no label `loadbalancer.server.port` do docker-compose.
.env local de desenvolvimento NAO vai para a VPS.
.dockerignore DEVE ter `.env` para nao contaminar a imagem Docker.

### REGRA #6: MIGRACAO DE BANCO ANTES DO DEPLOY
Tabelas nao existentes no banco = crash do backend.
Gerar migration e commitar ANTES do push.

---

## TEMPLATES

### deploy.yml (GitHub Actions — template final)
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
          host: 184.107.115.190
          username: root
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

### Labels Traefik no docker-compose.yml
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.NOME.rule=Host(`dominio.ugaritdigital.com`)"
  - "traefik.http.routers.NOME.entrypoints=websecure"
  - "traefik.http.routers.NOME.tls.certresolver=letsencrypt"
  - "traefik.http.services.NOME.loadbalancer.server.port=PORTA"
networks:
  - traefik_public

# No nivel raiz do compose:
networks:
  traefik_public:
    external: true
```

### Clone inicial na VPS
```bash
ssh-add ~/.ssh/id_ed25519_PROJETO
ssh -A vps-icontainer "cd /opt/apps && git clone git@github.com-USUARIO:USUARIO/REPO.git NOME"
```

### Enviar .env de producao
```bash
scp .env.production vps-icontainer:/opt/apps/PROJETO/.env
```

---

## COMANDOS DE VERIFICACAO

```bash
# Pre-deploy
ssh vps-icontainer "docker ps | grep traefik && docker network ls | grep traefik_public"

# Pos-deploy
ssh vps-icontainer "docker ps --format 'table {{.Names}}\t{{.Status}}'"
ssh vps-icontainer "docker logs CONTAINER --tail 30"
curl -I https://dominio.ugaritdigital.com

# Verificar porta sincronizada
ssh vps-icontainer "grep PORT /opt/apps/PROJETO/.env"
ssh vps-icontainer "grep loadbalancer /opt/apps/PROJETO/docker-compose.yml"
```

---

## ESTRUTURA FIXA NA VPS

```
/opt/apps/
├── traefik/              # edge router - nao mexer sem motivo
├── chronodesk/           # https://chronodesk.ugaritdigital.com
├── orbytwin/             # https://orbytwin.ugaritdigital.com
└── PROXIMO_PROJETO/
```

---

*v2.0 — Atualizado apos sessoes ChronoDesk + Orbytwin — 2026-09-13*
