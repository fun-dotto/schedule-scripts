"""既存テーブル（cancelled_classes, makeup_classes, room_changes）への ORM マッピング。"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

PgUUID = UUID(as_uuid=True)


class Base(DeclarativeBase):
    pass


class CancelledClass(Base):
    __tablename__ = "cancelled_classes"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID, primary_key=True, insert_default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MakeupClasses(Base):
    __tablename__ = "makeup_classes"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID, primary_key=True, insert_default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoomChange(Base):
    __tablename__ = "room_changes"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID, primary_key=True, insert_default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    original_room_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False)
    new_room_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
