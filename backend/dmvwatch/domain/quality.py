"""Checks every scraped slot before it is allowed downstream.

A scraper that silently returns nothing when a page layout changes is worse than one
that fails loudly, so rejects are counted and reported rather than dropped.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from dmvwatch.domain.models import Slot


@dataclass(frozen=True, slots=True)
class Rejection:
    slot: Slot
    reason: str


class SlotValidator:
    def __init__(self, known_office_ids: frozenset[str]) -> None:
        self._known_office_ids = known_office_ids

    def reason_to_reject(self, slot: Slot, now: datetime) -> str | None:
        if slot.starts_at.tzinfo is None:
            return "naive_datetime"
        if slot.starts_at <= now:
            return "slot_in_past"
        if slot.office.office_id not in self._known_office_ids:
            return "unknown_office"
        return None


def partition(
    slots: Iterable[Slot],
    validator: SlotValidator,
    now: datetime,
) -> tuple[list[Slot], list[Rejection]]:
    accepted: list[Slot] = []
    rejected: list[Rejection] = []
    for slot in slots:
        reason = validator.reason_to_reject(slot, now=now)
        if reason is None:
            accepted.append(slot)
        else:
            rejected.append(Rejection(slot=slot, reason=reason))
    return accepted, rejected
