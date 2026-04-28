"""休講テーブル行のパース。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TypedDict

from dotto_batch_jobs.scrape_class_changes.scrapers.nendo import add_years, nendo_end, nendo_start


class CancelledClass(TypedDict):
    lessonId: int
    date: date
    period: str
    lessonName: str
    campus: str
    staff: str
    comment: str
    type: str


def cancelled_classes_to_dict(k: CancelledClass) -> dict:
    return {**k, "date": k["date"].isoformat()}


def get_cancelled_classes(table_rows) -> list[CancelledClass]:
    cancelled_classes: list[CancelledClass] = []
    for row in table_rows:
        date_td = row.find("td", {"data-col-responsive-title": "日付"})
        day = row.find("td", {"data-col-responsive-title": "曜日"})
        period = row.find("td", {"data-col-responsive-title": "時限"})
        lecture_name = row.find("td", {"data-col-responsive-title": "授業名"})
        campus = row.find("td", {"data-col-responsive-title": "キャンパス"})
        instructor = row.find("td", {"data-col-responsive-title": "代表教職員"})
        cancellation_comment = row.find(
            "td", {"data-col-responsive-title": "休講コメント"}
        )
        today = date.today()
        d_format = "%m/%d"

        if all(
            [date_td, day, period, lecture_name, campus, instructor, cancellation_comment]
        ):
            cancel_comment = cancellation_comment.text.strip()
            kind = "その他"
            if cancel_comment.startswith("補講あり"):
                kind = "補講あり"
            elif cancel_comment.startswith("補講なし"):
                kind = "補講なし"
            elif cancel_comment.startswith("補講未定"):
                kind = "補講未定"
            dt = date_td.text.strip()
            s_dt = datetime.strptime(dt, d_format).date()
            new_date = date(year=today.year, month=s_dt.month, day=s_dt.day)
            if new_date < nendo_start():
                new_date = add_years(new_date, 1)
            if new_date > nendo_end():
                new_date = add_years(new_date, -1)
            cancelled_classes.append(
                {
                    "lessonId": 0,
                    "date": new_date,
                    "period": f"Period{int(period.text.strip()[0])}",
                    "lessonName": lecture_name.text.strip(),
                    "campus": campus.text.strip(),
                    "staff": instructor.text.strip(),
                    "comment": cancel_comment,
                    "type": kind,
                }
            )
    return cancelled_classes
