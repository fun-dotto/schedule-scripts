from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


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


def load_name_maps(csv_path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """
    exact: CSV の name 原文 -> id（先勝ち）
    normalized: normalize_for_match(name) -> id（先勝ち、重複 id は警告）
    """
    exact: dict[str, int] = {}
    normalized: dict[str, int] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            raw_id = row.get("id") or row.get("syllabus_id")
            if raw_id is None or str(raw_id).strip() == "":
                continue
            sid = int(str(raw_id).strip())

            if name in exact:
                if exact[name] != sid:
                    print(
                        f"警告: CSV で同一 name に複数 id（先勝ち {exact[name]}、無視 {sid}）: {name!r}",
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
    """正規化済みクエリに最も近い CSV 側キー 1 件を選ぶ。自信がなければ None。"""
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
    種別: exact | normalized | legacy_then_normalized | fuzzy
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


def main() -> None:
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="classification_result と cancel_lecture を照合して lessonId を埋める")
    p.add_argument(
        "--csv",
        type=Path,
        default=root / "classification_result.csv",
        help="id,name 列を持つ CSV（デフォルト: リポジトリ直下）",
    )
    p.add_argument(
        "--input",
        type=Path,
        default=root / "cancel_lecture.json",
        help="入力 JSON（デフォルト: cancel_lecture.json）",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "cancel_lecture_with_lesson_id.json",
        help="出力 JSON",
    )
    p.add_argument(
        "--no-fuzzy",
        action="store_true",
        help="曖昧一致（difflib）を使わない（正規化・（旧:）除去までのみ）",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="各レコードのマッチ種別を stderr に出す",
    )
    args = p.parse_args()

    exact, normalized = load_name_maps(args.csv)
    use_fuzzy = not args.no_fuzzy

    with args.input.open(encoding="utf-8") as f:
        records: list[dict] = json.load(f)

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
        if args.verbose:
            display = name if isinstance(name, str) else str(name)
            print(f"[{kind}] {display!r} -> {lid}", file=sys.stderr)

        if lid is not None:
            item["lessonId"] = lid
            matched += 1
        else:
            unmatched_names.append(name.strip() if isinstance(name, str) else str(name))

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")

    uniq_unmatched = sorted(set(unmatched_names))
    print(f"レコード数: {len(records)}")
    print(f"一致して lessonId を設定: {matched}")
    print(f"未一致（lessonId は元のまま）: {len(records) - matched}")
    print("内訳:", ", ".join(f"{k}={v}" for k, v in sorted(kind_counts.items())))
    if uniq_unmatched:
        print("未一致の lessonName（ユニーク、最大20件）:")
        for n in uniq_unmatched[:20]:
            print(f"  - {n!r}")
        if len(uniq_unmatched) > 20:
            print(f"  ... 他 {len(uniq_unmatched) - 20} 件")
    print(f"出力: {args.output}")


if __name__ == "__main__":
    main()
