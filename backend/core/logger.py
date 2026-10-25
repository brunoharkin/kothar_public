"""
=============================================================
 KOTHAR v4.0 — Logger Estruturado
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Logger JSON estruturado com contexto de agente e sessão.
 Compatível com Loki, CloudWatch, ou qualquer stack de log.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

import structlog

from backend.core.config import settings
from backend.core.privacy import redact_log


def _add_kothar_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Injeta metadados do Kothar em cada linha de log."""
    event_dict["kothar_version"] = settings.kothar_version
    event_dict["environment"] = settings.environment
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def setup_logging() -> None:
    """
    Configura logging estruturado via structlog.
    Em desenvolvimento: output colorido e legível.
    Em produção: JSON puro para ingestão por coletores.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_kothar_context,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_development:
        processors = [
            *shared_processors,
            redact_log,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            redact_log,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )

    # Configura stdlib logging para capturar bibliotecas externas
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )

    # Silencia logs ruidosos de bibliotecas externas
    for noisy_lib in ["httpx", "httpcore", "asyncio", "uvicorn.access"]:
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


def get_logger(name: str, **initial_context: Any) -> structlog.BoundLogger:
    """
    Fábrica de logger com contexto inicial.

    Uso:
        log = get_logger("maestro.orchestrator", agent="maestro")
        log.info("Tarefa iniciada", task_id="abc-123")
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger
