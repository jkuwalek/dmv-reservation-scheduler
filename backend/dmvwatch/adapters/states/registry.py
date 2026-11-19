"""Maps a state code to the adapter that knows how to read its booking system.

Supporting another state means writing an adapter and registering it here. Nothing in
the domain or the services changes.
"""

from collections.abc import Callable

from dmvwatch.domain.protocols import SlotSource


class UnsupportedState(LookupError):
    pass


class StateRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], SlotSource]] = {}

    def register(self, state_code: str, factory: Callable[[], SlotSource]) -> None:
        self._factories[state_code.upper()] = factory

    def create(self, state_code: str) -> SlotSource:
        try:
            factory = self._factories[state_code.upper()]
        except KeyError:
            raise UnsupportedState(state_code.upper()) from None
        return factory()

    def supported(self) -> list[str]:
        return sorted(self._factories)
