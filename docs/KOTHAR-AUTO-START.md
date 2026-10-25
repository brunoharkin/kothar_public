# Como Ativar o Kothar Automaticamente

## Opção 1: Comando `/kothar` (Recomendado)

O comando `/kothar` já está configurado. Ao abrir o Claude Code:

```
$ claude
> /kothar
```

Isso vai mostrar a saudação completa do Kothar v3.0.

---

## Opção 2: Alias no Shell

Adicione um alias no seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Kothar Alias
alias k='claude && ~/.kothar/scripts/kothar-cli.sh activate'
```

Ou um alias mais simples:

```bash
alias kothar='~/.kothar/scripts/kothar-cli.sh'
```

Depois de adicionar, recarregue com:
```bash
source ~/.bashrc  # ou source ~/.zshrc
```

---

## Opção 3: Wrapper do Claude Code

Crie um wrapper que inicia o Claude com o Kothar:

```bash
#!/bin/bash
# Salvar em ~/.local/bin/kothar-claude
export PATH="$HOME/.kothar/scripts:$PATH"
exec claude "$@"
```

---

## Opção 4: Hook de Sessão (Automático)

O hook `kothar-session-init.sh` já está configurado para executar
automaticamente quando o Claude Code inicia. Ele:
- Verifica a estrutura do Kothar
- Verifica ChromaDB
- Verifica MCP
- Registra início de sessão

O hook não mostra output diretamente, mas você pode ver os logs em:
```
~/.claude/hooks/hook.log
```

---

## Verificação Rápida

Para verificar se tudo está configurado:

```bash
# Status do sistema
~/kothar/scripts/kothar-cli.sh status

# Health check
~/kothar/scripts/kothar-cli.sh health

# Verificar hooks
cat ~/.claude/settings.local.json | grep -A 5 "hooks"
```

---

## Estrutura de Comandos

```
~/kothar/scripts/
├── kothar-cli.sh           # CLI principal
├── kothar-welcome.sh       # Saudações
├── kothar-health.sh        # Verificação de saúde
├── kothar-auto-start.sh    # Auto-inicialização
└── kothar-claude.sh        # Wrapper do Claude
```

---

## Comandos Disponíveis

| Comando | Função |
|---------|--------|
| `/kothar` | Ativar Kothar (via slash command) |
| `/kothar status` | Status do sistema |
| `/kothar health` | Verificação completa |
| `/kothar fix` | Corrigir problemas |
| `/kothar start` | Iniciar gravação |
| `/kothar stop` | Parar gravação |

---

## Para Ativar Automaticamente via Alias

Adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Kothar v3.0
export KOTHAR_DIR="$HOME/kothar"

# Função para iniciar Claude com Kothar
kothar() {
    if [ -x "$KOTHAR_DIR/scripts/kothar-cli.sh" ]; then
        $KOTHAR_DIR/scripts/kothar-cli.sh activate
    else
        echo "Kothar não encontrado"
    fi
}

# Alias rápido
alias k='kothar'
```

Depois:
```bash
source ~/.bashrc
k  # Ativa o Kothar
```

---

## Troubleshooting

### Comando `/kothar` não funciona
```bash
# Verificar se está configurado
cat ~/.claude/commands/kothar.toml

# Reinstalar comando
cp ~/kothar/.claude/commands/kothar.toml ~/.claude/commands/
```

### Hook não executa
```bash
# Verificar permissões
chmod +x ~/kothar/hooks/*.sh

# Ver logs
tail -f ~/.claude/hooks/hook.log
```

### Kothar não carrega
```bash
# Verificar estrutura
ls -la ~/kothar/

# Health check
~/kothar/scripts/kothar-cli.sh health
```
