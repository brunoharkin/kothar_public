#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Pesquisa de Mercado & SEO com AIsa
 Ugarit Digital | Bruno Harkin
=============================================================
Consome a API da AIsa para mapear volumes reais de busca,
dificuldade de ranqueamento (KD), intenção de busca e
concorrentes para os nichos prioritários da Ugarit:
- Advocacia (Atendimento Jurídico)
- Clínicas de Estética / Saúde
- Softhouse / Agentes de IA B2B
=============================================================
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Carregar .env manualmente para não depender de pacotes externos
def carregar_env(caminho_env: Path) -> dict:
    vars_env = {}
    if not caminho_env.exists():
        return vars_env
    with open(caminho_env, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if "=" in linha:
                chave, valor = linha.split("=", 1)
                vars_env[chave.strip()] = valor.strip().strip('"').strip("'")
    return vars_env


KOTHAR_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = KOTHAR_DIR / ".env"
env_vars = carregar_env(ENV_FILE)

AISA_API_KEY = os.environ.get("AISA_API_KEY") or env_vars.get("AISA_API_KEY")
AISA_BASE_URL = os.environ.get("AISA_BASE_URL") or env_vars.get("AISA_BASE_URL", "https://api.aisa.one")

if not AISA_API_KEY:
    print("❌ Erro: AISA_API_KEY não encontrada no .env nem nas variáveis de ambiente.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {AISA_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Kothar-Ugarit/4.0"
}

# Termos Semente por Cohort Estratégico
TERMOS_SEMENTE = {
    "Advocacia": [
        "automacao whatsapp escritorio advocacia",
        "agente de ia para advogados",
        "atendimento automatico advocacia",
        "triagem de clientes advocacia whatsapp",
        "software juridico com inteligencia artificial",
    ],
    "Clinicas_Estetica": [
        "agendamento automatico whatsapp clinica estetica",
        "chatbot inteligencia artificial clinica",
        "confirmacao de consulta automatica whatsapp",
        "automacao de atendimento clinica medica",
        "ia para clinica estetica",
    ],
    "Softhouse_IA_Geral": [
        "agente de ia para empresas",
        "desenvolvimento de agentes de inteligencia artificial",
        "softhouse inteligencia artificial brasil",
        "automacao de vendas whatsapp ia",
        "qualificacao de leads com ia",
    ]
}


def requisicao_aisa(endpoint: str, payload: dict = None, metodo: str = "POST") -> dict:
    """Faz requisição para AIsa e trata erros e quotas."""
    url = f"{AISA_BASE_URL.rstrip('/')}{endpoint}"
    data_bytes = json.dumps(payload).encode("utf-8") if payload else None
    
    req = urllib.request.Request(url, data=data_bytes, headers=HEADERS, method=metodo)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = resp.read().decode("utf-8")
            return json.loads(corpo)
    except urllib.error.HTTPError as e:
        erro_body = e.read().decode("utf-8", errors="ignore")
        return {
            "erro": True,
            "status_code": e.code,
            "detalhes": erro_body or str(e)
        }
    except Exception as e:
        return {
            "erro": True,
            "status_code": 500,
            "detalhes": str(e)
        }


def pesquisar_inteligencia_concorrencia():
    """Usa o gateway de LLM / Perplexity via AIsa para sintetizar panorama de concorrentes reais no Brasil."""
    print("🔍 Consultando inteligência de concorrência e posicionamento via AIsa Gateway...")
    
    prompt = """Você é o consultor de inteligência de mercado do Kothar (Ugarit Digital).
Analise o mercado brasileiro atual (2026) de agências/softhouses que vendem agentes de IA e automação de atendimento via WhatsApp para negócios locais (advocacia, clínicas de estética) e negócios online.

Forneça um relatório objetivo com:
1. Os 3 a 5 principais players / plataformas concorrentes que atuam no Brasil nesse segmento (ex: Z-API, Zenvia, Blip, micro-agências de agentes de IA, etc).
2. O que eles oferecem de fato e qual é o 'gap' (fraqueza) que a Ugarit Digital pode explorar (ex: falta de supervisão humana, cobrança excessiva por mensagem, falta de CRM e teleprompter integrados).
3. As 10 palavras-chave com maior valor transacional que empresários brasileiros usam quando procuram resolver a dor de atendimento e perda de leads no WhatsApp.
4. Estimativa de intenção de busca (Comercial, Transacional, Informativa) e formato de página recomendado (Landing Page nichada vs Artigo vs VSL).

Responda em formato estruturado markdown, estritamente em português do Brasil."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Você é um analista sênior de inteligência competitiva e SEO técnico."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    # Rota padrão compatível com OpenAI da AIsa
    res = requisicao_aisa("/v1/chat/completions", payload, metodo="POST")
    return res


def tentar_dataforseo_volume(termos: list):
    """Consulta endpoints de busca DataForSEO disponíveis na AIsa."""
    print(f"📊 Consultando volume e métricas de busca para {len(termos)} termos...")
    
    # Endpoint do catálogo AIsa para DataForSEO Labs Google Keyword Ideas
    payload = [{
        "keywords": termos,
        "location_code": 2076,  # Brasil
        "language_code": "pt",
        "limit": 10
    }]
    
    endpoint = "/apis/v1/dataforseo/dataforseo_labs/google/keyword_ideas/live"
    res = requisicao_aisa(endpoint, payload, metodo="POST")
    return res


def main():
    print("=" * 60)
    print("🎵 KOTHAR v4.0 — PESQUISA DE MERCADO & CONCORRÊNCIA (AIsa)")
    print("=" * 60)
    print(f"Chave AIsa configurada: {AISA_API_KEY[:8]}...{AISA_API_KEY[-4:]}")
    print(f"Gateway Base URL: {AISA_BASE_URL}\n")
    
    relatorio_final = []
    relatorio_final.append("# Relatório Executivo de Mercado, Concorrência e Palavras-Chave")
    relatorio_final.append("**Fonte:** AIsa Intelligence Gateway | **Data:** Outubro/2026\n")
    
    # 1. Inteligência de Mercado & Concorrentes
    analise = pesquisar_inteligencia_concorrencia()
    
    if analise.get("erro"):
        print(f"⚠️ Aviso na consulta de inteligência: {analise.get('status_code')} - {analise.get('detalhes')}")
        # Tentar fallback com modelo claude ou outro endpoint se gpt-4o-mini retornar restrição
        payload_fallback = {
            "model": "claude-3-5-haiku-20241022",
            "messages": [
                {"role": "user", "content": "Mapeie os 5 maiores concorrentes de automação de WhatsApp com IA no Brasil e as melhores palavras-chave para vender agentes de IA para clínicas e advocacia."}
            ]
        }
        res_fb = requisicao_aisa("/v1/chat/completions", payload_fallback, metodo="POST")
        if not res_fb.get("erro"):
            conteudo = res_fb["choices"][0]["message"]["content"]
            relatorio_final.append(conteudo)
        else:
            relatorio_final.append(f"Erro na consulta de LLM Gateway: {analise.get('detalhes')}")
    else:
        conteudo = analise["choices"][0]["message"]["content"]
        relatorio_final.append(conteudo)
        print("✅ Análise de inteligência de concorrência concluída com sucesso.")
        
    # 2. Consultar DataForSEO para múltiplos cohorts
    print("\nConsultando DataForSEO para Advocacia, Clínicas de Estética e Automação B2B...")
    
    cohorts_busca = {
        "Advocacia": [
            "advogados online agora",
            "atendimento whatsapp advocacia",
            "consulta com advogado online"
        ],
        "Clinicas_Estetica": [
            "clinica de estetica whatsapp",
            "agendamento consulta estetica",
            "botox agendamento online",
            "clinica estetica atendimento automatico"
        ],
        "Automacao_B2B_IA": [
            "automacao whatsapp empresas",
            "agente de ia para empresas",
            "chatbot para vendas whatsapp"
        ]
    }
    
    relatorio_final.append("\n---\n## Dados Técnicos de Volume & SERP (Google Brasil via DataForSEO / AIsa)")
    
    for nome_cohort, termos in cohorts_busca.items():
        print(f"📊 Consultando {nome_cohort} ({len(termos)} termos)...")
        dados_seo = tentar_dataforseo_volume(termos)
        
        relatorio_final.append(f"\n### Cohort: {nome_cohort.replace('_', ' ')}")
        
        if dados_seo.get("erro"):
            relatorio_final.append(f"*Erro no endpoint*: {dados_seo.get('detalhes')}")
            continue
            
        try:
            tasks = dados_seo.get("tasks", [])
            if tasks and "result" in tasks[0] and tasks[0]["result"]:
                res_data = tasks[0]["result"][0]
                total_encontrado = res_data.get("total_count", 0)
                items = res_data.get("items", [])
                
                relatorio_final.append(f"Total de oportunidades mapeadas: **{total_encontrado}**\n")
                relatorio_final.append("| Palavra-Chave | Volume Mensal | Dificuldade (KD) | CPC Médio (USD) | Concorrência | Intenção |")
                relatorio_final.append("|---|---|---|---|---|---|")
                
                for item in items[:15]:
                    kw = item.get("keyword", "-")
                    kw_info = item.get("keyword_info", {})
                    kw_prop = item.get("keyword_properties", {})
                    search_vol = kw_info.get("search_volume") or "-"
                    cpc = kw_info.get("cpc") or "-"
                    comp = kw_info.get("competition_level") or "-"
                    kd = kw_prop.get("keyword_difficulty") or "-"
                    intent = item.get("search_intent_info", {}).get("main_intent") or "Comercial"
                    
                    relatorio_final.append(f"| **{kw}** | {search_vol} | {kd} | ${cpc} | {comp} | {intent} |")
            else:
                relatorio_final.append("*Nenhum dado retornado para este lote.*")
        except Exception as e:
            relatorio_final.append(f"*Erro de formatação*: {e}")
    if dados_seo.get("erro"):
        relatorio_final.append(f"\n*Nota Técnica*: Endpoint DataForSEO retornou status {dados_seo.get('status_code')}: `{dados_seo.get('detalhes')}`")
    else:
        try:
            tasks = dados_seo.get("tasks", [])
            if tasks and "result" in tasks[0] and tasks[0]["result"]:
                res_data = tasks[0]["result"][0]
                total_encontrado = res_data.get("total_count", 0)
                items = res_data.get("items", [])
                
                relatorio_final.append(f"\n### Total de Palavras-Chave Identificadas no Google Brasil: **{total_encontrado}**\n")
                relatorio_final.append("| Palavra-Chave | Volume de Busca | Dificuldade (KD) | CPC (USD) | Concorrência | Intenção |")
                relatorio_final.append("|---|---|---|---|---|---|")
                
                for item in items:
                    kw = item.get("keyword", "-")
                    kw_info = item.get("keyword_info", {})
                    kw_prop = item.get("keyword_properties", {})
                    search_vol = kw_info.get("search_volume") or "-"
                    cpc = kw_info.get("cpc") or "-"
                    comp = kw_info.get("competition_level") or "-"
                    kd = kw_prop.get("keyword_difficulty") or "-"
                    intent = item.get("search_intent_info", {}).get("main_intent") or "Comercial"
                    
                    relatorio_final.append(f"| **{kw}** | {search_vol} | {kd} | ${cpc} | {comp} | {intent} |")
            else:
                relatorio_final.append("\n```json\n" + json.dumps(dados_seo, indent=2, ensure_ascii=False)[:2000] + "\n```")
        except Exception as e:
            relatorio_final.append(f"\nErro ao formatar itens: {e}\n```json\n" + json.dumps(dados_seo, indent=2, ensure_ascii=False)[:2000] + "\n```")

    # Salvar relatório gerado
    docs_dir = KOTHAR_DIR / "docs"
    docs_dir.mkdir(exist_ok=True)
    arquivo_saida = docs_dir / "pesquisa-mercado-concorrentes-aisa.md"
    
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(relatorio_final))
        
    print(f"\n📄 Relatório salvo com sucesso em: {arquivo_saida}")
    print("=" * 60)


if __name__ == "__main__":
    main()
