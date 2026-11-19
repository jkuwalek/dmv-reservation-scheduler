from datetime import UTC, datetime, timedelta

from dmvwatch.domain.models import Office, Slot, TransactionType
from dmvwatch.domain.quality import SlotValidator
from dmvwatch.services.sweep import SweepService
from tests.fakes import FakeClock, FakeSlotSource, InMemoryObservationRepository

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
PERMIT = TransactionType.PERMIT_LICENSE_ID
BROOKLYN = Office(state_code="NY", office_id="7001", name="Office 7001")


def _slot(hours_ahead: int, office: Office = BROOKLYN) -> Slot:
    return Slot(
        office=office,
        transaction_type=PERMIT,
        starts_at=NOW + timedelta(hours=hours_ahead),
    )


def _service(
    source: FakeSlotSource,
    repo: InMemoryObservationRepository,
    clock: FakeClock,
) -> SweepService:
    return SweepService(
        source=source,
        repository=repo,
        validator=SlotValidator(known_office_ids=frozenset({"7001", "7002"})),
        clock=clock,
    )


async def test_the_first_sweep_reports_everything_as_newly_available() -> None:
    source = FakeSlotSource("NY", {"7001": [_slot(24), _slot(48)]})
    repo = InMemoryObservationRepository()
    result = await _service(source, repo, FakeClock(NOW)).sweep(BROOKLYN, PERMIT)
    assert len(result.newly_available) == 2
    assert result.worth_notifying is True


async def test_a_repeat_sweep_with_the_same_slots_reports_nothing_new() -> None:
    source = FakeSlotSource("NY", {"7001": [_slot(24)]})
    repo = InMemoryObservationRepository()
    service = _service(source, repo, FakeClock(NOW))
    await service.sweep(BROOKLYN, PERMIT)
    result = await service.sweep(BROOKLYN, PERMIT)
    assert result.newly_available == []
    assert result.worth_notifying is False


async def test_a_slot_that_appears_later_is_reported_as_new() -> None:
    source = FakeSlotSource("NY", {"7001": [_slot(24)]})
    repo = InMemoryObservationRepository()
    service = _service(source, repo, FakeClock(NOW))
    await service.sweep(BROOKLYN, PERMIT)
    source.set_slots("7001", [_slot(24), _slot(72)])
    result = await service.sweep(BROOKLYN, PERMIT)
    assert [s.starts_at for s in result.newly_available] == [NOW + timedelta(hours=72)]


async def test_invalid_slots_are_counted_and_not_recorded() -> None:
    source = FakeSlotSource("NY", {"7001": [_slot(24), _slot(-5)]})
    repo = InMemoryObservationRepository()
    result = await _service(source, repo, FakeClock(NOW)).sweep(BROOKLYN, PERMIT)
    assert result.rejected == {"slot_in_past": 1}
    assert len(result.seen) == 1
    assert len(repo.records) == 1


async def test_every_sweep_is_recorded_even_when_it_finds_nothing() -> None:
    source = FakeSlotSource("NY", {"7001": []})
    repo = InMemoryObservationRepository()
    result = await _service(source, repo, FakeClock(NOW)).sweep(BROOKLYN, PERMIT)
    assert result.seen == []
    assert result.rejected == {}
