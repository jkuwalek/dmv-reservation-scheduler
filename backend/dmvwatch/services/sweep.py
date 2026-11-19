"""Turns a SlotSource into a recorded observation and a list of what is new."""

import uuid
from collections import Counter

from dmvwatch.domain.models import Office, SweepResult, TransactionType
from dmvwatch.domain.protocols import Clock, ObservationRepository, SlotSource
from dmvwatch.domain.quality import SlotValidator, partition


class SweepService:
    def __init__(
        self,
        source: SlotSource,
        repository: ObservationRepository,
        validator: SlotValidator,
        clock: Clock,
    ) -> None:
        self._source = source
        self._repository = repository
        self._validator = validator
        self._clock = clock

    async def sweep(self, office: Office, transaction_type: TransactionType) -> SweepResult:
        observed_at = self._clock.now()
        previous = await self._repository.latest_slot_times(office, transaction_type)

        raw = self._source.available_slots(office, transaction_type)
        accepted, rejections = partition(raw, validator=self._validator, now=observed_at)

        await self._repository.record_sweep(
            sweep_id=uuid.uuid4(),
            slots=accepted,
            observed_at=observed_at,
        )

        newly_available = [slot for slot in accepted if slot.starts_at not in previous]
        return SweepResult(
            office=office,
            seen=accepted,
            newly_available=newly_available,
            rejected=dict(Counter(r.reason for r in rejections)),
        )
