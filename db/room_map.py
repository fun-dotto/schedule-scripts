"""rooms.name から部屋 UUID を引き、部屋変更レコードに original_room_id / new_room_id を付与する。"""

from __future__ import annotations

import re
import sys
import unicodedata
import uuid
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine

_SPACE_RE = re.compile(r"\s+")


def normalize_room_name(s: str) -> str:
    """照合用キー: NFKC・連続空白の圧縮・前後空白除去・大文字小文字無視。"""
    t = unicodedata.normalize("NFKC", s)
    t = t.strip()
    t = t.replace("\u3000", " ").replace("\xa0", " ")
    t = _SPACE_RE.sub(" ", t).strip()
    return t.casefold()


def load_room_name_to_id_map(engine: Engine) -> dict[str, uuid.UUID]:
    """
    rooms テーブルから name -> id の対応を読む（照合キーは normalize_room_name）。
    正規化後に同一キーが複数行ある場合は先勝ちし、stderr に警告する。
    """
    out: dict[str, uuid.UUID] = {}
    sql = text("SELECT id, name FROM rooms WHERE name IS NOT NULL")
    with engine.connect() as conn:
        rows = conn.execute(sql).all()
    for row in rows:
        raw = row.name
        if raw is None:
            continue
        key = normalize_room_name(str(raw))
        if not key:
            continue
        uid = row.id
        if isinstance(uid, str):
            uid = uuid.UUID(uid)
        elif not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(str(uid))
        if key in out:
            if out[key] != uid:
                print(
                    f"警告: rooms で正規化後同一キー {key!r} に複数 id（先勝ち {out[key]}、無視 {uid}）",
                    file=sys.stderr,
                )
        else:
            out[key] = uid
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
    照合は normalize_room_name で広げたキーで行う。未一致ログは元の文字列（strip 後）を出す。
    """
    matched_from = 0
    matched_to = 0
    eligible_from = 0
    eligible_to = 0
    unmatched: set[str] = set()

    for item in records:
        rf = item.get("roomFrom")
        rt = item.get("roomTo")
        if isinstance(rf, str):
            display_f = rf.strip()
            key_f = normalize_room_name(rf)
            if key_f:
                eligible_from += 1
                uid = name_to_room_id.get(key_f)
                if uid is not None:
                    item["original_room_id"] = str(uid)
                    matched_from += 1
                else:
                    unmatched.add(display_f)
        if isinstance(rt, str):
            display_t = rt.strip()
            key_t = normalize_room_name(rt)
            if key_t:
                eligible_to += 1
                uid = name_to_room_id.get(key_t)
                if uid is not None:
                    item["new_room_id"] = str(uid)
                    matched_to += 1
                else:
                    unmatched.add(display_t)

    return FillRoomIdsResult(
        matched_from=matched_from,
        matched_to=matched_to,
        eligible_from=eligible_from,
        eligible_to=eligible_to,
        total=len(records),
        unmatched_names=sorted(unmatched),
    )
