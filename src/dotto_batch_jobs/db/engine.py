"""Cloud SQL への SQLAlchemy engine（migrate やジョブで共有）。"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v or not v.strip():
        raise RuntimeError(f"環境変数 {name} が未設定です（.env を確認）")
    return v.strip()


def get_engine():
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
