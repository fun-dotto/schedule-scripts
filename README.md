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
├── Dockerfile                       # Go バッチ用イメージ（build-class-change-notifications / dispatch-notifications を 1 イメージに収納）
├── Dockerfile.scraper               # Python ジョブ（class-change-batch）用イメージ
├── go.mod / requirements.txt        # 依存定義
└── mise.toml                        # ツールチェイン（Python / Go / Terraform）
```

## 必要環境

`mise.toml` で固定しているバージョン。

- Python 3.12.8
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
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

実行結果として `data/*.json`（取得結果と必須項目欠落のスキップ一覧）が出力される。

### 教員居室データの取り込み

```sh
python -m scripts.insert_faculty_rooms
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

3 つの Cloud Run Job を 2 つの Artifact Registry リポジトリで運用している。

| AR リポジトリ | 用途 | Dockerfile | 含まれるジョブ |
| --- | --- | --- | --- |
| `class-change-batch` | Python スクレイパー | `Dockerfile.scraper` | `class-change-batch` |
| `batch-jobs` | Go バッチ群（単一イメージに複数バイナリ） | `Dockerfile` | `build-class-change-notifications` / `dispatch-notifications` |

### 初回セットアップ

```sh
cd terraform
cp terraform.tfvars.example terraform.tfvars  # 値を埋める
terraform init

# 1. Artifact Registry を先に作成（イメージ push 先を用意）
terraform apply \
  -target=google_artifact_registry_repository.repo \
  -target=google_artifact_registry_repository.batch_jobs_repo

# 2. Docker 認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 3. イメージ build & push（macOS Apple Silicon は --platform linux/amd64 必須）
# Python (class-change-batch)
docker build --platform linux/amd64 -f Dockerfile.scraper \
  -t asia-northeast1-docker.pkg.dev/swift2023groupc/class-change-batch/class-change-batch:latest .
docker push asia-northeast1-docker.pkg.dev/swift2023groupc/class-change-batch/class-change-batch:latest

# Go (build-class-change-notifications + dispatch-notifications)
docker build --platform linux/amd64 \
  -t asia-northeast1-docker.pkg.dev/swift2023groupc/batch-jobs/batch-jobs:latest .
docker push asia-northeast1-docker.pkg.dev/swift2023groupc/batch-jobs/batch-jobs:latest

# 4. 残りのリソースを適用
terraform apply
```

### イメージ更新

該当する Dockerfile を修正後、同じタグで build & push し、Cloud Run Job のイメージ参照を再解決させる。

```sh
gcloud run jobs update <job-name> --region asia-northeast1 \
  --image asia-northeast1-docker.pkg.dev/swift2023groupc/<repo>/<repo>:latest
```

`latest` タグでも Cloud Run Job は作成時点の digest を保持するため、タグ据え置き運用ではこの再解決が必要。タグを git SHA 等にするなら `terraform.tfvars` の `image_tag` / `batch_jobs_image_tag` を更新して `terraform apply` するだけで済む。

### スケジュール

`terraform.tfvars` の以下の変数で cron を指定する（タイムゾーンは Asia/Tokyo 固定）。

| 変数 | 対象ジョブ | デフォルト |
| --- | --- | --- |
| `schedule` | `class-change-batch`（Python） | `0 17 * * *` |
| `build_class_change_notifications_schedule` | `build-class-change-notifications`（Go） | `30 17 * * *` |
| `dispatch_notifications_schedule` | `dispatch-notifications`（Go） | `0 18 * * *` |

ジョブ間に依存があるためデフォルトを 30 分ずつずらしている（スクレイパー → 通知ビルド → 配信）。スクレイパーが 30 分以内に終わらないようなら、`build_class_change_notifications_schedule` を後ろ倒しすること。

### シークレット

`USER_ID` / `USER_PASSWORD` は別プロジェクトの Secret Manager で管理し、`secret_project_id` 経由で参照する（Python の `class-change-batch` のみ使用）。Cloud Run Job の SA に対象シークレットへの `roles/secretmanager.secretAccessor` を付与しておくこと。Go バッチ側は IAM 認証のみで、シークレット参照は不要。

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
