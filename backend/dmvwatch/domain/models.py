"""Core types. Nothing here may import a framework or touch I/O."""

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
