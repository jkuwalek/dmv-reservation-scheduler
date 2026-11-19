"""Database schema.

Mapped separately from the domain types on purpose: the domain should not acquire an
ORM dependency just to be persisted.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Watch(Base):
    __tablename__ = "watch"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    state_code: Mapped[str] = mapped_column(String(2))
    transaction_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notified_count: Mapped[int] = mapped_column(Integer, default=0)


class WatchOfficeMute(Base):
    """One row per office a watcher has asked to stop hearing about."""

    __tablename__ = "watch_office_mute"
    __table_args__ = (UniqueConstraint("watch_id", "office_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watch.id", ondelete="CASCADE"), index=True
    )
    office_id: Mapped[str] = mapped_column(String(32))
    muted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Credential(Base):
    """Encrypted access codes, kept apart so they can be purged on their own."""

    __tablename__ = "credential"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watch.id", ondelete="CASCADE"), unique=True
    )
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    key_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SlotObservation(Base):
    """Every sweep, including the ones that found nothing.

    Keeping the misses is what makes this a time series rather than a log.
    """

    __tablename__ = "slot_observation"
    __table_args__ = (
        Index(
            "ix_slot_observation_office_transaction_observed",
            "office_id",
            "transaction_type",
            "observed_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sweep_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), index=True)
    state_code: Mapped[str] = mapped_column(String(2))
    office_id: Mapped[str] = mapped_column(String(32))
    transaction_type: Mapped[str] = mapped_column(String(40))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    slot_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watch.id", ondelete="CASCADE"), index=True
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    slot_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    channel: Mapped[str] = mapped_column(String(16))
