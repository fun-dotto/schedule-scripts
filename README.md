# batch-jobs

公立はこだて未来大学の学生ポータル（`students.fun.ac.jp`）から **休講・補講・教室変更** をスクレイピングし、Cloud SQL (PostgreSQL) に保存・正規化したうえで、翌日分の予定について FCM プッシュ通知を配信するためのバッチ群。

Cloud Run Job + Cloud Scheduler 上で日次実行することを想定している。

## 構成

このリポジトリには Python と Go の 2 種類のジョブが同居している。

| 種別 | エントリポイント | 役割 |
| --- | --- | --- |
| Python | `main.py` | ポータルから休講・補講・教室変更をスクレイピングし、`subjects` / `rooms` と突合して `cancelled_classes` / `makeup_classes` / `room_changes` テーブルへ UPSERT する。 |
| Python | `scripts/insert_faculty_rooms.py` | `data/faculties_{year}.csv` を読み、`faculties.email` と `rooms.name` で照合して `faculty_rooms` を一括 INSERT する（年次運用ツール）。 |
| Go | `cmd/build-class-change-notifications` | 翌日の休講・補講・教室変更を DB から読み、履修者宛の `notifications` レコードを生成（UPSERT）する。 |
| Go | `cmd/dispatch-notifications` | `notifications` の配信待ちを取得し、対象ユーザーの FCM トークン宛に Firebase Cloud Messaging で送信する。`-dry-run` フラグ対応。 |

### ディレクトリ

```
.
├── main.py                          # Python: スクレイピング + DB 保存
├── lesson_ids.py                    # 授業名 ↔ data/classification_result.csv のマッチング
├── data/                            # CSV / JSON 入出力（classification_result.csv, faculties_*.csv, rooms.csv, *.json）
├── scrapers/                        # ポータルログイン / HTML パース
├── db/                              # SQLAlchemy エンジン・モデル・永続化処理
├── scripts/insert_faculty_rooms.py  # 教員と居室の年次データ取り込み
├── cmd/                             # Go バイナリのエントリポイント
│   ├── build-class-change-notifications/
│   └── dispatch-notifications/
├── internal/
│   ├── domain/                      # ドメインモデル
│   ├── database/                    # Cloud SQL Connector + GORM 接続
│   ├── repository/                  # DB アクセス
│   └── service/                     # 通知作成 / FCM 配信ロジック
├── terraform/                       # GCP リソース定義（Cloud Run Job + Scheduler 等）
├── Dockerfile                       # Python ジョブ用イメージ
├── go.mod                           # Go 依存定義
├── pyproject.toml / uv.lock         # Python 依存定義（uv 管理）
└── mise.toml                        # ツールチェイン（uv / Go / Terraform）
```

## 必要環境

`mise.toml` で固定しているバージョン。

- uv 0.11.8（Python 3.12 は uv が `pyproject.toml` の `requires-python` に従って自動取得）
- Go 1.25.7
- Terraform 1.9.8

`mise install` で一括取得できる。

## 環境変数

`.env.example` をコピーして `.env` を作成する。

| 変数名 | 用途 |
| --- | --- |
| `USER_ID` | ポータルログイン用の学籍番号 |
| `USER_PASSWORD` | ポータルログイン用のパスワード |
| `DB_IAM_USER` | Cloud SQL IAM 認証ユーザー（SA メールから `.gserviceaccount.com` を除いたもの） |
| `DB_NAME` | 接続先データベース名 |
| `INSTANCE_CONNECTION_NAME` | Cloud SQL 接続名 `project:region:instance` |
| `GOOGLE_APPLICATION_CREDENTIALS` | ローカル実行時の SA キーへのパス（Cloud Run 上では不要） |

## ローカル実行

### Python ジョブ（スクレイピング + DB 保存）

```sh
uv sync
uv run python main.py
```

実行結果として `data/*.json`（取得結果と必須項目欠落のスキップ一覧）が出力される。

依存追加は `uv add <pkg>`、ロック更新は `uv lock --upgrade`。

### 教員居室データの取り込み

```sh
uv run python -m scripts.insert_faculty_rooms
```

`faculties_{2025,2026}.csv` を読み、未一致の email / room_name があれば INSERT せず中断する。

### Go ジョブ

```sh
# 翌日分の通知レコードを生成
go run ./cmd/build-class-change-notifications

# 配信待ち通知を FCM で送信（実送信前は dry-run 推奨）
go run ./cmd/dispatch-notifications -dry-run
go run ./cmd/dispatch-notifications
```

`dispatch-notifications` は Firebase Admin SDK を使うため、`GOOGLE_APPLICATION_CREDENTIALS` で Firebase プロジェクトに対する権限を持つ SA を渡す必要がある。

## デプロイ（Terraform）

`terraform/` 配下に Cloud Run Job / Cloud Scheduler / Artifact Registry / Service Account / IAM の定義一式が入っている。state は `swift2023groupc-tfstate` バケットに保管。

```sh
cd terraform
cp terraform.tfvars.example terraform.tfvars  # 値を埋める
terraform init
terraform plan
terraform apply
```

### スケジュール

`terraform.tfvars` の `schedule` で cron を指定する（タイムゾーンは Asia/Tokyo 固定、デフォルト `0 17 * * *`）。

### シークレット

`USER_ID` / `USER_PASSWORD` は別プロジェクトの Secret Manager で管理し、`secret_project_id` 経由で参照する。Cloud Run Job の SA に対象シークレットへの `roles/secretmanager.secretAccessor` を付与しておくこと。

## 通知の流れ

```
[Cloud Scheduler]
       │ 17:00 JST 起動
       ▼
[main.py / class-change-batch Cloud Run Job]
   ポータルから休講・補講・教室変更を取得
   subjects / rooms と突合して DB へ UPSERT
       │
       ▼
[build-class-change-notifications]
   翌日分のレコードを集めて notifications を UPSERT
   履修者を course_registrations から解決
       │
       ▼
[dispatch-notifications]
   notifications.notify_after / notify_before の窓内のものを取得
   fcm_tokens を引いて FCM Multicast 送信
   送信成功分を is_notified=true にマーク
```

通知 ID は `urn:schedule-scripts:class-change:{type}:{source_id}` から SHA-1 ベースの UUID v5 で決定論的に生成しており、再実行しても重複登録されない。
