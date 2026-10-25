"""
=============================================================
 KOTHAR v4.0 — Harness Package
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Pacote de controle do fluxo de execução.
 Componentes:
 - Circuit Breaker: proteção contra falhas em cascata
 - Step Validator: validação de dependências e locks
 - Checkpoint: recuperação após falhas
 - Blueprint Executor: execução controlada do fluxo
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitBreakerRegistry,
    CircuitState,
)
from .step_validator import (
    StepValidator,
    StepValidationResult,
    STEP_DEPENDENCIES,
)
from .checkpoint import (
    CheckpointManager,
    CheckpointData,
    checkpoint_manager,
)

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitBreakerRegistry",
    "CircuitState",
    # Step Validator
    "StepValidator",
    "StepValidationResult",
    "STEP_DEPENDENCIES",
    # Checkpoint
    "CheckpointManager",
    "CheckpointData",
    "checkpoint_manager",
]
