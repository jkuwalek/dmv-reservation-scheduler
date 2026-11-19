import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dmvwatch.adapters.db.tables import Base, Credential
from dmvwatch.adapters.db.watches import SqlWatchRepository
from dmvwatch.domain.models import TransactionType, WatchStatus
from dmvwatch.security.codes import EncryptedCode

docker = pytest.importorskip("testcontainers.postgres")

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
BLOB = EncryptedCode(ciphertext=b"cipher", nonce=b"nonce", key_version=1)


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


async def _new_watch(repo: SqlWatchRepository) -> uuid.UUID:
    return await repo.create(
        email="a@example.com",
        state_code="NY",
        transaction_type=TransactionType.PERMIT_LICENSE_ID,
        encrypted_code=BLOB,
        created_at=NOW,
    )


async def test_a_created_watch_starts_pending(session: AsyncSession) -> None:
    repo = SqlWatchRepository(session)
    watch_id = await _new_watch(repo)
    assert await repo.status_of(watch_id) is WatchStatus.PENDING_CONFIRMATION


async def test_the_credential_is_stored_alongside(session: AsyncSession) -> None:
    repo = SqlWatchRepository(session)
    watch_id = await _new_watch(repo)
    rows = await session.execute(select(Credential).where(Credential.watch_id == watch_id))
    stored = rows.scalar_one()
    assert stored.ciphertext == b"cipher"
    assert stored.key_version == 1


async def test_status_can_be_advanced(session: AsyncSession) -> None:
    repo = SqlWatchRepository(session)
    watch_id = await _new_watch(repo)
    assert await repo.set_status(watch_id, WatchStatus.ACTIVE) is True
    assert await repo.status_of(watch_id) is WatchStatus.ACTIVE


async def test_advancing_a_watch_that_does_not_exist_reports_failure(
    session: AsyncSession,
) -> None:
    repo = SqlWatchRepository(session)
    assert await repo.set_status(uuid.uuid4(), WatchStatus.ACTIVE) is False


async def test_forgetting_the_credential_removes_only_the_credential(
    session: AsyncSession,
) -> None:
    repo = SqlWatchRepository(session)
    watch_id = await _new_watch(repo)
    await repo.forget_credential(watch_id)
    rows = await session.execute(select(Credential).where(Credential.watch_id == watch_id))
    assert rows.scalar_one_or_none() is None
    assert await repo.status_of(watch_id) is WatchStatus.PENDING_CONFIRMATION


async def test_muting_the_same_office_twice_is_harmless(session: AsyncSession) -> None:
    repo = SqlWatchRepository(session)
    watch_id = await _new_watch(repo)
    await repo.mute_office(watch_id, "7002", NOW)
    await repo.mute_office(watch_id, "7002", NOW)
    assert await repo.muted_offices(watch_id) == {"7002"}
