variable "project_id" {
  type        = string
  description = "Google Cloud プロジェクト ID"
}

variable "region" {
  type        = string
  description = "Cloud Run Job / Artifact Registry / Scheduler のリージョン"
  default     = "asia-northeast1"
}

variable "instance_connection_name" {
  type        = string
  description = "Cloud SQL のインスタンス接続名（project:region:instance 形式）"
}

variable "db_name" {
  type        = string
  description = "接続先の PostgreSQL データベース名"
}

variable "schedule" {
  type        = string
  description = "Cloud Scheduler の cron 式（time_zone は Asia/Tokyo 固定）"
  default     = "0 17 * * *"
}

variable "image_tag" {
  type        = string
  description = "Cloud Run Job が参照する Docker イメージタグ"
  default     = "latest"
}
