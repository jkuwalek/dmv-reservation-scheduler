import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dmvwatch.adapters.db.tables import SlotObservation
from dmvwatch.domain.models import Office, Slot, TransactionType


class SqlObservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_sweep(
        self,
        sweep_id: uuid.UUID,
        slots: Sequence[Slot],
        observed_at: datetime,
    ) -> None:
        self._session.add_all(
            [
                SlotObservation(
                    sweep_id=sweep_id,
                    state_code=slot.office.state_code,
                    office_id=slot.office.office_id,
                    transaction_type=slot.transaction_type.value,
                    observed_at=observed_at,
                    slot_datetime=slot.starts_at,
                )
                for slot in slots
            ]
        )
        await self._session.commit()

    async def latest_slot_times(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> set[datetime]:
        newest = (
            select(SlotObservation.sweep_id)
            .where(
                SlotObservation.office_id == office.office_id,
                SlotObservation.transaction_type == transaction_type.value,
            )
            .order_by(SlotObservation.observed_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        rows = await self._session.execute(
            select(SlotObservation.slot_datetime).where(SlotObservation.sweep_id == newest)
        )
        return set(rows.scalars().all())
