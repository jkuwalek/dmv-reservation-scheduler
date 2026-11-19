import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dmvwatch.adapters.db.observations import SqlObservationRepository
from dmvwatch.adapters.db.tables import Base
from dmvwatch.domain.models import Office, Slot, TransactionType

docker = pytest.importorskip("testcontainers.postgres")

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
PERMIT = TransactionType.PERMIT_LICENSE_ID
BROOKLYN = Office(state_code="NY", office_id="7001", name="Office 7001")


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    try:
        container = docker.PostgresContainer("postgres:17-alpine", driver="asyncpg")
        container.start()
    except Exception as exc:  # usually just a stopped docker daemon
        pytest.skip(f"docker unavailable: {exc}")

    try:
        engine = create_async_engine(container.get_connection_url())
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as open_session:
            yield open_session
        await engine.dispose()
    finally:
        container.stop()


def _slot(hours_ahead: int) -> Slot:
    return Slot(
        office=BROOKLYN,
        transaction_type=PERMIT,
        starts_at=NOW + timedelta(hours=hours_ahead),
    )


async def test_a_recorded_sweep_can_be_read_back(session: AsyncSession) -> None:
    repo = SqlObservationRepository(session)
    await repo.record_sweep(uuid.uuid4(), [_slot(24), _slot(48)], observed_at=NOW)
    assert await repo.latest_slot_times(BROOKLYN, PERMIT) == {
        NOW + timedelta(hours=24),
        NOW + timedelta(hours=48),
    }


async def test_only_the_most_recent_sweep_counts(session: AsyncSession) -> None:
    repo = SqlObservationRepository(session)
    await repo.record_sweep(uuid.uuid4(), [_slot(24)], observed_at=NOW)
    await repo.record_sweep(uuid.uuid4(), [_slot(72)], observed_at=NOW + timedelta(minutes=5))
    assert await repo.latest_slot_times(BROOKLYN, PERMIT) == {NOW + timedelta(hours=72)}


async def test_an_office_never_swept_has_no_history(session: AsyncSession) -> None:
    repo = SqlObservationRepository(session)
    other = Office(state_code="NY", office_id="7002", name="Office 7002")
    assert await repo.latest_slot_times(other, PERMIT) == set()
