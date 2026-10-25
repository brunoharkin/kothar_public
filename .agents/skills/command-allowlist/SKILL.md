---
name: command-allowlist
description: >-
  Skill do Kothar: Command Allowlist. Ativar quando necessário para execução da habilidade command-allowlist.
---

# Command Allowlist

> **Skill:** Kothar Command Allowlist  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw command allowlist + Kothar NousResearch container isolation  

---

## 🎯 Objetivo

Sistema de allowlist para comandos perigosos que protege contra execução acidental.

**Problema resolvido:** Kothar executa comandos perigosos (rm -rf, git push --force).

---

## 📋 Categorias

```
┌─────────────────────────────────────────────────────────────┐
│ COMMAND CATEGORIES                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ SAFE          Executa direto, sem confirmação          │
│     ls, cat, grep, find, pwd, echo, head, tail, wc         │
│                                                              │
│  ⚠️  CONFIRM      Pede confirmação antes de executar        │
│     rm (arquivos), mv, cp, git commit, git branch           │
│                                                              │
│  🔴 DANGEROUS    Bloqueia, exige override explícito        │
│     rm -rf, dd, mkfs, git push --force, chmod 777           │
│                                                              │
│  🚫 CRITICAL      Sempre nega, não permite override         │
│     fork bomb, :(){ :|:& };:, rm -rf /                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Regras Detalhadas

```javascript
const allowlistRules = {
  // SAFE — executa direto
  safe: [
    'ls', 'ls -la', 'ls -l', 'ls -a',
    'cat', 'cat -n',
    'grep', 'grep -r', 'grep -n', 'grep -i',
    'find', 'find .', 'find -name',
    'pwd',
    'echo', 'echo -n',
    'head', 'head -n',
    'tail', 'tail -n', 'tail -f',
    'wc', 'wc -l',
    'cd', // com caminho válido
    'mkdir -p', // com caminho válido
    'stat',
    'file',
    'which',
    'type',
    'date',
    'whoami',
    'id',
    'ps aux', // sem kill
    'df -h',
    'du -sh',
    'curl -s', // GET simples
    'git status',
    'git log --oneline',
    'git diff --stat'
  ],
  
  // CONFIRM — pede confirmação
  confirm: [
    // Remoção (com caminho específico)
    { cmd: /^rm\s+/, reason: 'Remoção de arquivo' },
    { cmd: /^rmdir\s+/, reason: 'Remoção de diretório' },
    // Modificação
    { cmd: /^mv\s+/, reason: 'Movimentação de arquivo' },
    { cmd: /^cp\s+/, reason: 'Cópia de arquivo' },
    // Git (sem push destrutivo)
    { cmd: /^git\s+commit/, reason: 'Git commit' },
    { cmd: /^git\s+branch/, reason: 'Git branch' },
    { cmd: /^git\s+checkout/, reason: 'Git checkout' },
    { cmd: /^git\s+add\s+/, reason: 'Git add' },
    { cmd: /^git\s+reset\s+/, reason: 'Git reset' },
    { cmd: /^git\s+stash/, reason: 'Git stash' },
    // Bash scripts
    { cmd: /\.sh$/, reason: 'Executar script' },
    // npm/yarn
    { cmd: /^npm\s+install/, reason: 'npm install' },
    { cmd: /^yarn\s+install/, reason: 'yarn install' },
    // Docker
    { cmd: /^docker\s+stop/, reason: 'Docker stop' },
    { cmd: /^docker\s+rm/, reason: 'Docker rm' },
    // systemctl
    { cmd: /^systemctl\s+restart/, reason: 'systemctl restart' },
    { cmd: /^systemctl\s+stop/, reason: 'systemctl stop' }
  ],
  
  // DANGEROUS — bloqueia, override explícito
  dangerous: [
    // Remoção forçada/recursiva
    { cmd: /rm\s+-[rfv]+\s+/, reason: 'Remoção forçada/recursiva' },
    { cmd: /rm\s+-[rfv]+$/, reason: 'Remoção forçada/recursiva' },
    // git push forçado
    { cmd: /git\s+push\s+.*--force/, reason: 'Git force push' },
    { cmd: /git\s+push\s+-f/, reason: 'Git force push' },
    { cmd: /git\s+push\s+--delete/, reason: 'Git push delete (branch)' },
    // chmod perigoso
    { cmd: /chmod\s+777/, reason: 'chmod 777 (sem segurança)' },
    { cmd: /chmod\s+000/, reason: 'chmod 000' },
    { cmd: /chmod\s+-R\s+777/, reason: 'chmod recursivo 777' },
    // Sobrescrever device
    { cmd: /dd\s+.*of=/, reason: 'dd para device (destrutivo)' },
    // mkfs
    { cmd: /mkfs/, reason: 'Formatar filesystem' },
    // Destruição de dados
    { cmd: /shred\s+/, reason: 'Sobrescrever arquivo' },
    { cmd: /dd\s+.*of=\/dev\/null/, reason: 'dd para null (gasta dados)' },
    // Docker danger
    { cmd: /docker\s+system\s+prune/, reason: 'Docker system prune' },
    { cmd: /docker\s+volume\s+rm/, reason: 'Docker volume rm' },
    { cmd: /docker\s+rm\s+--force/, reason: 'Docker force rm' },
    // Pipe para sh (security)
    { cmd: /\|\s*sh$/, reason: 'Pipe para shell' },
    { cmd: /\|*\s*bash$/, reason: 'Pipe para bash' },
    // Download + execute
    { cmd: /curl.*\|.*sh/, reason: 'Download e execute' },
    { cmd: /wget.*\|.*sh/, reason: 'Download e execute' },
    // SSH com chaves fracas
    { cmd: /ssh.*-o\s+StrictHostKeyChecking=no.*password/, reason: 'SSH inseguro' }
  ],
  
  // CRITICAL — nunca permite
  critical: [
    // Fork bomb
    { cmd: /:\s*\(\s*\)\s*:\s*\|/, reason: 'Fork bomb detectada' },
    { cmd: /\|\s*&/, pattern: /:.*:.*\|.*&/ },
    // rm rf no root
    { cmd: /rm\s+-rf\s+\//, reason: 'rm -rf / (destrói sistema)' },
    { cmd: /rm\s+-rf\s+\/\*/, reason: 'rm -rf /* (destrói sistema)' },
    { cmd: /rm\s+-rf\s+\.\*/i, reason: 'rm -rf .* (pode destruir tudo)' },
    // dd para device crítico
    { cmd: /dd\s+.*of=\/dev\/sd/, reason: 'dd para device disco' },
    { cmd: /dd\s+.*of=\/dev\/nvme/, reason: 'dd para NVMe' },
    // killall
    { cmd: /killall\s+-9/, reason: 'killall -9 (destrutivo)' },
    // Regras de firewall (pode se trancar)
    { cmd: /iptables\s+-A.*DROP.*--source/, reason: 'iptables DROP (pode se trancar)' },
    // Desabilitar segurança
    { cmd: /chmod\s+-x\s+\/usr\/bin/, reason: 'Remover permissão de execução' },
    // Modificar /etc/passwd
    { cmd: />\s*\/etc\/passwd/, reason: 'Sobrescrever /etc/passwd' },
    // Enviar spam/malware
    { cmd: /mail\s+.*<.*\/etc\/passwd/, reason: 'Enviar arquivo sensível por email' }
  ]
}
```

---

## 🔧 Implementação

```javascript
class CommandAllowlist {
  constructor(config = {}) {
    this.config = {
      dangerousOverride: config.dangerousOverride || false,
      logAllCommands: config.logAllCommands !== false,
      ...config
    }
    
    this.commandHistory = []
  }
  
  // Verificar comando
  check(command) {
    const normalized = this.normalize(command)
    const category = this.categorize(normalized)
    
    const result = {
      command,
      normalized,
      category,
      allowed: category === 'safe' || category === 'confirm_approved',
      requiresConfirm: category === 'confirm',
      blocked: category === 'dangerous' || category === 'critical',
      dangerous: category === 'dangerous',
      critical: category === 'critical',
      reason: null
    }
    
    if (category === 'confirm') {
      const rule = this.findRule('confirm', normalized)
      result.reason = rule?.reason || 'Requer confirmação'
    } else if (category === 'dangerous') {
      const rule = this.findRule('dangerous', normalized)
      result.reason = rule?.reason || 'Comando perigoso bloqueado'
    } else if (category === 'critical') {
      const rule = this.findRule('critical', normalized)
      result.reason = rule?.reason || 'Comando crítico, nunca permitido'
    }
    
    // Log
    if (this.config.logAllCommands) {
      this.logCommand(result)
    }
    
    return result
  }
  
  // Normalizar comando (remover escapes, etc)
  normalize(command) {
    return command
      .trim()
      .replace(/\s+/g, ' ')
      .replace(/\\\n/g, ' ')
      .replace(/;.*$/, '') // Remover após ;
  }
  
  // Categorizar
  categorize(command) {
    // CRITICAL (nunca permite)
    for (const rule of allowlistRules.critical) {
      if (rule.pattern ? rule.pattern.test(command) : rule.cmd.test(command)) {
        return 'critical'
      }
    }
    
    // DANGEROUS (bloqueia se não override)
    for (const rule of allowlistRules.dangerous) {
      if (rule.pattern ? rule.pattern.test(command) : rule.cmd.test(command)) {
        return this.config.dangerousOverride ? 'dangerous_override' : 'dangerous'
      }
    }
    
    // CONFIRM
    for (const rule of allowlistRules.confirm) {
      if (rule.cmd.test(command)) {
        return 'confirm'
      }
    }
    
    // SAFE
    for (const safe of allowlistRules.safe) {
      if (command === safe || command.startsWith(safe + ' ')) {
        return 'safe'
      }
    }
    
    // Desconhecido — treat as confirm
    return 'unknown'
  }
  
  // Encontrar regra
  findRule(category, command) {
    const rules = allowlistRules[category] || []
    return rules.find(rule => 
      rule.pattern ? rule.pattern.test(command) : rule.cmd.test(command)
    )
  }
  
  // Aprovar confirmação
  approve(command) {
    this.commandHistory.push({
      command,
      approved: true,
      timestamp: Date.now()
    })
  }
  
  // Log
  logCommand(result) {
    log.info('Command check', {
      category: result.category,
      command: result.normalized,
      allowed: result.allowed,
      reason: result.reason
    })
  }
}
```

---

## 🔧 Integração com Bash Tool

```javascript
// Hook de segurança
const securityHook = {
  name: 'command-allowlist',
  event: 'before_tool_call',
  priority: 100, // Executa primeiro!
  callback: async (context) => {
    if (context.tool !== 'Bash') return
    
    const check = commandAllowlist.check(context.params.command)
    
    if (check.critical) {
      throw new Error(`🚫 COMANDO CRÍTICO BLOQUEADO: ${check.reason}`)
    }
    
    if (check.blocked) {
      throw new Error(`🔴 COMANDO PERIGOSO BLOQUEADO: ${check.reason}\n\nPara forçar, use: kothar override enable`)
    }
    
    if (check.requiresConfirm) {
      // Notificar Bruno
      const approved = await askUser({
        type: 'confirm',
        message: `⚠️ Este comando requer confirmação:\n\n\`${check.command}\`\n\n${check.reason}\n\nExecutar?`,
        actions: ['Sim', 'Não']
      })
      
      if (!approved) {
        throw new Error('Comando cancelado pelo usuário')
      }
      
      commandAllowlist.approve(check.command)
    }
    
    // SAFE — continua
  }
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `allowlist check "comando"` | Verificar se comando é seguro |
| `allowlist list` | Listar categorias |
| `allowlist override enable` | Habilitar override de perigosos |
| `allowlist override disable` | Desabilitar override |
| `allowlist history` | Ver histórico de comandos |

---

## 📝 Exemplo de Output

```
$ kothar allowlist check "rm -rf /tmp/test"

┌─────────────────────────────────────────────────────────────┐
│ COMMAND CHECK                                               │
├─────────────────────────────────────────────────────────────┤
│ Command:    rm -rf /tmp/test                               │
│ Category:   ⚠️ CONFIRM                                    │
│ Reason:     Remoção forçada/recursiva                       │
│                                                              │
│ ℹ️  Este comando remove arquivos de forma forçada.          │
│                                                              │
│ [Sim] [Não]                                                │
└─────────────────────────────────────────────────────────────┘

$ kothar allowlist check "rm -rf /"

┌─────────────────────────────────────────────────────────────┐
│ COMMAND CHECK                                               │
├─────────────────────────────────────────────────────────────┤
│ Command:    rm -rf /                                      │
│ Category:   🚫 CRITICAL                                    │
│ Reason:     rm -rf / (destrói sistema)                     │
│                                                              │
│ 🚫 BLOQUEADO — Override não permitido                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] SAFE executa direto
- [ ] CONFIRM pede confirmação
- [ ] DANGEROUS bloqueia (com override opcional)
- [ ] CRITICAL sempre bloqueia
- [ ] Histórico é mantido
- [ ] Logs são gerados

---

## 🔗 Integração

| Componente | Como usa command-allowlist |
|------------|--------------------------|
| hooks-system | before_tool_call hook |
| fault-tolerance | Bloqueio em retry |
| logging | Log de comandos bloqueados |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
