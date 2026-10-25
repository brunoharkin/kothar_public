"""
=============================================================
 KOTHAR v4.0 — Circuit Breaker Tests
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Testa a abertura do circuit breaker após falhas consecutivas.
"""

import asyncio
import pytest

from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
)


class TestCircuitBreaker:
    """Testes para o Circuit Breaker."""

    @pytest.fixture
    def cb(self):
        """Cria um circuit breaker limpo para cada teste."""
        return CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=60,
        )

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, cb):
        """Estado inicial deve ser CLOSED."""
        assert cb.state == CircuitState.CLOSED
        assert cb.circuit_state == "closed"
        assert cb.failure_count == 0
        assert cb.circuit_failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_returns_result(self, cb):
        """Chamada bem-sucedida retorna resultado e não abre circuito."""
        async def success_func():
            return "ok"

        result = await cb.call(success_func)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_increments_counter(self, cb):
        """Falha deve incrementar contador."""
        async def fail_func():
            raise ConnectionError("connection refused")

        # 2 falhas não abrem o circuito
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(fail_func)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2
        assert cb.circuit_failure_count == 2

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self, cb):
        """Circuito deve abrir após failure_threshold falhas."""
        call_count = 0

        async def fail_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("connection refused")

        # 3 falhas (threshold padrão)
        for i in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_open_circuit_blocks_calls(self, cb):
        """Circuito aberto deve bloquear chamadas e levantar CircuitBreakerOpen."""
        async def fail_func():
            raise ConnectionError("connection refused")

        # Abre o circuito
        for _ in range(3):
            try:
                await cb.call(fail_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Próxima chamada deve ser bloqueada
        with pytest.raises(CircuitBreakerOpen) as exc_info:
            await cb.call(fail_func)

        assert exc_info.value.name == "test"
        assert exc_info.value.remaining_time > 0

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self, cb):
        """Circuito deve ir para HALF_OPEN após recovery_timeout."""
        async def fail_func():
            raise ConnectionError("connection refused")

        # Abre o circuito
        for _ in range(3):
            try:
                await cb.call(fail_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Simula passagem do recovery_timeout
        cb.last_failure_time = 0  # Força timeout passado
        cb.recovery_timeout = 0   # Timeout instantâneo para teste

        # Próxima chamada deve ir para HALF_OPEN
        allowed, _ = await cb._should_allow_request()
        assert allowed
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, cb):
        """Sucesso em HALF_OPEN fecha o circuito."""
        # Configura para half_open
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_calls = 0
        cb.last_failure_time = 0
        cb.recovery_timeout = 0

        async def success_func():
            return "recovered"

        result = await cb.call(success_func)

        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, cb):
        """Falha em HALF_OPEN reabre o circuito."""
        # Configura para half_open
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_calls = 1

        async def fail_func():
            raise ConnectionError("still failing")

        with pytest.raises(ConnectionError):
            await cb.call(fail_func)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_manual_reset(self, cb):
        """Reset manual deve fechar o circuito."""
        # Abre o circuito
        async def fail_func():
            raise ConnectionError("connection refused")

        for _ in range(3):
            try:
                await cb.call(fail_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_get_status(self, cb):
        """get_status() retorna dicionário com métricas."""
        async def fail_func():
            raise ConnectionError("connection refused")

        for _ in range(2):
            try:
                await cb.call(fail_func)
            except ConnectionError:
                pass

        status = cb.get_status()

        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert status["failure_count"] == 2
        assert status["failure_threshold"] == 3
        assert status["recovery_timeout"] == 60

    @pytest.mark.asyncio
    async def test_sync_function_works(self, cb):
        """Funções síncronas também devem funcionar."""
        def sync_func():
            return 42

        result = await cb.call(sync_func)
        assert result == 42

    @pytest.mark.asyncio
    async def test_custom_exception_type(self):
        """Circuit breaker deve contar apenas expected_exception."""
        cb = CircuitBreaker(
            name="custom",
            failure_threshold=2,
            expected_exception=ValueError,
        )

        async def wrong_exception():
            raise TypeError("wrong type")  # Não conta

        async def right_exception():
            raise ValueError("right type")  # Conta

        # Não deve abrir com 2 TypeError
        for _ in range(2):
            with pytest.raises(TypeError):
                await cb.call(wrong_exception)

        assert cb.state == CircuitState.CLOSED

        # 2 ValueError devem abrir
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(right_exception)

        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerMetrics:
    """Testes para métricas expostas."""

    @pytest.fixture
    def cb(self):
        return CircuitBreaker(name="metrics_test", failure_threshold=3)

    def test_circuit_state_property(self, cb):
        """circuit_state property expõe estado."""
        assert cb.circuit_state == "closed"
        cb.state = CircuitState.OPEN
        assert cb.circuit_state == "open"
        cb.state = CircuitState.HALF_OPEN
        assert cb.circuit_state == "half_open"

    def test_circuit_failure_count_property(self, cb):
        """circuit_failure_count property expõe contador."""
        assert cb.circuit_failure_count == 0
        cb.failure_count = 5
        assert cb.circuit_failure_count == 5


class TestForceFailureScenario:
    """
    Teste de cenário: força falha e verifica abertura.
    Este é o teste principal que demonstra a funcionalidade.
    """

    @pytest.mark.asyncio
    async def test_forced_failure_opens_circuit(self):
        """
        Cenário: ChromaDB falha 3x -> circuito abre.
        """
        cb = CircuitBreaker(
            name="chroma_db",
            failure_threshold=3,
            recovery_timeout=30,
        )

        # Simula ChromaDB indisponível
        call_count = 0

        async def chroma_call():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("ChromaDB connection refused")

        # 1a chamada - falha
        print(f"Chamada 1: failure_count={cb.failure_count}, state={cb.state.value}")
        with pytest.raises(ConnectionError):
            await cb.call(chroma_call)
        assert cb.state == CircuitState.CLOSED

        # 2a chamada - falha
        print(f"Chamada 2: failure_count={cb.failure_count}, state={cb.state.value}")
        with pytest.raises(ConnectionError):
            await cb.call(chroma_call)
        assert cb.state == CircuitState.CLOSED

        # 3a chamada - falha -> abre
        print(f"Chamada 3: failure_count={cb.failure_count}, state={cb.state.value}")
        with pytest.raises(ConnectionError):
            await cb.call(chroma_call)
        assert cb.state == CircuitState.OPEN
        assert call_count == 3

        # 4a chamada - bloqueada
        print(f"Chamada 4 (deve ser bloqueada): state={cb.state.value}")
        with pytest.raises(CircuitBreakerOpen) as exc:
            await cb.call(chroma_call)

        print(f"  -> CircuitBreakerOpen: {exc.value}")
        assert cb.last_failure_time is not None

        # Verifica métricas
        print(f"\n=== Métricas do Circuit Breaker ===")
        print(f"  circuit_state: {cb.circuit_state}")
        print(f"  circuit_failure_count: {cb.circuit_failure_count}")
        print(f"  failure_threshold: {cb.failure_threshold}")
        print(f"  recovery_timeout: {cb.recovery_timeout}s")

        assert cb.circuit_state == "open"
        assert cb.circuit_failure_count == 3
