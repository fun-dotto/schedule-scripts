"""補講テーブル行のパース。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TypedDict

from scrapers.nendo import add_years, nendo_end, nendo_start


class MakeupClasses(TypedDict):
    lessonId: int
    date: date
    period: str
    lessonName: str
    campus: str
    staff: str
    comment: str
    roomName: str
    roomId: int


def makeup_classes_to_dict(s: MakeupClasses) -> dict:
    return {**s, "date": s["date"].isoformat()}


def get_makeup_classes(table_rows) -> list[MakeupClasses]:
    makeup_classes: list[MakeupClasses] = []
    room_name_to_id = {
        "アトリエ": "50",
        "363": "16",
        "364": "17",
        "365": "18",
        "体育館": "51",
        "大講義室": "2",
        "483": "19",
        "484": "10",
        "493": "3",
        "494C&D": "8",
        "495C&D": "9",
        "講堂": "1",
        "583": "11",
        "584": "12",
        "585": "13",
        "593": "4",
        "594": "5",
        "595": "6",
        "R781": "14",
        "R782": "15",
        "R791": "7",
    }
    for row in table_rows:
        date_td = row.find("td", {"data-col-responsive-title": "日付"})
        day = row.find("td", {"data-col-responsive-title": "曜日"})
        period = row.find("td", {"data-col-responsive-title": "時限"})
        lecture_name = row.find("td", {"data-col-responsive-title": "授業名"})
        campus = row.find("td", {"data-col-responsive-title": "キャンパス"})
        room_td = row.find("td", {"data-col-responsive-title": "教室名"})
        instructor = row.find("td", {"data-col-responsive-title": "代表教職員"})
        supplement_comment = row.find(
            "td", {"data-col-responsive-title": "補講コメント"}
        )
        today = date.today()
        d_format = "%m/%d"

        if all(
            [
                date_td,
                day,
                period,
                lecture_name,
                campus,
                room_td,
                instructor,
                supplement_comment,
            ]
        ):
            dt = date_td.text.strip()
            s_dt = datetime.strptime(dt, d_format).date()
            new_date = date(year=today.year, month=s_dt.month, day=s_dt.day)
            if new_date < nendo_start():
                new_date = add_years(new_date, 1)
            if new_date > nendo_end():
                new_date = add_years(new_date, -1)
            room_name = room_td.text.strip()
            room_id = int(room_name_to_id[room_name]) if room_name in room_name_to_id else 0
            makeup_classes.append(
                {
                    "lessonId": 0,
                    "date": new_date,
                    "period": f"Period{int(period.text.strip()[0])}",
                    "lessonName": lecture_name.text.strip(),
                    "campus": campus.text.strip(),
                    "staff": instructor.text.strip(),
                    "comment": supplement_comment.text.strip(),
                    "roomName": room_name,
                    "roomId": room_id,
                }
            )
    return makeup_classes
