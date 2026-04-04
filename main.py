import json
from pathlib import Path

from dotenv import load_dotenv

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
