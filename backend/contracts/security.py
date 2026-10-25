"""Decisões conservadoras para resultados de agentes; não certifica produção."""
from typing import Any


def approved_result(result: Any, expected_status: str) -> bool:
    """Um retorno desconhecido, simulado ou com erro nunca aprova uma etapa."""
    return (
        isinstance(result, dict)
        and result.get("status") == expected_status
        and not result.get("error")
        and not result.get("errors")
        and not result.get("blockers")
        and not result.get("simulated")
        and result.get("returncode", 0) == 0
    )


def security_coverage_approved(result: Any) -> bool:
    """Confirma cobertura do scanner, não autenticação/autorização ou segurança de produção."""
    if not approved_result(result, "passed"):
        return False
    requested = result.get("files_requested")
    scanned = result.get("files_scanned")
    return (
        type(requested) is int
        and type(scanned) is int
        and requested > 0
        and scanned == requested
        and result.get("coverage_complete") is True
        and not result.get("ignored_files")
        and not result.get("issues")
    )

