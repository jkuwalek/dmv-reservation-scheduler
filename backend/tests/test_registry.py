from collections.abc import Sequence

import pytest

from dmvwatch.adapters.states.registry import StateRegistry, UnsupportedState
from dmvwatch.domain.models import Office, Slot, TransactionType


class StubSource:
    state_code = "ZZ"

    def offices(self) -> Sequence[Office]:
        return [Office(state_code="ZZ", office_id="1", name="Test Office")]

    def available_slots(
        self,
        office: Office,
        transaction_type: TransactionType,
    ) -> Sequence[Slot]:
        return []


def test_a_registered_state_can_be_resolved() -> None:
    registry = StateRegistry()
    registry.register("ZZ", StubSource)
    assert registry.create("ZZ").state_code == "ZZ"


def test_state_codes_are_case_insensitive() -> None:
    registry = StateRegistry()
    registry.register("ZZ", StubSource)
    assert registry.create("zz").state_code == "ZZ"


def test_an_unregistered_state_raises() -> None:
    registry = StateRegistry()
    with pytest.raises(UnsupportedState, match="QQ"):
        registry.create("QQ")


def test_supported_states_are_listed_sorted() -> None:
    registry = StateRegistry()
    registry.register("ZZ", StubSource)
    registry.register("AA", StubSource)
    assert registry.supported() == ["AA", "ZZ"]
