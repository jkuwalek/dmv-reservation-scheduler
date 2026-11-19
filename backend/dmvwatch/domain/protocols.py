"""The seams. Services depend on these, never on concrete adapters."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from dmvwatch.domain.models import CodeCheck, Office, Slot, TransactionType, WatchStatus
from dmvwatch.security.codes import EncryptedCode


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


class CodeValidator(Protocol):
    """Checks an access code against one state's booking system."""

    @property
    def state_code(self) -> str: ...

    async def check(self, access_code: str) -> CodeCheck: ...


class Notifier(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class WatchRepository(Protocol):
    async def create(
        self,
        email: str,
        state_code: str,
        transaction_type: TransactionType,
        encrypted_code: EncryptedCode,
        created_at: datetime,
    ) -> uuid.UUID: ...

    async def set_status(self, watch_id: uuid.UUID, status: WatchStatus) -> bool: ...

    async def forget_credential(self, watch_id: uuid.UUID) -> None: ...

    async def mute_office(
        self, watch_id: uuid.UUID, office_id: str, muted_at: datetime
    ) -> None: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
