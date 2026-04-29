import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from dotto_batch_jobs.db.engine import get_engine
from dotto_batch_jobs.db.persist_schedule import (
    partition_cancelled_or_makeup,
    partition_room_changes,
    persist_cancelled,
    persist_makeup,
    persist_room_changes,
)
from dotto_batch_jobs.db.room_map import fill_room_ids_in_room_changes, load_room_name_to_id_map
from dotto_batch_jobs.db.subject_map import fill_subject_ids_in_records, load_syllabus_to_subject_id_map
from dotto_batch_jobs.scrape_class_changes.lesson_ids import fill_lesson_ids_in_records, load_name_maps
from dotto_batch_jobs.scrape_class_changes.scrapers.fetch import fetch_cancel_supple
from dotto_batch_jobs.scrape_class_changes.scrapers.cancel_classes import cancelled_classes_to_dict
from dotto_batch_jobs.scrape_class_changes.scrapers.room_change import room_change_to_dict
from dotto_batch_jobs.scrape_class_changes.scrapers.makeup_classes import makeup_classes_to_dict

load_dotenv(override=False)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "output"


def main() -> None:
    cancelled_classes_list, makeup_classes_list, exchange_list = fetch_cancel_supple()
    cancelled_classes_json = [cancelled_classes_to_dict(k) for k in cancelled_classes_list]
    makeup_classes_json = [makeup_classes_to_dict(s) for s in makeup_classes_list]
    room_changes_json = [room_change_to_dict(c) for c in exchange_list]

    engine = None
    try:
        engine = get_engine()
        try:
            name_maps = load_name_maps(engine)
            r_k = fill_lesson_ids_in_records(cancelled_classes_json, name_maps)
            r_s = fill_lesson_ids_in_records(makeup_classes_json, name_maps)
            r_r = fill_lesson_ids_in_records(room_changes_json, name_maps)
            print(
                f"lessonId 照合（subjects.name） 休講: {r_k.matched}/{r_k.total} 件, "
                f"補講: {r_s.matched}/{r_s.total} 件, "
                f"部屋変更: {r_r.matched}/{r_r.total} 件"
            )
        except Exception as e:
            print(f"スキップ: lessonId 照合（{e}）", flush=True)

        syllabus_map = load_syllabus_to_subject_id_map(engine)
        sk = fill_subject_ids_in_records(cancelled_classes_json, syllabus_map)
        sm = fill_subject_ids_in_records(makeup_classes_json, syllabus_map)
        sr = fill_subject_ids_in_records(room_changes_json, syllabus_map)
        print(
            f"subject_id 付与（subjects.syllabus_id） 休講: {sk.matched}/{sk.eligible} 件（全 {sk.total}）, "
            f"補講: {sm.matched}/{sm.eligible} 件（全 {sm.total}）, "
            f"部屋変更: {sr.matched}/{sr.eligible} 件（全 {sr.total}）"
        )
        all_unmatched = sorted(set(sk.unmatched_lesson_ids + sm.unmatched_lesson_ids + sr.unmatched_lesson_ids))
        if all_unmatched:
            print(f"警告: subjects に無い lessonId（syllabus_id）: {all_unmatched}", flush=True)

        try:
            room_map = load_room_name_to_id_map(engine)
            rr = fill_room_ids_in_room_changes(room_changes_json, room_map)
            print(
                f"room_id 付与（rooms.name） 移動元: {rr.matched_from}/{rr.eligible_from} 件, "
                f"移動先: {rr.matched_to}/{rr.eligible_to} 件（部屋変更 {rr.total} 件）"
            )
            if rr.unmatched_names:
                print(f"警告: rooms に無い教室名: {rr.unmatched_names}", flush=True)
        except Exception as e:
            print(f"スキップ: room_id 付与（{e}）", flush=True)
    except RuntimeError as e:
        print(f"スキップ: subject_id 付与（{e}）", flush=True)
    except Exception as e:
        print(f"スキップ: DB 接続または subject / room 付与（{e}）", flush=True)

    elig_cancel, skip_cancel = partition_cancelled_or_makeup(cancelled_classes_json)
    elig_makeup, skip_makeup = partition_cancelled_or_makeup(makeup_classes_json)
    elig_room, skip_room = partition_room_changes(room_changes_json)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    skipped_specs = [
        ("cancelled_classes_skipped.json", skip_cancel),
        ("makeup_classes_skipped.json", skip_makeup),
        ("room_changes_skipped.json", skip_room),
    ]
    for fname, rows in skipped_specs:
        with open(OUTPUT_DIR / fname, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    if engine is not None:
        try:
            with Session(engine) as session:
                pc = persist_cancelled(session, elig_cancel)
                pm = persist_makeup(session, elig_makeup)
                pr = persist_room_changes(session, elig_room)
                session.commit()
            print(
                f"DB 休講: 新規 {pc.inserted} / 重複除外 {pc.duplicates} "
                f"（必須不足 {len(skip_cancel)} 件 → output/cancelled_classes_skipped.json）"
            )
            print(
                f"DB 補講: 新規 {pm.inserted} / 重複除外 {pm.duplicates} "
                f"（必須不足 {len(skip_makeup)} 件 → output/makeup_classes_skipped.json）"
            )
            print(
                f"DB 部屋変更: 新規 {pr.inserted} / 重複除外 {pr.duplicates} "
                f"（必須不足 {len(skip_room)} 件 → output/room_changes_skipped.json）"
            )
        except Exception as e:
            print(f"DB 保存エラー: {e}", flush=True)
        finally:
            engine.dispose()

    with open(OUTPUT_DIR / "cancelled_classes.json", "w", encoding="utf-8") as f:
        json.dump(cancelled_classes_json, f, ensure_ascii=False, indent=2)
    with open(OUTPUT_DIR / "makeup_classes.json", "w", encoding="utf-8") as f:
        json.dump(makeup_classes_json, f, ensure_ascii=False, indent=2)
    with open(OUTPUT_DIR / "room_changes.json", "w", encoding="utf-8") as f:
        json.dump(room_changes_json, f, ensure_ascii=False, indent=2)
    print(f"休講 {len(cancelled_classes_json)} 件 → output/cancelled_classes.json")
    print(f"補講 {len(makeup_classes_json)} 件 → output/makeup_classes.json")
    print(f"部屋変更 {len(room_changes_json)} 件 → output/room_changes.json")


if __name__ == "__main__":
    main()
