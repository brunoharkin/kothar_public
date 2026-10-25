"""
=============================================================
 KOTHAR v4.0 — Testes Unitários: Classificador Anti-Propaganda
 Ugarit Digital — Bruno Harkin
=============================================================
"""

import pytest
from backend.servicos.comunicacao_google.classificador_email import (
    avaliar_se_e_propaganda
)

def test_github_ci_notification_preserved():
    """Garante que alertas de CI/CD do GitHub nunca sejam descartados."""
    remetente = "brunoharkin <notifications@github.com>"
    assunto = "[brunoharkin/Sophia] Run failed: Run Linux nightly installer - main (d81e57b)"
    snippet = "[brunoharkin/Sophia] Run Linux nightly installer workflow run: All jobs have failed"
    headers = {
        "precedence": "bulk",
        "list-id": "<Sophia.brunoharkin.github.com>",
        "list-unsubscribe": "<mailto:unsub@github.com>"
    }
    
    eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, headers)
    assert eh_promo is False
    assert "whitelist_dev_infra" in motivo or "transacional_ou_dev_critico" in motivo

def test_infra_and_dev_services_preserved():
    """Garante que Docker, GitLab, AWS e Stripe sejam preservados mesmo com precedence bulk."""
    servicos = [
        ("GitLab Notifications <notify@gitlab.com>", "Pipeline #12345 passed for main", {"precedence": "bulk"}),
        ("Docker Hub <noreply@docker.com>", "New automated build for repo", {"precedence": "bulk"}),
        ("Amazon Web Services <no-reply-aws@amazon.com>", "AWS Budget Notification: Actual spend exceeded", {"precedence": "bulk"}),
        ("Stripe Notifications <notifications@stripe.com>", "Payment confirmed: Invoice #9871", {"precedence": "bulk"})
    ]
    
    for rem, sub, hdrs in servicos:
        eh_promo, motivo = avaliar_se_e_propaganda(rem, sub, "Detalhes operacionais", hdrs)
        assert eh_promo is False, f"Falha ao preservar {rem}: {motivo}"

def test_security_and_transactional_alerts_preserved():
    """Garante que 2FA, recuperação de senha e notas fiscais sejam preservados."""
    remetente = "Segurança Google <no-reply@accounts.google.com>"
    assunto = "Alerta de segurança: Seu código de verificação é 849201"
    snippet = "Use o código de verificação 849201 para concluir o acesso."
    headers = {"precedence": "bulk"}
    
    eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, headers)
    assert eh_promo is False
    assert "whitelist_dev_infra" in motivo or "transacional_ou_dev_critico" in motivo

def test_ad_alison_courses_discarded():
    """Garante que e-mails de cursos e vendas frias sejam classificados como propaganda."""
    remetente = "Alison Courses <noreply@us-education.alison.com>"
    assunto = "Bruno, looking for “AI-proof” jobs? 👀"
    snippet = "Upskill in human-centred skills. View in web browser. Unsubscribe."
    headers = {
        "list-unsubscribe": "<https://alison.com/unsubscribe>",
        "precedence": "bulk"
    }
    
    eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, headers)
    assert eh_promo is True

def test_ad_pinterest_discarded():
    """Garante que recomendações de redes sociais sejam classificadas como propaganda."""
    remetente = "Pinterest <pinterest-recommendations@ideas.pinterest.com>"
    assunto = "Fotografia Masculina para Bruno"
    snippet = "Novas ideias e fotos sugeridas para você. Clique para ver mais."
    headers = {
        "list-unsubscribe": "<https://pinterest.com/unsubscribe>",
        "precedence": "bulk"
    }
    
    eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, headers)
    assert eh_promo is True

def test_legitimate_client_email_preserved():
    """Garante que e-mails legítimos de clientes ou pessoas físicas sejam mantidos no Inbox."""
    remetente = "Carlos Silva <carlos.silva@empresaexemplo.com.br>"
    assunto = "Proposta comercial para integração Kothar v4"
    snippet = "Olá Bruno, gostaríamos de agendar uma reunião técnica para discutir os prazos do projeto."
    headers = {}
    
    eh_promo, motivo = avaliar_se_e_propaganda(remetente, assunto, snippet, headers)
    assert eh_promo is False
    assert motivo == "cliente_ou_legitimo"

