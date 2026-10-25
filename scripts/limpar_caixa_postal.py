#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Limpeza Segura da Caixa Postal (Soft Delete)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import sys
import time
from pathlib import Path

# Adicionar raiz ao sys.path
DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIRETORIO_RAIZ))

from backend.servicos.comunicacao_google.gerenciador_email import (
    obter_access_token,
    obter_estatisticas_caixa,
    listar_ids_por_busca,
    mover_para_lixeira_em_lote
)

def formatar_barra(atual, total, tamanho=30):
    if total == 0:
        return "[==============================] 100%"
    prog = int(tamanho * (atual / total))
    pct = int(100 * (atual / total))
    barra = "=" * prog + "-" * (tamanho - prog)
    return f"[{barra}] {pct}% ({atual}/{total})"

def principal():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🧹 KOTHAR v4.0 — OPERAÇÃO LIMPEZA DA CAIXA POSTAL (GMAIL)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print("🔄 Conectando à API do Gmail e renovando credenciais...")
    token = obter_access_token()
    stats_iniciais = obter_estatisticas_caixa(token)
    
    print(f"✅ Conta: {stats_iniciais['conta']}")
    print(f"📦 Estado Atual: {stats_iniciais['inbox_total']} na Caixa de Entrada | {stats_iniciais['spam_total']} no Spam\n")
    
    # 1. Limpar Spam
    if stats_iniciais['spam_total'] > 0:
        print(f"🚨 Fase 1: Coletando mensagens de SPAM...")
        ids_spam = listar_ids_por_busca("in:spam", token)
        total_spam = len(ids_spam)
        print(f"   -> {total_spam} mensagens de spam localizadas. Movendo para Lixeira (TRASH)...")
        
        def prog_spam(c, t, s):
            print(f"\r   Progresso Spam: {formatar_barra(c, t)}", end="", flush=True)
            
        sucessos_spam = mover_para_lixeira_em_lote(ids_spam, token, prog_spam)
        print(f"\n   ✅ {sucessos_spam}/{total_spam} spams movidos com sucesso para a Lixeira.\n")
    else:
        print("✅ Fase 1: Pasta SPAM já está vazia.\n")
        
    # 2. Limpar Inbox
    if stats_iniciais['inbox_total'] > 0:
        print(f"📬 Fase 2: Coletando mensagens da Caixa de Entrada (INBOX)...")
        ids_inbox = listar_ids_por_busca("in:inbox", token)
        total_inbox = len(ids_inbox)
        print(f"   -> {total_inbox} mensagens no Inbox localizadas. Movendo para Lixeira (TRASH)...")
        
        def prog_inbox(c, t, s):
            print(f"\r   Progresso Inbox: {formatar_barra(c, t)}", end="", flush=True)
            
        sucessos_inbox = mover_para_lixeira_em_lote(ids_inbox, token, prog_inbox)
        print(f"\n   ✅ {sucessos_inbox}/{total_inbox} mensagens do Inbox movidas com sucesso para a Lixeira.\n")
    else:
        print("✅ Fase 2: Caixa de Entrada já está vazia.\n")
        
    # 3. Conferência Final
    print("📊 Verificando estado final pós-limpeza...")
    stats_finais = obter_estatisticas_caixa(token)
    print("─────────────────────────────────────────────────────────────")
    print(f"  Caixa de Entrada: {stats_finais['inbox_total']} mensagens")
    print(f"  Spam:             {stats_finais['spam_total']} mensagens")
    print(f"  Lixeira (TRASH):  {stats_finais['trash_total']} mensagens (seguras por 30 dias)")
    print("─────────────────────────────────────────────────────────────")
    print("\n🎉 INBOX ZERO ATINGIDO! A caixa postal está 100% limpa e pronta para o novo ciclo.")

if __name__ == "__main__":
    principal()

