"""
=============================================================
 KOTHAR v6.0 — Multi-Model Router
 Usa modelos remotos (Claude, OpenAI, etc.)
 Não suporta modelos locais Ollama
=============================================================
"""
import logging
from typing import Tuple, Optional

logger = logging.getLogger("kothar.router")


def route_model(
    user_msg: str,
    intent: str,
    user_override: Optional[str] = None,
    available_models: Optional[list] = None,
) -> Tuple[str, str]:
    """
    Decide qual provedor/modelo usar (Claude, OpenAI, etc).
    Modelos locais Ollama foram removidos.
    """
    # O router agora delega para oLLMProviders
    # Return Claude como default
    if user_override and user_override not in ("auto", ""):
        return user_override, f"user_override={user_override}"

    # Modelo default é Claude
    default_model = "claude"
    reason = f"intent={intent} → {default_model}"
    logger.info(f"Router: {reason}")
    return default_model, reason
