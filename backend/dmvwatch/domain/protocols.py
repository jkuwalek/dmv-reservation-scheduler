"""The seams. Services depend on these, never on concrete adapters."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from dmvwatch.domain.models import Office, Slot, TransactionType


class Clock(Protocol):
    def now(self) -> datetime: ...


class SlotSource(Protocol):
    """One state's booking system."""

    @property
    def state_code(self) -> str: ...

    def offices(self) -> Sequence[Office]: ...

    def available_slots(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> Sequence[Slot]: ...


class ObservationRepository(Protocol):
    async def record_sweep(
        self,
        sweep_id: uuid.UUID,
        slots: Sequence[Slot],
        observed_at: datetime,
    ) -> None: ...

    async def latest_slot_times(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> set[datetime]: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
