"""rooms.name から部屋 UUID を引き、部屋変更レコードに original_room_id / new_room_id を付与する。"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_room_name_to_id_map(engine: Engine) -> dict[str, uuid.UUID]:
    """
    rooms テーブルから name -> id の対応を読む。
    同一 name が複数行ある場合は先勝ちし、stderr に警告する。
    """
    out: dict[str, uuid.UUID] = {}
    sql = text("SELECT id, name FROM rooms WHERE name IS NOT NULL")
    with engine.connect() as conn:
        rows = conn.execute(sql).all()
    for row in rows:
        raw = row.name
        if raw is None:
            continue
        name = str(raw).strip()
        if not name:
            continue
        uid = row.id
        if isinstance(uid, str):
            uid = uuid.UUID(uid)
        elif not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(str(uid))
        if name in out:
            if out[name] != uid:
                print(
                    f"警告: rooms で同一 name={name!r} に複数 id（先勝ち {out[name]}、無視 {uid}）",
                    file=sys.stderr,
                )
        else:
            out[name] = uid
    return out


@dataclass
class FillRoomIdsResult:
    matched_from: int
    matched_to: int
    eligible_from: int
    eligible_to: int
    total: int
    unmatched_names: list[str] = field(default_factory=list)


def fill_room_ids_in_room_changes(
    records: list[dict],
    name_to_room_id: dict[str, uuid.UUID],
) -> FillRoomIdsResult:
    """
    roomFrom / roomTo を rooms.name と照合し、original_room_id / new_room_id（UUID 文字列）を設定する。
    """
    matched_from = 0
    matched_to = 0
    eligible_from = 0
    eligible_to = 0
    unmatched: set[str] = set()

    for item in records:
        rf = item.get("roomFrom")
        rt = item.get("roomTo")
        if isinstance(rf, str) and rf.strip():
            eligible_from += 1
            key = rf.strip()
            uid = name_to_room_id.get(key)
            if uid is not None:
                item["original_room_id"] = str(uid)
                matched_from += 1
            else:
                unmatched.add(key)
        if isinstance(rt, str) and rt.strip():
            eligible_to += 1
            key = rt.strip()
            uid = name_to_room_id.get(key)
            if uid is not None:
                item["new_room_id"] = str(uid)
                matched_to += 1
            else:
                unmatched.add(key)

    return FillRoomIdsResult(
        matched_from=matched_from,
        matched_to=matched_to,
        eligible_from=eligible_from,
        eligible_to=eligible_to,
        total=len(records),
        unmatched_names=sorted(unmatched),
    )
