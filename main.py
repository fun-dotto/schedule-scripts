import json
from pathlib import Path

from dotenv import load_dotenv

from db.engine import get_engine
from db.room_map import fill_room_ids_in_room_changes, load_room_name_to_id_map
from db.subject_map import fill_subject_ids_in_records, load_syllabus_to_subject_id_map
from lesson_ids import default_classification_csv_path, fill_lesson_ids_in_records
from scrapers.fetch import fetch_cancel_supple
from scrapers.cancel_classes import cancelled_classes_to_dict
from scrapers.room_change import room_change_to_dict
from scrapers.makeup_classes import makeup_classes_to_dict

load_dotenv(override=False)

ROOT = Path(__file__).resolve().parent


def main() -> None:
    cancelled_classes_list, makeup_classes_list, exchange_list = fetch_cancel_supple()
    cancelled_classes_json = [cancelled_classes_to_dict(k) for k in cancelled_classes_list]
    makeup_classes_json = [makeup_classes_to_dict(s) for s in makeup_classes_list]
    exchange_json = [room_change_to_dict(c) for c in exchange_list]

    csv_path = default_classification_csv_path(ROOT)
    if csv_path.is_file():
        r_k = fill_lesson_ids_in_records(cancelled_classes_json, csv_path)
        r_s = fill_lesson_ids_in_records(makeup_classes_json, csv_path)
        r_r = fill_lesson_ids_in_records(exchange_json, csv_path)
        print(
            f"lessonId 照合（{csv_path.name}） 休講: {r_k.matched}/{r_k.total} 件, "
            f"補講: {r_s.matched}/{r_s.total} 件, "
            f"部屋変更: {r_r.matched}/{r_r.total} 件"
        )
    else:
        print(
            f"スキップ: {csv_path.name} が無いため lessonId は 0 のまま（休講・補講・部屋変更）",
            flush=True,
        )

    try:
        engine = get_engine()
        try:
            syllabus_map = load_syllabus_to_subject_id_map(engine)
            sk = fill_subject_ids_in_records(cancelled_classes_json, syllabus_map)
            sm = fill_subject_ids_in_records(makeup_classes_json, syllabus_map)
            sr = fill_subject_ids_in_records(exchange_json, syllabus_map)
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
                rr = fill_room_ids_in_room_changes(exchange_json, room_map)
                print(
                    f"room_id 付与（rooms.name） 移動元: {rr.matched_from}/{rr.eligible_from} 件, "
                    f"移動先: {rr.matched_to}/{rr.eligible_to} 件（部屋変更 {rr.total} 件）"
                )
                if rr.unmatched_names:
                    print(f"警告: rooms に無い教室名: {rr.unmatched_names}", flush=True)
            except Exception as e:
                print(f"スキップ: room_id 付与（{e}）", flush=True)
        finally:
            engine.dispose()
    except RuntimeError as e:
        print(f"スキップ: subject_id 付与（{e}）", flush=True)

    with open("cancel_lecture.json", "w", encoding="utf-8") as f:
        json.dump(cancelled_classes_json, f, ensure_ascii=False, indent=2)
    with open("makeup_classes.json", "w", encoding="utf-8") as f:
        json.dump(makeup_classes_json, f, ensure_ascii=False, indent=2)
    with open("room_change.json", "w", encoding="utf-8") as f:
        json.dump(exchange_json, f, ensure_ascii=False, indent=2)
    print(f"休講 {len(cancelled_classes_json)} 件 → cancel_lecture.json")
    print(f"補講 {len(makeup_classes_json)} 件 → makeup_classes.json")
    print(f"部屋変更 {len(exchange_json)} 件 → room_change.json")


if __name__ == "__main__":
    main()
