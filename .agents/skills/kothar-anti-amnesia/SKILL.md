---
name: kothar-anti-amnesia
description: >-
  Prevenção de Amnésia e Leitura Rasa (AST / Graph Dependency Tracking). Impede deleção de funções internas acidentalmente durante refatorações. Sincroniza nomes entre frontend, backend e DB.
---

# Skill: Prevenção de Amnésia e Leitura Rasa (AST & Dependências)

> **Regra de Ouro:** NUNCA substitua um arquivo ou bloco de código sem antes MAPEÁ-LO COMPLETAMENTE (usando Graph/Neo4j se disponível, ou leitura profunda de árvore de dependências). 

## 1. O Problema da "Leitura Rasa"
- ❌ Ler o código por cima e substituir um bloco esquecendo funções internas.
- ❌ Alterar o nome de uma variável/função no Backend e esquecer de mudar no Frontend e DB.
- ❌ Apagar lógicas de fora e quebrar projetos inteiros (ex: Orby).

## 2. Protocolo de Substituição de Código (A REGRA AST)

Antes de modificar ou reescrever qualquer bloco de código:
1. **Mapeamento de Dependências (Graph):** Rastrei todas as ligações da função. Onde ela é chamada? Quem ela chama?
2. **Listagem de Funções Internas:** Escreva as funções que existem dentro do bloco que será substituído.
3. **Uso Exclusivo de Replace Cirúrgico:** Use ferramentas cirúrgicas de `replace_file_content` (por linha de início e fim). **É PROIBIDO** tentar substituir o arquivo inteiro de uma vez ou usar blocos gigantes que perdem o escopo.
4. **Alinhamento Trinodal (Sincronia):** Se você renomear ou recriar qualquer elemento, você é **obrigado** a abrir simultaneamente:
   - O arquivo do Frontend (Componente / Página)
   - O arquivo do Backend (Rota / Controller / API)
   - O Schema do Banco de Dados (DB)
   E garantir que a exata mesma nomenclatura foi usada em todos.

## 3. Workflow de Prevenção:
```
1. AUDITORIA PROFUNDA: Use `grep` e buscas textuais para encontrar TODOS os lugares onde o nome antigo aparece antes de deletar ou alterar.
2. EXTRAÇÃO: Liste as funções que estão dentro do bloco.
3. MODIFICAÇÃO CIRÚRGICA: Altere apenas o que foi pedido.
4. RE-INSERÇÃO: Garanta que todas as funções mapeadas na Extração continuam existindo no arquivo após a edição.
```
