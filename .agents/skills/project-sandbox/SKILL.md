---
name: project-sandbox
description: >-
  Skill do Kothar: Project Sandbox. Ativar quando necessário para execução da habilidade project-sandbox.
---

# Project Sandbox

> **Skill:** Kothar Project Sandbox  
> **Versão:** 1.0  
> **Data:** 2026-06-18  
> **Inspiration:** OpenClaw workspace isolation + Kothar NousResearch session isolation  

---

## 🎯 Objetivo

Sistema de isolamento de contexto por projeto. Cada projeto tem seu próprio PWD, SSH key, memórias e skills.

**Problema resolvido:** Kothar mistura projetos, contaminando contexto.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│ PROJECT SANDBOX                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PROJETO: disparo-em-massa                          │   │
│  │ ├─ PWD: /home/bruno/disparo-em-massa              │   │
│  │ ├─ SSH: ~/.ssh/id_ed25519_disparo                 │   │
│  │ ├─ Memory: ~/.kothar/memory/project/disparo/      │   │
│  │ ├─ Skills: [frontend, bug-analyst, security]      │   │
│  │ └─ Allowlist: [padrão + específicos]              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PROJETO: ratoflix                                 │   │
│  │ ├─ PWD: /home/bruno/ratoflix                      │   │
│  │ ├─ SSH: ~/.ssh/id_ed25519_ratoflix               │   │
│  │ ├─ Memory: ~/.kothar/memory/project/ratoflix/     │   │
│  │ ├─ Skills: [frontend, bug-analyst]               │   │
│  │ └─ Allowlist: [padrão]                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PROJETO: kothar (default)                          │   │
│  │ ├─ PWD: /home/bruno/Cofre                         │   │
│  │ ├─ SSH: ~/.ssh/id_ed25519_kothar                  │   │
│  │ ├─ Memory: ~/.kothar/memory/project/kothar/       │   │
│  │ ├─ Skills: [todas]                                │   │
│  │ └─ Allowlist: [padrão]                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Configuração

```javascript
const projectSandbox = {
  // Projeto atual (detectado automaticamente)
  current: null,
  
  // Projetos configurados
  projects: {
    'kothar': {
      name: 'Kothar (Agente)',
      root: '/home/bruno/Cofre',
      pwd: '/home/bruno/Cofre',
      sshKey: '~/.ssh/id_ed25519_kothar',
      memoryDir: 'memory/project/kothar',
      skills: ['*'], // Todas as skills
      allowlist: 'default',
      description: 'Sistema Kothar e cofres'
    },
    
    'disparo-em-massa': {
      name: 'Disparo em Massa',
      root: '/home/bruno/disparo-em-massa',
      pwd: '/home/bruno/disparo-em-massa',
      sshKey: '~/.ssh/id_ed25519_disparo',
      memoryDir: 'memory/project/disparo-em-massa',
      skills: ['frontend-ugarit', 'bug-analyst', 'security', 'mercadopago-mcp', 'ga4'],
      allowlist: 'default',
      description: 'Sistema de disparo em massa da Ugarit'
    },
    
    'ratoflix': {
      name: 'Ratoflix',
      root: '/home/bruno/ratoflix',
      pwd: '/home/bruno/ratoflix',
      sshKey: '~/.ssh/id_ed25519_ratoflix',
      memoryDir: 'memory/project/ratoflix',
      skills: ['frontend-ugarit', 'bug-analyst', 'security'],
      allowlist: 'default',
      description: 'Sistema Ratoflix para Dimitri'
    },
    
    'bioleads': {
      name: 'BioLeads',
      root: '/home/bruno/bioleads',
      pwd: '/home/bruno/bioleads',
      sshKey: '~/.ssh/id_ed25519_bioleads',
      memoryDir: 'memory/project/bioleads',
      skills: ['frontend-ugarit', 'bug-analyst', 'security', 'ga4'],
      allowlist: 'default',
      description: 'Plataforma BioLeads'
    }
  },
  
  // Regras de isolamento
  isolation: {
    // Validar PWD antes de cada comando
    validatePwd: true,
    // Validar SSH key antes de git
    validateSsh: true,
    // Isolar memórias por projeto
    isolateMemory: true,
    // Filtrar skills por projeto
    filterSkills: true,
    // Avisar se sair do diretório do projeto
    warnOnEscape: true
  }
}
```

---

## 🔧 Implementação

```javascript
class ProjectSandbox {
  constructor(config = {}) {
    this.config = {
      ...projectSandbox,
      ...config
    }
    
    this.currentProject = null
    this.previousProject = null
    this.projectStartTime = null
    
    // Hooks
    this.onProjectChange = []
  }
  
  // Detectar projeto atual
  detectProject() {
    const pwd = process.cwd()
    
    // Procurar projeto pelo path
    for (const [key, project] of Object.entries(this.config.projects)) {
      if (pwd.startsWith(project.root)) {
        return key
      }
    }
    
    // Default para kothar se não encontrar
    return 'kothar'
  }
  
  // Entrar em projeto
  enterProject(projectKey) {
    const project = this.config.projects[projectKey]
    if (!project) {
      throw new Error(`Projeto desconhecido: ${projectKey}`)
    }
    
    this.previousProject = this.currentProject
    this.currentProject = projectKey
    this.projectStartTime = Date.now()
    
    // Mudar PWD se necessário
    if (process.cwd() !== project.pwd) {
      try {
        process.chdir(project.pwd)
      } catch (e) {
        log.warn('Could not change directory', { 
          expected: project.pwd, 
          error: e.message 
        })
      }
    }
    
    // Atualizar logger
    logger.setProject(projectKey)
    
    // Atualizar métricas
    metrics.setProject(projectKey)
    
    // Notificar mudança
    if (this.previousProject !== this.currentProject) {
      this.onProjectChange.forEach(fn => fn({
        from: this.previousProject,
        to: this.currentProject,
        project: this.config.projects[this.currentProject]
      }))
    }
    
    log.info('Project entered', {
      project: projectKey,
      name: project.name,
      pwd: project.pwd
    })
    
    return project
  }
  
  // Validar operação no projeto atual
  validate(operation, context = {}) {
    if (!this.currentProject) {
      return { valid: true, reason: 'no_project_set' }
    }
    
    const project = this.config.projects[this.currentProject]
    const pwd = context.pwd || process.cwd()
    
    // Validar PWD
    if (this.config.isolation.validatePwd) {
      if (!pwd.startsWith(project.root)) {
        return {
          valid: false,
          reason: 'pwd_outside_project',
          message: `⚠️ PWD está fora do projeto.\n\n` +
                   `Esperado: ${project.root}\n` +
                   `Atual: ${pwd}\n\n` +
                   `Continuar?`,
          current: pwd,
          expected: project.root,
          project: this.currentProject
        }
      }
    }
    
    return { valid: true }
  }
  
  // Validar SSH key para git
  validateSsh(operation) {
    if (!this.currentProject) return { valid: true }
    
    const project = this.config.projects[this.currentProject]
    
    // Expandir path da chave
    const sshKeyPath = expandHome(project.sshKey)
    
    // Verificar se chave existe
    if (!fs.existsSync(sshKeyPath)) {
      log.warn('SSH key not found', { 
        project: this.currentProject,
        key: sshKeyPath 
      })
      
      return {
        valid: false,
        reason: 'ssh_key_missing',
        message: `🔑 Chave SSH não encontrada para ${project.name}.\n\n` +
                 `Esperada: ${sshKeyPath}\n\n` +
                 `Verificar configuração?`
      }
    }
    
    return { valid: true }
  }
  
  // Obter skills do projeto
  getProjectSkills() {
    if (!this.currentProject) return []
    
    const project = this.config.projects[this.currentProject]
    
    if (project.skills.includes('*')) {
      return null // Todas as skills
    }
    
    return project.skills
  }
  
  // Obter memória do projeto
  getProjectMemoryDir() {
    if (!this.currentProject) return null
    
    const project = this.config.projects[this.currentProject]
    return path.join(process.env.HOME, '.kothar', project.memoryDir)
  }
  
  // Hook de mudança de projeto
  onProjectSwitch(callback) {
    this.onProjectChange.push(callback)
  }
  
  // Status do sandbox
  getStatus() {
    return {
      currentProject: this.currentProject,
      project: this.currentProject ? this.config.projects[this.currentProject] : null,
      pwd: process.cwd(),
      uptime: this.projectStartTime ? Date.now() - this.projectStartTime : 0,
      previousProject: this.previousProject
    }
  }
}
```

---

## 🔄 Validação em R1-R5

### R1: Carregar Contexto

```javascript
// Após detectar projeto
const detected = sandbox.detectProject()
if (detected !== sandbox.currentProject) {
  const project = sandbox.enterProject(detected)
  
  // Nudgar se mudou de projeto
  if (sandbox.previousProject) {
    notify({
      type: 'project_switch',
      message: `🔄 Mudando de [${sandbox.previousProject}] para [${detected}]`,
      actions: [
        { label: 'Confirmar', action: 'continue' },
        { label: 'Cancelar', action: 'cancel' }
      ]
    })
  }
}
```

### R2: Planejar Antes de Agir

```javascript
// Validar que está no projeto certo
const validation = sandbox.validate('plan', { pwd: process.cwd() })
if (!validation.valid) {
  throw new Error(`Validação de projeto falhou: ${validation.reason}`)
}
```

### R3: Re-ler a cada 30min

```javascript
// Verificar se ainda está no projeto
const current = sandbox.detectProject()
if (current !== sandbox.currentProject) {
  log.warn('Project changed unexpectedly', {
    expected: sandbox.currentProject,
    actual: current
  })
}
```

### R5: Verificar Antes de Pronto

```javascript
// Validar contexto final
const finalValidation = sandbox.validate('complete')
if (!finalValidation.valid) {
  throw new Error(`Contexto final inválido: ${finalValidation.reason}`)
}
```

---

## 🔧 Comandos

| Comando | Descrição |
|---------|-----------|
| `sandbox status` | Status atual do sandbox |
| `sandbox list` | Lista projetos configurados |
| `sandbox switch nome` | Trocar para projeto |
| `sandbox validate` | Validar projeto atual |
| `sandbox ssh-check` | Verificar SSH key |
| `sandbox pwd` | Ver PWD esperado vs atual |

---

## 📝 Exemplo de Output

```
$ kothar sandbox status

┌─────────────────────────────────────────────────────────────┐
│ PROJECT SANDBOX                                             │
├─────────────────────────────────────────────────────────────┤
│ Current:     📁 disparo-em-massa                          │
│ Name:        Disparo em Massa                             │
│ PWD:         /home/bruno/disparo-em-massa ✅              │
│ SSH Key:     ~/.ssh/id_ed25519_disparo ✅                 │
│ Uptime:      45m 23s                                      │
│                                                              │
│ Skills ativas:                                              │
│ ✅ frontend-ugarit                                         │
│ ✅ bug-analyst                                              │
│ ✅ security                                                 │
│ ✅ mercadopago-mcp                                         │
│ ✅ ga4                                                     │
│                                                              │
│ PREVIOUS: kothar                                           │
└─────────────────────────────────────────────────────────────┘

$ kothar sandbox validate

┌─────────────────────────────────────────────────────────────┐
│ VALIDATION                                                  │
├─────────────────────────────────────────────────────────────┤
│ PWD:         ✅ Dentro do projeto                          │
│ SSH Key:     ✅ Encontrada                                 │
│ Memory:      ✅ Diretório existe                           │
│                                                              │
│ Status:      🟢 SANDBOX OK                                │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ DoD (Definition of Done)

- [ ] PWD é validado antes de cada comando
- [ ] SSH key corresponde ao projeto
- [ ] Memórias do projeto X não vazam para projeto Y
- [ ] Context switch pede confirmação
- [ ] Skills são filtradas por projeto
- [ ] Validação funciona em R1, R2, R3, R5

---

## 🔗 Integração

| Componente | Como usa project-sandbox |
|------------|------------------------|
| hooks-system | Validação em hooks |
| command-allowlist | PWD por projeto |
| ssh-validator | Validação SSH |
| memory-search | Filtro por projeto |

---

*Skill criada em 2026-06-18 por Kothar v1.3.0*
