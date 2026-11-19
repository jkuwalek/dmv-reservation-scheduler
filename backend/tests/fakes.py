"""Doubles for the protocols, so service tests need no browser and no database."""

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta

from dmvwatch.domain.models import (
    CodeCheck,
    Office,
    Slot,
    TransactionType,
    WatchStatus,
)
from dmvwatch.security.codes import EncryptedCode


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class FakeSlotSource:
    """Returns whatever it was told to return, per office."""

    def __init__(self, state_code: str, slots_by_office: dict[str, list[Slot]]) -> None:
        self._state_code = state_code
        self._slots_by_office = slots_by_office
        self.calls: list[tuple[str, TransactionType]] = []

    @property
    def state_code(self) -> str:
        return self._state_code

    def offices(self) -> Sequence[Office]:
        return [
            Office(state_code=self._state_code, office_id=office_id, name=f"Office {office_id}")
            for office_id in self._slots_by_office
        ]

    def available_slots(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> Sequence[Slot]:
        self.calls.append((office.office_id, transaction_type))
        return self._slots_by_office.get(office.office_id, [])

    def set_slots(self, office_id: str, slots: list[Slot]) -> None:
        self._slots_by_office[office_id] = slots


class InMemoryObservationRepository:
    def __init__(self) -> None:
        self.records: list[tuple[uuid.UUID, Slot, datetime]] = []

    async def record_sweep(
        self,
        sweep_id: uuid.UUID,
        slots: Sequence[Slot],
        observed_at: datetime,
    ) -> None:
        for slot in slots:
            self.records.append((sweep_id, slot, observed_at))

    async def latest_slot_times(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> set[datetime]:
        matching = [
            (sweep_id, slot)
            for sweep_id, slot, _ in self.records
            if slot.office == office and slot.transaction_type == transaction_type
        ]
        if not matching:
            return set()
        newest_sweep = matching[-1][0]
        return {slot.starts_at for sweep_id, slot in matching if sweep_id == newest_sweep}


class FakeCodeValidator:
    def __init__(self, state_code: str, result: CodeCheck) -> None:
        self._state_code = state_code
        self._result = result
        self.checked: list[str] = []

    @property
    def state_code(self) -> str:
        return self._state_code

    async def check(self, access_code: str) -> CodeCheck:
        self.checked.append(access_code)
        return self._result


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


class InMemoryWatchRepository:
    def __init__(self) -> None:
        self.watches: dict[uuid.UUID, dict[str, object]] = {}
        self.credentials: dict[uuid.UUID, EncryptedCode] = {}
        self.mutes: list[tuple[uuid.UUID, str]] = []

    async def create(
        self,
        email: str,
        state_code: str,
        transaction_type: TransactionType,
        encrypted_code: EncryptedCode,
        created_at: datetime,
    ) -> uuid.UUID:
        watch_id = uuid.uuid4()
        self.watches[watch_id] = {
            "email": email,
            "state_code": state_code,
            "transaction_type": transaction_type,
            "status": WatchStatus.PENDING_CONFIRMATION,
            "created_at": created_at,
        }
        self.credentials[watch_id] = encrypted_code
        return watch_id

    async def set_status(self, watch_id: uuid.UUID, status: WatchStatus) -> bool:
        if watch_id not in self.watches:
            return False
        self.watches[watch_id]["status"] = status
        return True

    async def forget_credential(self, watch_id: uuid.UUID) -> None:
        self.credentials.pop(watch_id, None)

    async def mute_office(self, watch_id: uuid.UUID, office_id: str, muted_at: datetime) -> None:
        self.mutes.append((watch_id, office_id))
