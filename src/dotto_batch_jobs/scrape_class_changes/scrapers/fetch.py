"""CS 講義ページ取得と休講・補講・部屋変更の一括取得。"""

from __future__ import annotations

from bs4 import BeautifulSoup

from dotto_batch_jobs.scrape_class_changes.scrapers.auth import PASSWORD, USERNAME, login_session
from dotto_batch_jobs.scrape_class_changes.scrapers.cancel_classes import CancelledClass, get_cancelled_classes
from dotto_batch_jobs.scrape_class_changes.scrapers.room_change import RoomChange, get_room_changes
from dotto_batch_jobs.scrape_class_changes.scrapers.makeup_classes import MakeupClasses, get_makeup_classes


def fetch_cancel_supple() -> tuple[list[CancelledClass], list[MakeupClasses], list[RoomChange]]:
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
        get_cancelled_classes(table_rows),
        get_makeup_classes(table_rows),
        get_room_changes(table_rows),
    )
