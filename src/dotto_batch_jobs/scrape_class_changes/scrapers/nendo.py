"""年度（4月始まり）の範囲と日付補正。"""

from __future__ import annotations

from datetime import date

YEAR = 2026


def nendo_start() -> date:
    return date(YEAR, 4, 1)


def nendo_end() -> date:
    return date(YEAR + 1, 3, 31)


def add_years(d: date, delta: int) -> date:
    return date(d.year + delta, d.month, d.day)
