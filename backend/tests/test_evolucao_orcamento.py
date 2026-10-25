"""Reservas e consumo monetário inteiros com isolamento e reconciliação."""

import pytest

from backend.servicos.evolucao.modelos import EvolutionError
from backend.servicos.evolucao.operacoes import EvolutionService
from backend.tests.test_evolucao_estado import evolution_db as evolution_db


async def test_budget_reserve_settle_refunds_unused_and_dedupes(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        await service.set_budget("default", {"tokens": 100, "calls": 3, "cost_microunits": 1000})
        reserved = await service.reserve_budget("call-a", {"tokens": 80, "calls": 1, "cost_microunits": 600})
        assert (await service.reserve_budget("call-a", {"tokens": 80, "calls": 1, "cost_microunits": 600}))["id"] == reserved["id"]
        assert (await service.get_budget())["reserved"]["tokens"] == 80
        with pytest.raises(EvolutionError, match="budget_exceeded"):
            await service.reserve_budget("call-b", {"tokens": 21})
        closed = await service.settle_budget("call-a", {"tokens": 20, "calls": 1, "cost_microunits": 200})
        assert (await service.settle_budget("call-a", {"tokens": 20, "calls": 1, "cost_microunits": 200}))["revision"] == closed["revision"]
        budget = await service.get_budget()
        assert budget["reserved"] == {"tokens": 0, "calls": 0, "cost_microunits": 0}
        assert budget["spent"] == {"tokens": 20, "calls": 1, "cost_microunits": 200}
        await db.commit()
    async with evolution_db() as db:
        assert (await EvolutionService(db, "owner", "project").get_budget())["spent"]["tokens"] == 20


async def test_release_exactly_once_and_reject_settlement_after_release(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        await service.set_budget("default", {"tokens": 100})
        await service.reserve_budget("reserved", {"tokens": 70})
        released = await service.release_budget("reserved")
        assert (await service.release_budget("reserved"))["revision"] == released["revision"]
        assert (await service.get_budget())["reserved"]["tokens"] == 0
        with pytest.raises(EvolutionError, match="reservation_closed"):
            await service.settle_budget("reserved", {"tokens": 1})
        with pytest.raises(EvolutionError, match="dedupe_conflict"):
            await service.reserve_budget("reserved", {"tokens": 71})


async def test_limit_cannot_reduce_below_committed_and_isolates_projects(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        await service.set_budget("default", {"tokens": 100})
        await service.reserve_budget("a", {"tokens": 70})
        with pytest.raises(EvolutionError, match="budget_below_committed_usage"):
            await service.set_budget("default", {"tokens": 69})
        with pytest.raises(EvolutionError, match="not_found"):
            await EvolutionService(db, "owner", "other-project").get_budget()


async def test_real_overrun_is_recorded_and_blocks_new_spend(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        await service.set_budget("default", {"tokens": 100})
        await service.reserve_budget("a", {"tokens": 80})
        settled = await service.settle_budget("a", {"tokens": 110})
        assert settled["overrun"] is True
        budget = await service.get_budget()
        assert budget["spent"]["tokens"] == 110
        assert budget["reserved"]["tokens"] == 0
        assert budget["overrun"] is True
        with pytest.raises(EvolutionError, match="budget_exceeded"):
            await service.reserve_budget("new-call", {"tokens": 1})


async def test_partial_failed_reservation_transaction_does_not_leak_state(evolution_db):
    async with evolution_db() as db:
        service = EvolutionService(db, "owner", "project")
        await service.set_budget("default", {"tokens": 100})
        original = service.repo.replace

        async def conflict(kind, row, payload):
            if kind == "budget":
                raise EvolutionError("concurrent_change")
            return await original(kind, row, payload)

        service.repo.replace = conflict
        with pytest.raises(EvolutionError, match="concurrent_change"):
            await service.reserve_budget("rolled-back", {"tokens": 80})
        service.repo.replace = original
        assert (await service.get_budget())["reserved"]["tokens"] == 0
        assert await service.repo.list("reservation") == []
