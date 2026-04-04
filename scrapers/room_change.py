"""部屋変更テーブル行のパース（移動元・移動先列）。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TypedDict

from scrapers.nendo import add_years, nendo_end, nendo_start


class RoomChange(TypedDict):
    lessonId: int
    date: date
    period: int
    lessonName: str
    campus: str
    staff: str
    roomFrom: str
    roomTo: str


def room_change_to_dict(c: RoomChange) -> dict:
    return {**c, "date": c["date"].isoformat()}


def get_room_changes(table_rows) -> list[RoomChange]:
    out: list[RoomChange] = []
    today = date.today()
    d_format = "%m/%d"
    for row in table_rows:
        date_td = row.find("td", {"data-col-responsive-title": "日付"})
        period = row.find("td", {"data-col-responsive-title": "時限"})
        lecture_name = row.find("td", {"data-col-responsive-title": "授業名"})
        campus = row.find("td", {"data-col-responsive-title": "キャンパス"})
        instructor = row.find("td", {"data-col-responsive-title": "代表教職員"})
        from_td = row.find("td", {"data-col-responsive-title": "移動元"})
        to_td = row.find("td", {"data-col-responsive-title": "移動先"})
        if not all(
            [date_td, period, lecture_name, campus, instructor, from_td, to_td]
        ):
            continue
        dt = date_td.text.strip()
        s_dt = datetime.strptime(dt, d_format).date()
        new_date = date(year=today.year, month=s_dt.month, day=s_dt.day)
        if new_date < nendo_start():
            new_date = add_years(new_date, 1)
        if new_date > nendo_end():
            new_date = add_years(new_date, -1)
        room_from = from_td.text.strip()
        room_to = to_td.text.strip()
        out.append(
            {
                "lessonId": 0,
                "date": new_date,
                "period": int(period.text.strip()[0]),
                "lessonName": lecture_name.text.strip(),
                "campus": campus.text.strip(),
                "staff": instructor.text.strip(),
                "roomFrom": room_from,
                "roomTo": room_to,
            }
        )
    return out
