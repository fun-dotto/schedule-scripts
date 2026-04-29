"""subjects テーブルから (syllabus_id, name) を読み、授業名と照合してレコードの lessonId を埋める。"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from sqlalchemy import text
from sqlalchemy.engine import Engine

# 曖昧一致: これ未満は採用しない
FUZZY_MIN_RATIO = 0.88
# 1位と2位の差がこれ未満なら「どちらか不明」として棄却
FUZZY_MIN_GAP = 0.04

# ポータル側に付く「旧科目名」注釈
_LEGACY_SUFFIX = re.compile(r"（旧[:：][^）]*）|\(旧[:：][^)]*\)")


def normalize_for_match(s: str) -> str:
    """比較用: 互換文字の統一・連続空白の圧縮。"""
    t = unicodedata.normalize("NFKC", s).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def strip_legacy_annotation(s: str) -> str:
    """（旧:…）をすべて除去して前後空白を整える。"""
    t = _LEGACY_SUFFIX.sub("", s)
    return t.strip()


def load_name_maps(engine: Engine) -> tuple[dict[str, int], dict[str, int]]:
    """
    subjects テーブルの (syllabus_id, name) から:
    exact: name 原文 -> syllabus_id（先勝ち）
    normalized: normalize_for_match(name) -> syllabus_id（先勝ち、重複 id は警告）
    """
    exact: dict[str, int] = {}
    normalized: dict[str, int] = {}
    sql = text(
        "SELECT syllabus_id, name FROM subjects "
        "WHERE syllabus_id IS NOT NULL AND name IS NOT NULL "
        "ORDER BY syllabus_id, name"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).all()
    for row in rows:
        raw_id = row.syllabus_id
        if raw_id is None:
            continue
        try:
            sid = int(raw_id)
        except (TypeError, ValueError):
            continue
        name = (row.name or "").strip()
        if not name:
            continue

        if name in exact:
            if exact[name] != sid:
                print(
                    f"警告: subjects で同一 name に複数 syllabus_id（先勝ち {exact[name]}、無視 {sid}）: {name!r}",
                    file=sys.stderr,
                )
        else:
            exact[name] = sid

        key = normalize_for_match(name)
        if key in normalized:
            if normalized[key] != sid:
                print(
                    f"警告: 正規化キーが衝突（先勝ち id={normalized[key]}、無視 id={sid}）: {key!r}",
                    file=sys.stderr,
                )
        else:
            normalized[key] = sid

    return exact, normalized


def fuzzy_pick_id(query_norm: str, normalized: dict[str, int]) -> int | None:
    """正規化済みクエリに最も近い subjects 由来のキー 1 件を選ぶ。自信がなければ None。"""
    if not query_norm:
        return None
    best_key: str | None = None
    best_ratio = 0.0
    second_ratio = 0.0
    for cand_key in normalized:
        r = SequenceMatcher(None, query_norm, cand_key).ratio()
        if r > best_ratio:
            second_ratio = best_ratio
            best_ratio = r
            best_key = cand_key
        elif r > second_ratio:
            second_ratio = r
    if best_key is None:
        return None
    if best_ratio < FUZZY_MIN_RATIO:
        return None
    if (best_ratio - second_ratio) < FUZZY_MIN_GAP:
        return None
    return normalized[best_key]


def resolve_lesson_id(
    lesson_name: str,
    exact: dict[str, int],
    normalized: dict[str, int],
    *,
    use_fuzzy: bool,
) -> tuple[int | None, str]:
    """
    (lesson_id or None, マッチ種別)
    種別: exact | normalized | legacy_then_normalized | fuzzy | none
    """
    raw = lesson_name.strip() if isinstance(lesson_name, str) else str(lesson_name).strip()

    if raw in exact:
        return exact[raw], "exact"

    key = normalize_for_match(raw)
    if key in normalized:
        return normalized[key], "normalized"

    stripped = strip_legacy_annotation(raw)
    key2 = normalize_for_match(stripped)
    if key2 in normalized:
        return normalized[key2], "legacy_then_normalized"

    if use_fuzzy:
        lid = fuzzy_pick_id(key2, normalized)
        if lid is not None:
            return lid, "fuzzy"

    return None, "none"


@dataclass
class FillLessonIdsResult:
    matched: int
    total: int
    kind_counts: dict[str, int] = field(default_factory=dict)
    unmatched_names: list[str] = field(default_factory=list)


def fill_lesson_ids_in_records(
    records: list[dict],
    name_maps: tuple[dict[str, int], dict[str, int]],
    *,
    use_fuzzy: bool = True,
    verbose: bool = False,
) -> FillLessonIdsResult:
    """
    records を in-place で更新し、lessonName から lessonId を設定する。
    一致しない場合は lessonId を変更しない（取得時の 0 のまま）。
    name_maps は load_name_maps の戻り値 (exact, normalized) を渡す。
    """
    exact, normalized = name_maps
    matched = 0
    unmatched_names: list[str] = []
    kind_counts: dict[str, int] = {}

    for item in records:
        name = item.get("lessonName", "")
        lid, kind = resolve_lesson_id(
            name if isinstance(name, str) else str(name),
            exact,
            normalized,
            use_fuzzy=use_fuzzy,
        )
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if verbose:
            display = name if isinstance(name, str) else str(name)
            print(f"[{kind}] {display!r} -> {lid}", file=sys.stderr)

        if lid is not None:
            item["lessonId"] = lid
            matched += 1
        else:
            unmatched_names.append(name.strip() if isinstance(name, str) else str(name))

    return FillLessonIdsResult(
        matched=matched,
        total=len(records),
        kind_counts=kind_counts,
        unmatched_names=unmatched_names,
    )
