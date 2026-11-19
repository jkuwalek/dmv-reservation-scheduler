"""How hard we are willing to hit a public booking system, in one place.

The throttle returns the delay a caller should wait rather than sleeping itself, which
keeps the limits unit-testable and keeps the sleeping decision with the scheduler.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from dmvwatch.domain.protocols import Clock


@dataclass(frozen=True, slots=True)
class CrawlPolicy:
    min_interval: timedelta
    max_concurrency: int
    max_attempts: int
    base_backoff: timedelta
    user_agent: str

    def backoff_for(self, attempt: int) -> timedelta:
        return self.base_backoff * (2 ** (attempt - 1))


class Throttle:
    def __init__(self, policy: CrawlPolicy, clock: Clock) -> None:
        self._policy = policy
        self._clock = clock
        self._last_request: dict[str, datetime] = {}

    def delay_before(self, host: str) -> timedelta:
        last = self._last_request.get(host)
        if last is None:
            return timedelta(0)
        elapsed = self._clock.now() - last
        return max(self._policy.min_interval - elapsed, timedelta(0))

    def record(self, host: str) -> None:
        self._last_request[host] = self._clock.now()
