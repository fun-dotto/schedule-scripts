import json
import os
import time
from datetime import date, datetime
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(override=False)
USERNAME = os.environ.get("USER_ID")
PASSWORD = os.environ.get("USER_PASSWORD")
YEAR = 2026


class Kyukou(TypedDict):
    lessonId: int
    date: date
    period: int
    lessonName: str
    campus: str
    staff: str
    comment: str
    type: str


class Supple(TypedDict):
    lessonId: int
    date: date
    period: int
    lessonName: str
    campus: str
    staff: str
    comment: str
    roomName: str
    roomId: int


class ClassroomExchange(TypedDict):
    lessonId: int
    date: date
    period: int
    lessonName: str
    campus: str
    staff: str
    roomFrom: str
    roomTo: str


def nendo_start() -> date:
    return date(YEAR, 4, 1)


def nendo_end() -> date:
    return date(YEAR + 1, 3, 31)


def _add_years(d: date, delta: int) -> date:
    return date(d.year + delta, d.month, d.day)


def kyukou_to_dict(k: Kyukou) -> dict:
    return {**k, "date": k["date"].isoformat()}


def supple_to_dict(s: Supple) -> dict:
    return {**s, "date": s["date"].isoformat()}


def classroom_exchange_to_dict(c: ClassroomExchange) -> dict:
    return {**c, "date": c["date"].isoformat()}


def login_session() -> requests.Session:
    session = requests.Session()
    payload = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__SCROLLPOSITIONX": 0,
        "__SCROLLPOSITIONY": 0,
        "ctl00$MainContent$TargetYearList": YEAR,
        "ctl00$MainContent$TargetTermList": 11,
        "ctl00$MainContent$LoginId": USERNAME,
        "ctl00$MainContent$LoginPassword": PASSWORD,
        "ctl00$MainContent$LoginButton": "ログイン",
    }
    hidden = ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]
    r = session.get("https://students.fun.ac.jp/Login", timeout=30)
    r.raise_for_status()
    bs = BeautifulSoup(r.text, "html.parser")
    for name in hidden:
        el = bs.find(attrs={"name": name})
        if el and el.get("value") is not None:
            payload[name] = el["value"]
    r = session.post("https://students.fun.ac.jp/Login", data=payload, timeout=30)
    r.raise_for_status()
    time.sleep(2)
    return session


def get_kyukou(table_rows) -> list[Kyukou]:
    kyukou_lessons: list[Kyukou] = []
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
                new_date = _add_years(new_date, 1)
            if new_date > nendo_end():
                new_date = _add_years(new_date, -1)
            kyukou_lessons.append(
                {
                    "lessonId": 0,
                    "date": new_date,
                    "period": int(period.text.strip()[0]),
                    "lessonName": lecture_name.text.strip(),
                    "campus": campus.text.strip(),
                    "staff": instructor.text.strip(),
                    "comment": cancel_comment,
                    "type": kind,
                }
            )
    return kyukou_lessons


def get_sup_lesson(table_rows) -> list[Supple]:
    supplemental: list[Supple] = []
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
                new_date = _add_years(new_date, 1)
            if new_date > nendo_end():
                new_date = _add_years(new_date, -1)
            room_name = room_td.text.strip()
            room_id = int(room_name_to_id[room_name]) if room_name in room_name_to_id else 0
            supplemental.append(
                {
                    "lessonId": 0,
                    "date": new_date,
                    "period": int(period.text.strip()[0]),
                    "lessonName": lecture_name.text.strip(),
                    "campus": campus.text.strip(),
                    "staff": instructor.text.strip(),
                    "comment": supplement_comment.text.strip(),
                    "roomName": room_name,
                    "roomId": room_id,
                }
            )
    return supplemental


def get_classroom_exchange(table_rows) -> list[ClassroomExchange]:
    """MainContent_MainContent_ClassroomExchangedLectureGridView 相当（移動元・移動先列）。"""
    out: list[ClassroomExchange] = []
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
            new_date = _add_years(new_date, 1)
        if new_date > nendo_end():
            new_date = _add_years(new_date, -1)
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


def fetch_cancel_supple() -> tuple[list[Kyukou], list[Supple], list[ClassroomExchange]]:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("環境変数 USER_ID / USER_PASSWORD を設定してください")
    session = login_session()
    try:
        r = session.get("https://students.fun.ac.jp/Pt/CSLecture", timeout=30)
        r.raise_for_status()
        bs = BeautifulSoup(r.text, "html.parser")
        table_rows = bs.find_all("tr")
    finally:
        session.close()

    return (
        get_kyukou(table_rows),
        get_sup_lesson(table_rows),
        get_classroom_exchange(table_rows),
    )


def main() -> None:
    kyukou_list, supple_list, exchange_list = fetch_cancel_supple()
    kyukou_json = [kyukou_to_dict(k) for k in kyukou_list]
    supple_json = [supple_to_dict(s) for s in supple_list]
    exchange_json = [classroom_exchange_to_dict(c) for c in exchange_list]
    with open("cancel_lecture.json", "w", encoding="utf-8") as f:
        json.dump(kyukou_json, f, ensure_ascii=False, indent=2)
    with open("sup_lecture.json", "w", encoding="utf-8") as f:
        json.dump(supple_json, f, ensure_ascii=False, indent=2)
    with open("classroom_exchange_lecture.json", "w", encoding="utf-8") as f:
        json.dump(exchange_json, f, ensure_ascii=False, indent=2)
    print(f"休講 {len(kyukou_json)} 件 → cancel_lecture.json")
    print(f"補講 {len(supple_json)} 件 → sup_lecture.json")
    print(
        f"教室移動 {len(exchange_json)} 件 → classroom_exchange_lecture.json"
    )


if __name__ == "__main__":
    main()
