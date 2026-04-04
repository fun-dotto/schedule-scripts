"""休講・補講・部屋変更のテーブル定義。

GORM の CourseRegistration 相当（UUID の id / subject_id、対象日付、CreatedAt / UpdatedAt）に揃える。
CreatedAt / UpdatedAt は DB の now() と ORM の onupdate で GORM に近い自動更新とする。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# PostgreSQL の UUID（Python 側は uuid.UUID）
PgUUID = UUID(as_uuid=True)


class Base(DeclarativeBase):
    pass


class CancelledClass(Base):
    """休講（科目 UUID・対象日付・時限テキスト・休講教室 UUID）。"""

    __tablename__ = "cancelled_classes"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, primary_key=True, insert_default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class MakeupClasses(Base):
    """補講（科目 UUID・対象日付・時限テキスト・補講教室 UUID）。"""

    __tablename__ = "makeup_classes"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, primary_key=True, insert_default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class RoomChange(Base):
    """部屋変更（科目 UUID・時限テキスト・変更後の部屋 UUID）。"""

    __tablename__ = "room_changes"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, primary_key=True, insert_default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID, nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    original_room_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False, index=True)
    new_room_id: Mapped[uuid.UUID] = mapped_column(PgUUID, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
