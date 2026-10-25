"""
=============================================================
 KOTHAR v4.0 — Classificador e Filtro Anti-Propaganda (Gmail)
 Ugarit Digital — Bruno Harkin
=============================================================
 Filtro em Camadas:
 1. Heurística RFC de Marketing (List-Unsubscribe, Precedence: bulk)
 2. Padrões de Remetente Comercial (noreply, marketing, ofertas, news)
 3. Detecção de Copy Promocional e Descadastramento no Snippet
 4. Proteção Absoluta de Clientes (Whitelist e Dúvida Pró-Cliente)
=============================================================
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
import requests

from backend.servicos.comunicacao_google.gerenciador_email import (
    obter_access_token,
    mover_para_lixeira_em_lote,
    ARQUIVO_REMETENTES_BLOQUEADOS
)

# 1. Whitelist Absoluta de Infraestrutura, Dev & Repositórios (Prioridade Zero)
PADROES_WHITELIST_DEV_INFRA = [
    r"@(?:[a-zA-Z0-9-]+\.)?github\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?gitlab\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?bitbucket\.org",
    r"@(?:[a-zA-Z0-9-]+\.)?docker\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?amazon(?:aws)?\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?google\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?accounts\.google\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?vercel\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?cloudflare\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?digitalocean\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?supabase\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?stripe\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?railway\.app"
]

# 2. Padrões Transacionais e Alertas Críticos de Sistema / CI / Segurança
PADROES_TRANSACIONAIS_CRITICOS = [
    r"\[.+\]\s*(?:run (?:failed|succeeded|cancelled)|workflow|pull request|merge request|job|pipeline|issue)",
    r"(?:run failed|run succeeded|workflow run|pull request|merge request|build failed|build succeeded)",
    r"(?:alerta de seguran[cç]a|security alert|novo login|new sign-in|c[oó]digo de (?:verifica[cç][aã]o|confirma[cç][aã]o|seguran[cç]a))",
    r"(?:verification code|security code|redefini[cç][aã]o de senha|reset your password|password reset)",
    r"(?:fatura|recibo de pagamento|comprovante de pagamento|nota fiscal|invoice|payment receipt|billing receipt)"
]

# 3. Remetentes e domínios com padrões explícitos de propaganda/disparo automático
PADROES_REMETENTE_PROPAGANDA = [
    r"no[-_]?reply",
    r"newsletter",
    r"marketing",
    r"promoc(ao|oes|ional)",
    r"ofertas?",
    r"descontos?",
    r"news@",
    r"comercial@",
    r"noticias@",
    r"bounce",
    r"campaign",
    r"mailchimp",
    r"sendgrid",
    r"hubspot",
    r"rdstation",
    r"intercom",
    r"@(?:[a-zA-Z0-9-]+\.)?alison\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?pinterest\.com",
    r"@(?:[a-zA-Z0-9-]+\.)?ideas\.pinterest\.com"
]

# 4. Expressões que comprovam e-mail comercial em massa
PADROES_SNIPPET_PROPAGANDA = [
    r"descadastre[- ]se",
    r"cancelar\s+inscri[cç][aã]o",
    r"unsubscribe",
    r"opt[- ]out",
    r"n[aã]o\s+deseja\s+mais\s+receber",
    r"clique\s+aqui\s+para\s+deixar\s+de\s+receber",
    r"pol[ií]tica\s+de\s+privacidade\s*\|\s*termos",
    r"oferta\s+v[aá]lida\s+at[eé]",
    r"cupom\s+de\s+desconto",
    r"compre\s+agora",
    r"aproveite\s+o\s+desconto",
    r"promo[cç][aã]o\s+exclusiva",
    r"frete\s+gr[aá]tis",
    r"black\s*friday",
    r"gostaria\s+de\s+apresentar\s+nossa\s+solu[cç][aã]o",
    r"tem\s+15\s+minutos\s+para\s+uma\s+call"
]

def obter_lista_remetentes_bloqueados() -> List[str]:
    """Retorna a lista de remetentes explicitamente bloqueados pelo usuário."""
    if ARQUIVO_REMETENTES_BLOQUEADOS.exists():
        try:
            with open(ARQUIVO_REMETENTES_BLOQUEADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def avaliar_se_e_propaganda(
    remetente: str,
    assunto: str,
    snippet: str,
    headers_dict: Dict[str, str]
) -> Tuple[bool, str]:
    """
    Avalia deterministicamente se a mensagem é propaganda/marketing/vendas.
    Prioridades:
    0. Lista negra de remetentes bloqueados -> Descarte.
    1. Whitelist de Dev / Infra (GitHub, GitLab, Docker, AWS, etc.) -> Preservar SEMPRE.
    2. Padrões transacionais / alertas de CI / faturas -> Preservar SEMPRE.
    3. Remetentes de propaganda conhecidos -> Descarte.
    4. Snippet / Assunto com copy promocional -> Descarte.
    5. Headers RFC de marketing (List-Unsubscribe, Precedence: bulk) -> Descarte.
    6. Dúvida -> Preservar (pró-cliente / pró-humano).
    """
    remetente_lower = remetente.lower()
    assunto_lower = assunto.lower()
    snippet_lower = snippet.lower()
    
    # Camada 0: Lista negra local (bloqueados explicitamente)
    for bloqueado in obter_lista_remetentes_bloqueados():
        if bloqueado.lower() in remetente_lower:
            return True, f"remetente_bloqueado_lista_negra ({bloqueado})"
            
    # Camada 1: Whitelist absoluta de Dev / Infraestrutura (GitHub, GitLab, AWS, etc.)
    for padrao_dev in PADROES_WHITELIST_DEV_INFRA:
        if re.search(padrao_dev, remetente_lower):
            return False, f"whitelist_dev_infra ({padrao_dev})"
            
    # Camada 2: Padrões transacionais, CI/CD e segurança no Assunto e Snippet
    for padrao_trans in PADROES_TRANSACIONAIS_CRITICOS:
        if re.search(padrao_trans, assunto_lower) or re.search(padrao_trans, snippet_lower):
            return False, f"transacional_ou_dev_critico ({padrao_trans})"
            
    # Camada 3: Padrão no Remetente comercial/anúncio
    for padrao_remetente in PADROES_REMETENTE_PROPAGANDA:
        if re.search(padrao_remetente, remetente_lower):
            return True, f"remetente_promocional ({padrao_remetente})"
            
    # Camada 4: Copy promocional no Snippet ou Assunto
    for padrao_copy in PADROES_SNIPPET_PROPAGANDA:
        if re.search(padrao_copy, snippet_lower) or re.search(padrao_copy, assunto_lower):
            return True, f"conteudo_promocional_detectado ({padrao_copy})"
            
    # Camada 5: Headers RFC de Email Marketing (List-Unsubscribe ou Precedence: bulk)
    # Apenas verificado após descartar Dev, Infra e Transacionais
    if "list-unsubscribe" in headers_dict or "list-unsubscribe-post" in headers_dict:
        return True, "header_list_unsubscribe (newsletter/disparo em massa)"
        
    if headers_dict.get("precedence", "").lower() in ["bulk", "list", "junk"]:
        return True, "header_precedence_bulk (disparo automático)"
        
    # Camada 6: Na dúvida, preserva como cliente/legítimo
    return False, "cliente_ou_legitimo"

def varrer_e_filtrar_inbox(limite_mensagens=50, aplicar_descarte=True, access_token=None):
    """
    Varre os e-mails na Caixa de Entrada.
    Identifica mensagens de propaganda/vendas e clientes reais.
    Se aplicar_descarte=True, move as propagandas para a Lixeira (Soft Delete).
    """
    token = access_token or obter_access_token()
    headers_auth = {"Authorization": f"Bearer {token}"}
    
    url_lista = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q=in:inbox&maxResults={limite_mensagens}"
    resp = requests.get(url_lista, headers=headers_auth, timeout=12)
    if resp.status_code != 200:
        return {"erro": f"Falha ao listar mensagens: {resp.status_code}"}
        
    mensagens_raw = resp.json().get("messages", [])
    if not mensagens_raw:
        return {
            "total_analisado": 0,
            "propagandas_detectadas": 0,
            "clientes_preservados": 0,
            "itens_clientes": [],
            "itens_descarte": []
        }
        
    propagandas = []
    clientes = []
    
    for m in mensagens_raw:
        mid = m["id"]
        url_detalhe = (
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}"
            f"?format=metadata"
            f"&metadataHeaders=From"
            f"&metadataHeaders=Subject"
            f"&metadataHeaders=Date"
            f"&metadataHeaders=List-Unsubscribe"
            f"&metadataHeaders=Precedence"
        )
        r = requests.get(url_detalhe, headers=headers_auth, timeout=8)
        if r.status_code != 200:
            continue
            
        dados = r.json()
        hdrs = {h["name"].lower(): h["value"] for h in dados.get("payload", {}).get("headers", [])}
        
        remetente = hdrs.get("from", "Desconhecido")
        assunto = hdrs.get("subject", "(Sem assunto)")
        data = hdrs.get("date", "")
        snippet = dados.get("snippet", "")
        
        eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, hdrs)
        
        info_msg = {
            "id": mid,
            "remetente": remetente,
            "assunto": assunto,
            "data": data,
            "snippet": snippet[:100],
            "motivo": motivo
        }
        
        if eh_promo:
            propagandas.append(info_msg)
        else:
            clientes.append(info_msg)
            
    descartados_sucesso = 0
    if aplicar_descarte and propagandas:
        ids_descarte = [p["id"] for p in propagandas]
        descartados_sucesso = mover_para_lixeira_em_lote(ids_descarte, token)
        
    return {
        "total_analisado": len(mensagens_raw),
        "propagandas_descartadas": descartados_sucesso if aplicar_descarte else 0,
        "total_propagandas": len(propagandas),
        "clientes_preservados": len(clientes),
        "lista_clientes": clientes,
        "lista_propagandas": propagandas
    }

