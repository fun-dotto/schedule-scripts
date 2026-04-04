"""
モデル定義に基づきテーブルを作成する（SQLAlchemy metadata.create_all）。

.env の Cloud SQL 用変数（.env.example 参照）で接続する。
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine

import db.models  # noqa: F401 — テーブルを Base に登録
from db.models import Base


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v or not v.strip():
        raise RuntimeError(f"環境変数 {name} が未設定です（.env を確認）")
    return v.strip()


def get_engine():
    """
    Cloud SQL（PostgreSQL）に IAM 認証で接続する Engine を返す。

    使用する環境変数:
      INSTANCE_CONNECTION_NAME, DB_NAME, DB_IAM_USER
      GOOGLE_APPLICATION_CREDENTIALS（サービスアカウント JSON のパス）
    """
    load_dotenv(override=False)
    instance = _require_env("INSTANCE_CONNECTION_NAME")
    database = _require_env("DB_NAME")
    user = _require_env("DB_IAM_USER")

    connector = Connector()

    def getconn():
        return connector.connect(
            instance,
            "pg8000",
            user=user,
            db=database,
            enable_iam_auth=True,
        )

    return create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
    )


def migrate() -> None:
    """未作成のテーブルのみ作成する（既存テーブルは変更しない）。"""
    engine = get_engine()
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    migrate()
    print("migrate 完了: cancel_lectures, supplement_lectures, room_changes")
