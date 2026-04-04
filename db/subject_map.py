"""subjects.syllabus_id から subject の UUID を引き、レコードに subject_id を付与する。"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_syllabus_to_subject_id_map(engine: Engine) -> dict[int, uuid.UUID]:
    """
    subjects テーブルから syllabus_id -> id の対応を読む。
    同一 syllabus_id が複数行ある場合は先勝ちし、stderr に警告する。
    """
    out: dict[int, uuid.UUID] = {}
    sql = text("SELECT id, syllabus_id FROM subjects WHERE syllabus_id IS NOT NULL")
    with engine.connect() as conn:
        rows = conn.execute(sql).all()
    for row in rows:
        sid_raw = row.syllabus_id
        if sid_raw is None:
            continue
        try:
            syllabus_id = int(sid_raw)
        except (TypeError, ValueError):
            continue
        uid = row.id
        if isinstance(uid, str):
            uid = uuid.UUID(uid)
        elif not isinstance(uid, uuid.UUID):
            uid = uuid.UUID(str(uid))
        if syllabus_id in out:
            if out[syllabus_id] != uid:
                print(
                    f"警告: subjects で同一 syllabus_id={syllabus_id} に複数 id（先勝ち {out[syllabus_id]}、無視 {uid}）",
                    file=sys.stderr,
                )
        else:
            out[syllabus_id] = uid
    return out


@dataclass
class FillSubjectIdsResult:
    matched: int
    eligible: int
    total: int
    unmatched_lesson_ids: list[int] = field(default_factory=list)


def fill_subject_ids_in_records(
    records: list[dict],
    syllabus_to_subject: dict[int, uuid.UUID],
) -> FillSubjectIdsResult:
    """
    lessonId（シラバス ID）が正のとき、syllabus_to_subject で subject_id（UUID 文字列）を設定する。
    一致しない lessonId は unmatched_lesson_ids に集約（重複は除く）。
    """
    matched = 0
    eligible = 0
    unmatched_set: set[int] = set()

    for item in records:
        lid = item.get("lessonId")
        if lid is None:
            continue
        try:
            n = int(lid)
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        eligible += 1
        uid = syllabus_to_subject.get(n)
        if uid is not None:
            item["subject_id"] = str(uid)
            matched += 1
        else:
            unmatched_set.add(n)

    return FillSubjectIdsResult(
        matched=matched,
        eligible=eligible,
        total=len(records),
        unmatched_lesson_ids=sorted(unmatched_set),
    )
