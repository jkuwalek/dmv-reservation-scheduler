import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from dmvwatch.adapters.db.tables import Credential, Watch, WatchOfficeMute
from dmvwatch.domain.models import TransactionType, WatchStatus
from dmvwatch.security.codes import EncryptedCode


class SqlWatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        email: str,
        state_code: str,
        transaction_type: TransactionType,
        encrypted_code: EncryptedCode,
        created_at: datetime,
    ) -> uuid.UUID:
        watch = Watch(
            email=email,
            state_code=state_code,
            transaction_type=transaction_type.value,
            status=WatchStatus.PENDING_CONFIRMATION.value,
            created_at=created_at,
            notified_count=0,
        )
        self._session.add(watch)
        await self._session.flush()
        self._session.add(
            Credential(
                watch_id=watch.id,
                ciphertext=encrypted_code.ciphertext,
                nonce=encrypted_code.nonce,
                key_version=encrypted_code.key_version,
                created_at=created_at,
            )
        )
        await self._session.commit()
        return watch.id

    async def status_of(self, watch_id: uuid.UUID) -> WatchStatus | None:
        rows = await self._session.execute(select(Watch.status).where(Watch.id == watch_id))
        value = rows.scalar_one_or_none()
        return None if value is None else WatchStatus(value)

    async def set_status(self, watch_id: uuid.UUID, status: WatchStatus) -> bool:
        watch = await self._session.get(Watch, watch_id)
        if watch is None:
            return False
        watch.status = status.value
        await self._session.commit()
        return True

    async def forget_credential(self, watch_id: uuid.UUID) -> None:
        await self._session.execute(delete(Credential).where(Credential.watch_id == watch_id))
        await self._session.commit()

    async def mute_office(
        self, watch_id: uuid.UUID, office_id: str, muted_at: datetime
    ) -> None:
        statement = (
            insert(WatchOfficeMute)
            .values(
                id=uuid.uuid4(),
                watch_id=watch_id,
                office_id=office_id,
                muted_at=muted_at,
            )
            .on_conflict_do_nothing(index_elements=["watch_id", "office_id"])
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def muted_offices(self, watch_id: uuid.UUID) -> set[str]:
        rows = await self._session.execute(
            select(WatchOfficeMute.office_id).where(WatchOfficeMute.watch_id == watch_id)
        )
        return set(rows.scalars().all())
