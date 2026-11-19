"""Core types. Nothing here may import a framework or touch I/O."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TransactionType(StrEnum):
    PERMIT_LICENSE_ID = "permit_license_id"
    ROAD_TEST = "road_test"
    VEHICLE_REGISTRATION = "vehicle_registration"


@dataclass(frozen=True, slots=True)
class Office:
    state_code: str
    office_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Slot:
    office: Office
    transaction_type: TransactionType
    starts_at: datetime


class WatchStatus(StrEnum):
    PENDING_CONFIRMATION = "pending_confirmation"
    ACTIVE = "active"
    NOTIFIED = "notified"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class SweepResult:
    office: Office
    seen: Sequence[Slot]
    newly_available: Sequence[Slot]
    rejected: Mapping[str, int]

    @property
    def worth_notifying(self) -> bool:
        return bool(self.newly_available)
