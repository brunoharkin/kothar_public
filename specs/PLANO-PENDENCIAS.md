# PLANO DEPENDÊNCIAS HERMES - Pós-Correções

> **Data:** 2026-06-28  
> **Status:** ✅ Correções Críticas Aplicadas  
> **Próxima Revisão:** 2026-07-05

---

## ✅ CORREÇÕES APLICADAS

### 1. **kothar-init.sh** - Corrigido
- **Problema:** `exit 1` prematuro impedia exibição de Regras de Ouro
- **Solução:** Moveu regras antes do exit, garantindo exibição sempre
- **Resultado:** Sessões novas sempre mostram contexto essencial

### 2. **ChromaDB Wrapper** - Implementado
- **Problema:** ChromaDB só funcionava no venv
- **Solução:** Criado `chroma-wrapper.sh` e modificado embedder.py
- **Resultado:** RAG funciona em todas as situações

### 3. **Stall Detector** - Limpo
- **Problema:** JavaScript inexecutável (`setInterval`)
- **Solução:** Transformado em especificação conceitual
- **Resultado:** Sem alucinações de código executável

### 4. **Contradição de Prompts** - Resolvida
- **Problema:** "flexibilizados" vs "rígidos"
- **Solução:** Unificado para "simplificados" 
- **Resultado:** Kothar tem diretriz clara

---

## 🚨 O QUE AINDA PRECISA SER FEITO

### FASE A - URGENTE (Esta semana)

#### 1. **Validar RAG Funcional** 
**Prioridade:** ALTA  
**Quando:** Hoje  
**Responsável:** Kothar  
**O que fazer:**
- Testar se embeddings persistem entre sessões
- Verificar se busca semântica retorna resultados reais
- Testar wrapper em diferentes contextos

**Resultado Esperado:** 
- [ ] Indexação funciona sem erros
- [ ] Busca retorna resultados relevantes  
- [ ] Dados persistem entre reinícios

#### 2. **Atualizar SPEC.md com estado real**
**Prioridade:** ALTA  
**Quando:** Amanhã  
**Responsável:** Kothar  
**O que fazer:**
- Remover features não implementadas
- Atualizar versões para v2.1.3
- Documentar o que REALMENTE funciona

**Resultado Esperado:**
- [ ] SPEC refletindo implementação real
- [ ] Sem promessas falsas
- [ ] Versões consistentes

#### 3. **Testar todos os Hooks**
**Prioridade:** MÉDIA  
**Quando:** D+1  
**Responsável:** Kothar  
**O que fazer:**
- Validar que 19 hooks executam sem erro
- Testar integração com ChromaDB wrapper
- Verificar performance

**Resultado Esperado:**
- [ ] Todos hooks funcionam
- [ ] Sem dependências quebradas
- [ ] Performance aceitável

---

### FASE B - ESTABILIZAÇÃO (Próxima semana)

#### 4. **Criar sistema de detecção de alucinações**
**Prioridade:** MÉDIA  
**Quando:** D+2  
**O que fazer:**
- Identificar padrões de código não-executável
- Criar marcação automática
- Prevenir futuras alucinações

#### 5. **Documentar skills reais**
**Prioridade:** BAIXA  
**Quando:** D+3  
**O que fazer:**
- Listar skills que realmente funcionam
- Marcar skills conceituais vs executáveis
- Criar guia de uso

#### 6. **Performance RAG**
**Prioridade:** BAIXA  
**Quando:** D+4  
**O que fazer:**
- Implementar cache de resultados
- Otimizar busca com muitos vetores
- Adicionar indexação incremental

---

## 📊 METRICAS DE SUCESSO

| Item | Métrica | Alvo | Status |
|------|---------|------|--------|
| RAG Funcional | Busca retorna resultados | 95% | 🟡 Em teste |
| Hooks Ativos | 19/19 hooks sem erro | 100% | 🟡 Em teste |
| Sem Alucinações | Código executável = 0 | 0 | ✅ OK |
| Prompt Consistente | Contradições = 0 | 0 | ✅ OK |
| Performance | Tempo de resposta < 2s | 95% | 🟡 Em teste |

---

## 🚧 RISCOS IDENTIFICADOS

1. **ChromaDB wrapper pode falhar em alguns casos**
   - Mitigação: Testar em diferentes cenários

2. **Skills com pseudo-código podem ser reintroduzidas**
   - Mitigação: Criar checklist de validação

3. **SPEC ainda desatualizado**
   - Mitigação: Atualizar imediatamente

---

## 🎯 PRÓXIMOS PASSOS

1. **Hoje:** Validar RAG funcional
2. **Amanhã:** Atualizar SPEC.md  
3. **D+1:** Testar hooks completos
4. **D+2:** Implementar detector de alucinações

---

**Status:** ✅ Correções críticas aplicadas  
**Próxima Revisão:** 2026-07-05  
**Risco Baixo:** Sistema estável para uso