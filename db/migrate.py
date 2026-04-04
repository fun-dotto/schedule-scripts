"""
モデル定義に基づきテーブルを作成する（SQLAlchemy metadata.create_all）。

.env の Cloud SQL 用変数（.env.example 参照）で接続する。
"""

from __future__ import annotations

from db.engine import get_engine
from db.models import Base


def migrate() -> None:
    engine = get_engine()
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    migrate()
    print("migrate 完了: cancelled_classes, makeup_classes, room_changes")
