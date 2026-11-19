from datetime import UTC, datetime, timedelta

from dmvwatch.crawl.policy import CrawlPolicy, Throttle

POLICY = CrawlPolicy(
    min_interval=timedelta(seconds=30),
    max_concurrency=2,
    max_attempts=4,
    base_backoff=timedelta(seconds=5),
    user_agent="dmvwatch/0.1 (+https://github.com/jkuwalek/dmv-reservation-scheduler)",
)


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


def test_backoff_doubles_with_each_attempt() -> None:
    assert POLICY.backoff_for(attempt=1) == timedelta(seconds=5)
    assert POLICY.backoff_for(attempt=2) == timedelta(seconds=10)
    assert POLICY.backoff_for(attempt=3) == timedelta(seconds=20)


def test_the_first_request_to_a_host_is_not_delayed() -> None:
    clock = FakeClock(datetime(2026, 11, 19, 12, 0, tzinfo=UTC))
    throttle = Throttle(policy=POLICY, clock=clock)
    assert throttle.delay_before("dmv.ny.gov") == timedelta(0)


def test_a_second_request_too_soon_is_delayed_by_the_remainder() -> None:
    clock = FakeClock(datetime(2026, 11, 19, 12, 0, tzinfo=UTC))
    throttle = Throttle(policy=POLICY, clock=clock)
    throttle.record("dmv.ny.gov")
    clock.advance(timedelta(seconds=10))
    assert throttle.delay_before("dmv.ny.gov") == timedelta(seconds=20)


def test_no_delay_once_the_interval_has_elapsed() -> None:
    clock = FakeClock(datetime(2026, 11, 19, 12, 0, tzinfo=UTC))
    throttle = Throttle(policy=POLICY, clock=clock)
    throttle.record("dmv.ny.gov")
    clock.advance(timedelta(seconds=31))
    assert throttle.delay_before("dmv.ny.gov") == timedelta(0)


def test_hosts_are_throttled_independently() -> None:
    clock = FakeClock(datetime(2026, 11, 19, 12, 0, tzinfo=UTC))
    throttle = Throttle(policy=POLICY, clock=clock)
    throttle.record("dmv.ny.gov")
    assert throttle.delay_before("dmv.ca.gov") == timedelta(0)
