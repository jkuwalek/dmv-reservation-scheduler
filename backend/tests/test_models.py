from datetime import UTC, datetime

import pytest

from dmvwatch.domain.models import (
    Office,
    Slot,
    SweepResult,
    TransactionType,
    WatchStatus,
)


def test_offices_with_the_same_id_are_equal() -> None:
    a = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    b = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    assert a == b
    assert len({a, b}) == 1


def test_slots_are_hashable_so_they_can_be_de_duplicated() -> None:
    office = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    when = datetime(2026, 12, 1, 9, 30, tzinfo=UTC)
    first = Slot(office=office, transaction_type=TransactionType.PERMIT_LICENSE_ID, starts_at=when)
    second = Slot(office=office, transaction_type=TransactionType.PERMIT_LICENSE_ID, starts_at=when)
    assert len({first, second}) == 1


def test_slots_are_immutable() -> None:
    office = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    slot = Slot(
        office=office,
        transaction_type=TransactionType.PERMIT_LICENSE_ID,
        starts_at=datetime(2026, 12, 1, 9, 30, tzinfo=UTC),
    )
    with pytest.raises(AttributeError):
        slot.starts_at = datetime(2026, 12, 2, 9, 30, tzinfo=UTC)  # type: ignore[misc]


def test_watch_statuses_cover_the_lifecycle() -> None:
    assert WatchStatus.PENDING_CONFIRMATION.value == "pending_confirmation"
    assert WatchStatus.ACTIVE.value == "active"
    assert WatchStatus.NOTIFIED.value == "notified"
    assert WatchStatus.CLOSED.value == "closed"
    assert WatchStatus.EXPIRED.value == "expired"


def test_a_sweep_with_new_slots_is_worth_notifying() -> None:
    office = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    slot = Slot(
        office=office,
        transaction_type=TransactionType.PERMIT_LICENSE_ID,
        starts_at=datetime(2026, 12, 1, 9, 30, tzinfo=UTC),
    )
    result = SweepResult(office=office, seen=[slot], newly_available=[slot], rejected={})
    assert result.worth_notifying is True


def test_a_sweep_that_found_nothing_new_is_not_worth_notifying() -> None:
    office = Office(state_code="NY", office_id="7001", name="Brooklyn Atlantic Center")
    slot = Slot(
        office=office,
        transaction_type=TransactionType.PERMIT_LICENSE_ID,
        starts_at=datetime(2026, 12, 1, 9, 30, tzinfo=UTC),
    )
    result = SweepResult(office=office, seen=[slot], newly_available=[], rejected={})
    assert result.worth_notifying is False
