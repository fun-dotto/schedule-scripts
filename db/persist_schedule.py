"""スクレイプ結果を ORM モデルへ保存（必須欠落はスキップ、自然キー重複は挿入しない）。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import CancelledClass, MakeupClasses, RoomChange


def _parse_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return uuid.UUID(value.strip())
        except ValueError:
            return None
    return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def partition_cancelled_or_makeup(records: list[dict]) -> tuple[list[dict], list[dict]]:
    eligible: list[dict] = []
    skipped: list[dict] = []
    for r in records:
        if (
            _parse_uuid(r.get("subject_id")) is not None
            and _parse_date(r.get("date")) is not None
            and _non_empty_str(r.get("period"))
        ):
            eligible.append(r)
        else:
            skipped.append(r)
    return eligible, skipped


def partition_room_changes(records: list[dict]) -> tuple[list[dict], list[dict]]:
    eligible: list[dict] = []
    skipped: list[dict] = []
    for r in records:
        if (
            _parse_uuid(r.get("subject_id")) is not None
            and _parse_date(r.get("date")) is not None
            and _non_empty_str(r.get("period"))
            and _parse_uuid(r.get("original_room_id")) is not None
            and _parse_uuid(r.get("new_room_id")) is not None
        ):
            eligible.append(r)
        else:
            skipped.append(r)
    return eligible, skipped


def _normalize_comment(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        t = value.strip()
        return t or None
    return None


@dataclass(frozen=True)
class PersistStats:
    inserted: int
    duplicates: int


def persist_cancelled(session: Session, records: list[dict]) -> PersistStats:
    inserted = 0
    duplicates = 0
    seen: set[tuple[uuid.UUID, date, str]] = set()
    for r in records:
        sid = _parse_uuid(r["subject_id"])
        d = _parse_date(r["date"])
        assert sid is not None and d is not None
        period = str(r["period"]).strip()
        key = (sid, d, period)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        exists = session.scalar(
            select(CancelledClass.id).where(
                CancelledClass.subject_id == sid,
                CancelledClass.date == d,
                CancelledClass.period == period,
            ).limit(1)
        )
        if exists is not None:
            duplicates += 1
            continue
        session.add(
            CancelledClass(
                subject_id=sid,
                date=d,
                period=period,
                comment=_normalize_comment(r.get("comment")),
            )
        )
        inserted += 1
    return PersistStats(inserted, duplicates)


def persist_makeup(session: Session, records: list[dict]) -> PersistStats:
    inserted = 0
    duplicates = 0
    seen: set[tuple[uuid.UUID, date, str]] = set()
    for r in records:
        sid = _parse_uuid(r["subject_id"])
        d = _parse_date(r["date"])
        assert sid is not None and d is not None
        period = str(r["period"]).strip()
        key = (sid, d, period)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        exists = session.scalar(
            select(MakeupClasses.id).where(
                MakeupClasses.subject_id == sid,
                MakeupClasses.date == d,
                MakeupClasses.period == period,
            ).limit(1)
        )
        if exists is not None:
            duplicates += 1
            continue
        session.add(
            MakeupClasses(
                subject_id=sid,
                date=d,
                period=period,
                comment=_normalize_comment(r.get("comment")),
            )
        )
        inserted += 1
    return PersistStats(inserted, duplicates)


def persist_room_changes(session: Session, records: list[dict]) -> PersistStats:
    inserted = 0
    duplicates = 0
    seen: set[tuple[uuid.UUID, date, str, uuid.UUID, uuid.UUID]] = set()
    for r in records:
        sid = _parse_uuid(r["subject_id"])
        d = _parse_date(r["date"])
        period = str(r["period"]).strip()
        orig = _parse_uuid(r["original_room_id"])
        new = _parse_uuid(r["new_room_id"])
        assert sid is not None and d is not None and orig is not None and new is not None
        key = (sid, d, period, orig, new)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        exists = session.scalar(
            select(RoomChange.id).where(
                RoomChange.subject_id == sid,
                RoomChange.date == d,
                RoomChange.period == period,
                RoomChange.original_room_id == orig,
                RoomChange.new_room_id == new,
            ).limit(1)
        )
        if exists is not None:
            duplicates += 1
            continue
        session.add(
            RoomChange(
                subject_id=sid,
                date=d,
                period=period,
                original_room_id=orig,
                new_room_id=new,
            )
        )
        inserted += 1
    return PersistStats(inserted, duplicates)
