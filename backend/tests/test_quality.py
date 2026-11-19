from datetime import UTC, datetime, timedelta

from dmvwatch.domain.models import Office, Slot, TransactionType
from dmvwatch.domain.quality import SlotValidator, partition

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
BROOKLYN = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
VALIDATOR = SlotValidator(known_office_ids=frozenset({"7001"}))


def _slot(starts_at: datetime, office: Office = BROOKLYN) -> Slot:
    return Slot(
        office=office,
        transaction_type=TransactionType.PERMIT_LICENSE_ID,
        starts_at=starts_at,
    )


def test_a_future_slot_at_a_known_office_is_accepted() -> None:
    assert VALIDATOR.reason_to_reject(_slot(NOW + timedelta(days=1)), now=NOW) is None


def test_a_slot_in_the_past_is_rejected() -> None:
    reason = VALIDATOR.reason_to_reject(_slot(NOW - timedelta(minutes=1)), now=NOW)
    assert reason == "slot_in_past"


def test_a_naive_datetime_is_rejected() -> None:
    naive = datetime(2026, 12, 1, 9, 30)
    assert VALIDATOR.reason_to_reject(_slot(naive), now=NOW) == "naive_datetime"


def test_an_unknown_office_is_rejected() -> None:
    mystery = Office(state_code="NY", office_id="9999", name="Nowhere")
    slot = _slot(NOW + timedelta(days=1), office=mystery)
    assert VALIDATOR.reason_to_reject(slot, now=NOW) == "unknown_office"


def test_partition_splits_good_rows_from_rejections() -> None:
    good = _slot(NOW + timedelta(days=1))
    bad = _slot(NOW - timedelta(days=1))
    accepted, rejected = partition([good, bad], validator=VALIDATOR, now=NOW)
    assert accepted == [good]
    assert len(rejected) == 1
    assert rejected[0].slot == bad
    assert rejected[0].reason == "slot_in_past"
