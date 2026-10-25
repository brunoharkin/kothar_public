"""
Testes para o Kothar Token Counter
==================================
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Adiciona o backend ao path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from token_counter.models import (
    Fidelity,
    ProviderStatus,
    WindowType,
    LimitWindow,
    UsageContext,
    LocalPrediction,
    Totals,
    ProviderSnapshot,
)
from token_counter.ledger import LocalTokenLedger
from token_counter.providers.claude_cli import ClaudeCLIProvider
from token_counter.providers.base import ProviderKind, UsageProviderError
from token_counter.store import UsageStore, StoreConfig


def test_totals():
    """Testa a estrutura Totals."""
    print("Testing Totals...")

    totals = Totals()
    assert totals.requests == 0
    assert totals.input_tokens == 0
    assert totals.output_tokens == 0

    # Adiciona uma predição
    prediction = LocalPrediction(
        input_tokens=1000,
        output_tokens=500,
        reasoning_tokens=100,
    )
    totals.add(prediction)

    assert totals.requests == 1
    assert totals.input_tokens == 1000
    assert totals.output_tokens == 500
    assert totals.reasoning_tokens == 100
    assert totals.total_tokens == 1500
    assert totals.reasoning_share == 0.2  # 100/500

    print("  ✓ Totals works correctly")


def test_limit_window():
    """Testa a estrutura LimitWindow."""
    print("Testing LimitWindow...")

    window = LimitWindow(
        type=WindowType.SESSION,
        used_fraction=0.38,
        used=3800,
        limit=10000,
        remaining=6200,
    )

    assert window.percent_used == 38.0
    assert window.compact_used == "3.8k"
    assert "38% Used" in window.format_for_display()
    assert "62% left" in window.format_for_display()

    # Testa formato compacto
    window_large = LimitWindow(
        type=WindowType.MONTHLY,
        used_fraction=0.65,
        used=650000,
        limit=1000000,
        remaining=350000,
    )
    assert window_large.compact_used == "650.0k"

    print("  ✓ LimitWindow works correctly")


def test_local_prediction():
    """Testa LocalPrediction."""
    print("Testing LocalPrediction...")

    pred = LocalPrediction(
        input_tokens=500,
        output_tokens=250,
        reasoning_tokens=50,
    )

    data = pred.to_dict()
    assert data["input_tokens"] == 500
    assert data["output_tokens"] == 250
    assert data["reasoning_tokens"] == 50

    # Reconstrói
    pred2 = LocalPrediction.from_dict(data)
    assert pred2.input_tokens == pred.input_tokens
    assert pred2.output_tokens == pred.output_tokens

    print("  ✓ LocalPrediction works correctly")


def test_local_token_ledger():
    """Testa o LocalTokenLedger."""
    print("Testing LocalTokenLedger...")

    # Usa diretório temporário para testes
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = LocalTokenLedger(storage_path=tmpdir)

        # Registra algumas predições
        pred1 = LocalPrediction(
            input_tokens=1000,
            output_tokens=500,
            reasoning_tokens=100,
            timestamp=datetime.now(),
        )
        ledger.record(pred1)

        pred2 = LocalPrediction(
            input_tokens=2000,
            output_tokens=800,
            reasoning_tokens=150,
            timestamp=datetime.now(),
        )
        ledger.record(pred2)

        # Verifica totais de hoje
        today = ledger.totals_today()
        assert today.requests == 2
        assert today.input_tokens == 3000
        assert today.output_tokens == 1300
        assert today.reasoning_tokens == 250
        assert today.total_tokens == 4300

        # Verifica summary
        summary = ledger.summary()
        assert summary["today"]["requests"] == 2
        assert summary["all_time"]["total_tokens"] == 4300

        # Verifica persistência (recarrega)
        ledger2 = LocalTokenLedger(storage_path=tmpdir)
        today2 = ledger2.totals_today()
        assert today2.requests == 2
        assert today2.input_tokens == 3000

        print("  ✓ LocalTokenLedger works correctly")


def test_claude_cli_provider():
    """Testa o Claude CLI Provider."""
    print("Testing ClaudeCLIProvider...")

    provider = ClaudeCLIProvider()

    # Verifica propriedades
    assert provider.id == "claude-cli"
    assert provider.display_name == "Claude Code"
    assert provider.kind == ProviderKind.USAGE
    assert provider.glyph() == "🔮"

    # Verifica disponibilidade
    is_available = provider.is_available()
    print(f"  Claude CLI available: {is_available}")

    # Se disponível, testa fetch
    if is_available:
        print("  Testing fetch (this may take a few seconds)...")
        try:
            snapshot = asyncio.run(provider.fetch_snapshot())
            print(f"  ✓ Fetch successful: {snapshot.name}")
            print(f"    Status: {snapshot.status.value}")
            print(f"    Windows: {len(snapshot.windows)}")

            for window in snapshot.windows:
                print(f"      - {window.type.value}: {window.percent_used:.0f}%")
        except UsageProviderError as e:
            print(f"  ⚠ Fetch failed: {e.message}")
    else:
        print("  ⚠ Claude CLI not available (expected if not installed)")


def test_usage_store():
    """Testa o UsageStore."""
    print("Testing UsageStore...")

    config = StoreConfig(
        refresh_interval=5,  # Curto para testes
        idle_refresh_interval=10,
        persistence_path="~/.kothar/token-usage/test-store.json",
    )
    store = UsageStore(config)

    # Registra provider
    provider = ClaudeCLIProvider()
    store.register(provider)

    assert "claude-cli" in store._providers
    assert store.get_provider("claude-cli") == provider

    # Testa snapshot inicial
    snapshot = store.get_snapshot("claude-cli")
    print(f"  Initial snapshot: {snapshot}")

    # Testa fetch
    if provider.is_available():
        print("  Testing fetch...")
        result = asyncio.run(store.fetch("claude-cli"))
        if result:
            print(f"  ✓ Fetch successful: {result.status.value}")
            print(f"    Headline: {result.headline}")
        else:
            print("  ⚠ Fetch returned None")

    print("  ✓ UsageStore works correctly")


def test_provider_snapshot():
    """Testa ProviderSnapshot."""
    print("Testing ProviderSnapshot...")

    snapshot = ProviderSnapshot(
        id="test",
        name="Test Provider",
        fidelity=Fidelity.OFFICIAL,
        status=ProviderStatus.OK,
        windows=[
            LimitWindow(type=WindowType.SESSION, used_fraction=0.5),
            LimitWindow(type=WindowType.WEEKLY, used_fraction=0.25),
        ],
    )

    assert snapshot.headline.type == WindowType.SESSION
    assert snapshot.weekly_window.type == WindowType.WEEKLY

    data = snapshot.to_dict()
    assert data["id"] == "test"
    assert data["name"] == "Test Provider"
    assert len(data["windows"]) == 2

    print("  ✓ ProviderSnapshot works correctly")


def test_totals_addition():
    """Testa soma de Totals."""
    print("Testing Totals addition...")

    t1 = Totals(requests=5, input_tokens=1000, output_tokens=500)
    t2 = Totals(requests=3, input_tokens=600, output_tokens=300)

    t3 = t1 + t2

    assert t3.requests == 8
    assert t3.input_tokens == 1600
    assert t3.output_tokens == 800
    assert t3.total_tokens == 2400

    print("  ✓ Totals addition works correctly")


def test_fidelity_prefix():
    """Testa prefixo de Fidelity para display."""
    print("Testing Fidelity prefix...")

    assert Fidelity.OFFICIAL.prefix_for_display() == ""
    assert Fidelity.DERIVED.prefix_for_display() == "~"
    assert Fidelity.MANUAL.prefix_for_display() == "~"

    print("  ✓ Fidelity prefix works correctly")


def test_ledger_date_range():
    """Testa totais para intervalo de datas."""
    print("Testing ledger date range...")

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = LocalTokenLedger(storage_path=tmpdir)

        # Adiciona dados para diferentes dias
        today = datetime.now().date()

        # Hoje
        ledger.record(LocalPrediction(
            input_tokens=100,
            output_tokens=50,
            timestamp=datetime.now(),
        ))

        # Ontem
        yesterday = datetime.now() - timedelta(days=1)
        ledger.record(LocalPrediction(
            input_tokens=200,
            output_tokens=100,
            timestamp=yesterday,
        ))

        # 3 dias atrás
        three_days_ago = datetime.now() - timedelta(days=3)
        ledger.record(LocalPrediction(
            input_tokens=300,
            output_tokens=150,
            timestamp=three_days_ago,
        ))

        # Verifica range
        week_ago = today - timedelta(days=7)
        total_week = ledger.totals_for_range(week_ago, today)
        assert total_week.requests == 3  # Todos dentro de 7 dias

        # Verifica datas específicas
        yesterday_date = yesterday.date()
        total_yesterday = ledger.totals_for_date(yesterday_date)
        assert total_yesterday.input_tokens == 200

        print("  ✓ Ledger date range works correctly")


def run_all_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("Kothar Token Counter - Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_totals,
        test_totals_addition,
        test_fidelity_prefix,
        test_limit_window,
        test_local_prediction,
        test_provider_snapshot,
        test_local_token_ledger,
        test_ledger_date_range,
        test_claude_cli_provider,
        test_usage_store,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
