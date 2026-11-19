from datetime import UTC, datetime, timedelta

from dmvwatch.domain.models import Office, Slot, TransactionType
from dmvwatch.domain.quality import SlotValidator
from dmvwatch.services.sweep import SweepService
from dmvwatch.worker.tasks import sweep_all_offices
from tests.fakes import FakeClock, FakeSlotSource, InMemoryObservationRepository

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
PERMIT = TransactionType.PERMIT_LICENSE_ID


async def test_every_office_the_source_knows_about_is_swept() -> None:
    offices: dict[str, list[Slot]] = {"7001": [], "7002": []}
    source = FakeSlotSource("NY", offices)
    service = SweepService(
        source=source,
        repository=InMemoryObservationRepository(),
        validator=SlotValidator(known_office_ids=frozenset(offices)),
        clock=FakeClock(NOW),
    )
    results = await sweep_all_offices(service, source, PERMIT)
    assert {office_id for office_id, _ in source.calls} == {"7001", "7002"}
    assert len(results) == 2


async def test_results_carry_the_offices_that_found_something() -> None:
    brooklyn = Office(state_code="NY", office_id="7001", name="Office 7001")
    slot = Slot(office=brooklyn, transaction_type=PERMIT, starts_at=NOW + timedelta(days=1))
    source = FakeSlotSource("NY", {"7001": [slot], "7002": []})
    service = SweepService(
        source=source,
        repository=InMemoryObservationRepository(),
        validator=SlotValidator(known_office_ids=frozenset({"7001", "7002"})),
        clock=FakeClock(NOW),
    )
    results = await sweep_all_offices(service, source, PERMIT)
    notifiable = [r.office.office_id for r in results if r.worth_notifying]
    assert notifiable == ["7001"]
