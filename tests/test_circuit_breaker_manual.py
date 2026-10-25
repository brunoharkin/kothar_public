#!/usr/bin/env python3
"""
Teste manual do Circuit Breaker - valida que falha força abertura.
Execute: python3 tests/test_circuit_breaker_manual.py
"""

import asyncio
import sys
import os

# Adiciona backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
)


async def test_forced_failure_scenario():
    """
    Cenário: ChromaDB falha 3x -> circuito abre.
    """
    print("\n" + "=" * 60)
    print("TESTE: Circuit Breaker - Força Falha e Verifica Abertura")
    print("=" * 60)

    cb = CircuitBreaker(
        name="chroma_db",
        failure_threshold=3,
        recovery_timeout=30,
    )

    print(f"\n1. Estado inicial:")
    print(f"   state={cb.state.value}, failure_count={cb.failure_count}")

    # Simula ChromaDB indisponível
    call_count = 0

    async def chroma_call():
        nonlocal call_count
        call_count += 1
        print(f"   [Chamada {call_count}] -> ChromaDB connection refused!")
        raise ConnectionError("ChromaDB connection refused")

    # 1a chamada - falha
    print(f"\n2. Chamada 1 (falha esperada):")
    try:
        await cb.call(chroma_call)
    except ConnectionError:
        pass
    print(f"   state={cb.state.value}, failure_count={cb.failure_count}")
    assert cb.state == CircuitState.CLOSED, "FALHA: Circuito deveria estar CLOSED"

    # 2a chamada - falha
    print(f"\n3. Chamada 2 (falha esperada):")
    try:
        await cb.call(chroma_call)
    except ConnectionError:
        pass
    print(f"   state={cb.state.value}, failure_count={cb.failure_count}")
    assert cb.state == CircuitState.CLOSED, "FALHA: Circuito deveria estar CLOSED"

    # 3a chamada - falha -> abre!
    print(f"\n4. Chamada 3 (falha -> CIRCUITO ABRE):")
    try:
        await cb.call(chroma_call)
    except ConnectionError:
        pass
    print(f"   state={cb.state.value}, failure_count={cb.failure_count}")
    assert cb.state == CircuitState.OPEN, "FALHA: Circuito deveria estar OPEN!"
    assert call_count == 3

    # 4a chamada - bloqueada!
    print(f"\n5. Chamada 4 (DEVE SER BLOQUEADA):")
    blocked = False
    try:
        await cb.call(chroma_call)
    except CircuitBreakerOpen as e:
        blocked = True
        print(f"   >>> CircuitBreakerOpen! <<<")
        print(f"   name={e.name}")
        print(f"   remaining_time={e.remaining_time:.1f}s")

    assert blocked, "FALHA: Chamada deveria ter sido bloqueada!"

    # Métricas
    print(f"\n6. Métricas do Circuit Breaker:")
    print(f"   circuit_state: {cb.circuit_state}")
    print(f"   circuit_failure_count: {cb.circuit_failure_count}")
    print(f"   failure_threshold: {cb.failure_threshold}")
    print(f"   recovery_timeout: {cb.recovery_timeout}s")

    assert cb.circuit_state == "open", "FALHA: Métrica circuit_state deveria ser 'open'"
    assert cb.circuit_failure_count == 3, "FALHA: Métrica deveria ser 3"

    # Reset manual
    print(f"\n7. Reset manual do circuito:")
    cb.reset()
    print(f"   state={cb.state.value}, failure_count={cb.failure_count}")
    assert cb.state == CircuitState.CLOSED, "FALHA: Após reset deveria estar CLOSED"

    print("\n" + "=" * 60)
    print("SUCESSO! Todos os testes passaram!")
    print("=" * 60 + "\n")


async def test_half_open_recovery():
    """Testa recuperação em half-open."""
    print("\n" + "=" * 60)
    print("TESTE: Recuperação em HALF_OPEN")
    print("=" * 60)

    cb = CircuitBreaker(name="test_recovery", failure_threshold=2, recovery_timeout=1)

    # Abre o circuito
    async def fail():
        raise ConnectionError("fail")

    for _ in range(2):
        try:
            await cb.call(fail)
        except ConnectionError:
            pass

    print(f"1. Circuito aberto: state={cb.state.value}")
    assert cb.state == CircuitState.OPEN

    # Simula timeout passado (força half-open)
    cb.last_failure_time = 0
    cb.recovery_timeout = 0

    # Primeiro sucesso fecha
    print(f"2. Simulando timeout e primeira chamada...")

    async def success():
        return "OK"

    result = await cb.call(success)
    print(f"   Resultado: {result}, state={cb.state.value}")
    assert cb.state == CircuitState.CLOSED
    assert result == "OK"

    print("\n" + "=" * 60)
    print("SUCESSO! Recuperação funcionou!")
    print("=" * 60 + "\n")


async def main():
    try:
        await test_forced_failure_scenario()
        await test_half_open_recovery()
        return 0
    except AssertionError as e:
        print(f"\nERRO: {e}")
        return 1
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
