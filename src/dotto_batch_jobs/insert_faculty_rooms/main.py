"""faculties CSV を読み faculty_rooms テーブルへ INSERT する。

- email -> faculties.id, room_name -> rooms.name で照合
- room_name 空欄の行はスキップ
- 未一致が出た場合は INSERT せずに中断
- (faculty_id, year) / (room_id, year) の UNIQUE 違反は IntegrityError で停止
"""

from __future__ import annotations

import argparse
import csv
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from dotto_batch_jobs.db.engine import get_engine
from dotto_batch_jobs.db.models import Faculty, FacultyRoom
from dotto_batch_jobs.db.room_map import load_room_name_to_id_map, normalize_room_name


def _norm_email(s: str) -> str:
    return s.strip().lower()


def _parse_faculties(value: str) -> tuple[int, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"--faculties は YEAR=PATH 形式で指定してください: {value!r}"
        )
    year_str, path_str = value.split("=", 1)
    try:
        year = int(year_str)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"年度は整数で指定してください: {year_str!r}") from e
    if not path_str:
        raise argparse.ArgumentTypeError(f"PATH が空です: {value!r}")
    return year, Path(path_str)


def _parse_args() -> dict[int, Path]:
    parser = argparse.ArgumentParser(
        description=(
            "faculties CSV を読み faculty_rooms テーブルへ INSERT する。"
            " CSV は UTF-8 / ヘッダ行必須、必須カラムは name, email, room_name。"
            " email は faculties.email、room_name は rooms.name と照合する。"
            " room_name 空欄行はスキップ。"
        )
    )
    parser.add_argument(
        "--faculties",
        action="append",
        required=True,
        type=_parse_faculties,
        metavar="YEAR=PATH",
        help=(
            "年度と CSV パスのペア（例: --faculties 2025=<path-to-data-directory>/faculties_2025.csv）。"
            " 複数年度を取り込む場合は本オプションを複数回指定する。"
            " CSV 必須カラム: name, email, room_name"
        ),
    )
    args = parser.parse_args()
    csv_paths: dict[int, Path] = {}
    for year, path in args.faculties:
        if year in csv_paths:
            parser.error(f"年度 {year} が複数回指定されています")
        csv_paths[year] = path
    return csv_paths


def main() -> None:
    load_dotenv(override=False)
    csv_paths = _parse_args()
    engine = get_engine()
    try:
        name_to_room_id = load_room_name_to_id_map(engine)

        with Session(engine) as session:
            email_to_faculty_id: dict[str, uuid.UUID] = {}
            for fid, email in session.execute(
                select(Faculty.id, Faculty.email).where(Faculty.email.is_not(None))
            ):
                key = _norm_email(email)
                if key:
                    email_to_faculty_id[key] = fid

            new_rows: list[FacultyRoom] = []
            unmatched_emails: set[str] = set()
            unmatched_rooms: set[str] = set()
            skipped_blank = 0

            for year, path in sorted(csv_paths.items()):
                with open(path, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        room_name = (row.get("room_name") or "").strip()
                        if not room_name:
                            skipped_blank += 1
                            continue
                        email_raw = (row.get("email") or "").strip()
                        fid = email_to_faculty_id.get(_norm_email(email_raw))
                        rid = name_to_room_id.get(normalize_room_name(room_name))
                        if fid is None:
                            unmatched_emails.add(email_raw)
                        if rid is None:
                            unmatched_rooms.add(room_name)
                        if fid is None or rid is None:
                            continue
                        new_rows.append(
                            FacultyRoom(faculty_id=fid, room_id=rid, year=year)
                        )

            if unmatched_emails or unmatched_rooms:
                if unmatched_emails:
                    print(
                        f"未一致 email ({len(unmatched_emails)} 件): {sorted(unmatched_emails)}",
                        file=sys.stderr,
                    )
                if unmatched_rooms:
                    print(
                        f"未一致 room_name ({len(unmatched_rooms)} 件): {sorted(unmatched_rooms)}",
                        file=sys.stderr,
                    )
                print("中断: DB に該当行が無い項目があります（INSERT は実行しません）", file=sys.stderr)
                sys.exit(1)

            session.add_all(new_rows)
            session.commit()
            print(
                f"INSERT 完了: {len(new_rows)} 件 / 空 room_name スキップ: {skipped_blank} 件"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
