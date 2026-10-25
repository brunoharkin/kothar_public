"""
=============================================================
 KOTHAR v4.0 — Ferramentas MCP para Google Workspace (Gmail & Calendar)
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import json
from typing import Optional
from backend.servicos.comunicacao_google.gerenciador_email import (
    obter_estatisticas_caixa,
    resumir_mensagens_recentes,
    inspecionar_mensagem,
    mover_para_lixeira_em_lote,
    bloquear_e_descartar_remetente
)
from backend.servicos.comunicacao_google.gerenciador_agenda import listar_proximos_eventos

async def gmail_resumo_caixa(limite: int = 10, apenas_nao_lidos: bool = True) -> str:
    """
    Obtém um resumo compacto e executivo da Caixa de Entrada do Gmail.
    Retorna estatísticas da caixa (Inbox, Spam, Lixeira) e a lista dos últimos e-mails
    com Remetente, Assunto, Data e ID para tomada de decisão no chat.
    
    Args:
        limite: Quantidade máxima de e-mails para listar (padrão 10).
        apenas_nao_lidos: Se True, busca apenas mensagens não lidas.
    """
    try:
        stats = obter_estatisticas_caixa()
        mensagens = resumir_mensagens_recentes(limite=limite, apenas_nao_lidos=apenas_nao_lidos)
        
        linhas = [
            f"📊 ESTADO DA CAIXA POSTAL ({stats.get('conta', '')}):",
            f"• Inbox Total: {stats.get('inbox_total')} (Não lidos: {stats.get('inbox_nao_lidos')})",
            f"• Spam: {stats.get('spam_total')} | Lixeira: {stats.get('trash_total')}\n"
        ]
        
        if not mensagens:
            linhas.append("✅ Nenhuma mensagem pendente no momento (Inbox Zero).")
            return "\n".join(linhas)
            
        linhas.append(f"📬 ÚLTIMOS {len(mensagens)} E-MAILS:")
        for idx, m in enumerate(mensagens, 1):
            status = "[NÃO LIDO]" if m.get("nao_lido") else "[LIDO]"
            linhas.append(
                f"{idx}. {status} De: {m.get('remetente')} | Data: {m.get('data')}\n"
                f"   Assunto: {m.get('assunto')}\n"
                f"   Trecho: \"{m.get('trecho')}\"\n"
                f"   ID: {m.get('id')}\n"
            )
            
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar Gmail: {str(e)}"

async def gmail_inspecionar_email(mensagem_id: str) -> str:
    """
    Inspeciona detalhadamente um e-mail específico pelo ID com corpo sanitizado.
    
    Args:
        mensagem_id: O ID da mensagem retornado no resumo da caixa.
    """
    try:
        dados = inspecionar_mensagem(mensagem_id.strip())
        if "erro" in dados:
            return f"❌ {dados['erro']}"
            
        return (
            f"📧 DETALHES DO E-MAIL:\n"
            f"• ID: {dados.get('id')}\n"
            f"• De: {dados.get('remetente')}\n"
            f"• Para: {dados.get('destinatario')}\n"
            f"• Data: {dados.get('data')}\n"
            f"• Assunto: {dados.get('assunto')}\n"
            f"• Conteúdo (Sanitizado):\n{dados.get('resumo_seguro')}\n"
        )
    except Exception as e:
        return f"❌ Erro ao inspecionar e-mail: {str(e)}"

async def gmail_descartar_mensagens(mensagem_ids: str) -> str:
    """
    Move um ou mais e-mails para a Lixeira do Gmail (Soft Delete com retenção de 30 dias).
    
    Args:
        mensagem_ids: ID individual ou lista de IDs separados por vírgula.
    """
    try:
        lista_ids = [i.strip() for i in mensagem_ids.split(",") if i.strip()]
        if not lista_ids:
            return "⚠️ Nenhum ID de mensagem fornecido para descarte."
            
        sucessos = mover_para_lixeira_em_lote(lista_ids)
        return f"✅ {sucessos} de {len(lista_ids)} mensagem(ns) movida(s) com sucesso para a Lixeira (TRASH)."
    except Exception as e:
        return f"❌ Erro ao descartar mensagens: {str(e)}"

async def gmail_bloquear_descartar_remetente(remetente: str) -> str:
    """
    Localiza todas as mensagens recebidas de um remetente indesejado,
    move todas para a Lixeira e cataloga o remetente na lista negra local do Kothar.
    
    Args:
        remetente: Endereço de e-mail ou domínio do remetente a descartar e bloquear.
    """
    try:
        res = bloquear_e_descartar_remetente(remetente.strip())
        return (
            f"🛡️ REMETENTE BLOQUEADO:\n"
            f"• Remetente: {res.get('remetente')}\n"
            f"• Mensagens descartadas para Lixeira: {res.get('mensagens_descartadas')}\n"
            f"• Status: Catalogado na lista negra do Kothar."
        )
    except Exception as e:
        return f"❌ Erro ao bloquear remetente: {str(e)}"

async def google_agenda_eventos_dia(dias_a_frente: int = 1) -> str:
    """
    Consulta os próximos compromissos e reuniões no Google Calendar.
    
    Args:
        dias_a_frente: Quantidade de dias a frente para consultar (padrão: 1 dia).
    """
    try:
        dados = listar_proximos_eventos(dias_a_frente=dias_a_frente)
        if "erro" in dados:
            return f"❌ {dados['erro']}"
            
        eventos = dados.get("eventos", [])
        if not eventos:
            return f"📅 Nenhum compromisso agendado para os próximos {dias_a_frente} dia(s)."
            
        linhas = [f"📅 COMPROMISSOS AGENDADOS (Próximos {dias_a_frente} dia(s)):"]
        for idx, ev in enumerate(eventos, 1):
            linhas.append(
                f"{idx}. {ev.get('titulo')}\n"
                f"   Início: {ev.get('inicio')} | Fim: {ev.get('fim')}\n"
                f"   Local: {ev.get('local') or 'Não especificado'}\n"
            )
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao consultar Google Calendar: {str(e)}"

async def gmail_higienizar_propagandas(limite: int = 30, apenas_simular: bool = False) -> str:
    """
    Higieniza a Caixa de Entrada: identifica e descarta automaticamente propagandas,
    newsletters e e-mails de vendas frias para a Lixeira, preservando exclusivamente
    e-mails de clientes reais e mensagens legítimas.
    
    Args:
        limite: Quantidade máxima de e-mails para analisar (padrão 30).
        apenas_simular: Se True, apenas lista o que seria descartado sem mover para o lixo.
    """
    try:
        from backend.servicos.comunicacao_google.classificador_email import varrer_e_filtrar_inbox
        res = varrer_e_filtrar_inbox(limite_mensagens=limite, aplicar_descarte=not apenas_simular)
        
        if "erro" in res:
            return f"❌ {res['erro']}"
            
        total = res.get("total_analisado", 0)
        if total == 0:
            return "✅ Caixa de Entrada já está vazia (Inbox Zero). Nenhuma propaganda detectada."
            
        acao = "Simuladas" if apenas_simular else "Descartadas para Lixeira"
        linhas = [
            "🛡️ RESULTADO DA HIGIENIZAÇÃO INTELIGENTE:",
            f"• Total Analisado: {total} mensagens",
            f"• Propagandas {acao}: {res.get('total_propagandas', 0)}",
            f"• E-mails de Clientes/Legítimos Preservados: {res.get('clientes_preservados', 0)}\n"
        ]
        
        clientes = res.get("lista_clientes", [])
        if clientes:
            linhas.append(f"📬 E-MAILS DE CLIENTES / IMPORTANTES MANTIDOS NO INBOX ({len(clientes)}):")
            for idx, c in enumerate(clientes, 1):
                linhas.append(f"  {idx}. De: {c['remetente']} | Assunto: {c['assunto']}")
        else:
            linhas.append("ℹ️ Nenhum e-mail de cliente pendente na Caixa de Entrada no momento.")
            
        return "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao higienizar propagandas: {str(e)}"


