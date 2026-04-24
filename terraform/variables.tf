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

  validation {
    condition = length(split(":", var.instance_connection_name)) == 3 && alltrue([
      for part in split(":", var.instance_connection_name) : trimspace(part) != ""
    ])
    error_message = "instance_connection_name は \"project:region:instance\" 形式で指定してください。"
  }
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

variable "secret_project_id" {
  type        = string
  description = "USER_ID / USER_PASSWORD の Secret を保持している外部プロジェクトの ID"
}

variable "user_id_secret_name" {
  type        = string
  description = "外部プロジェクト上の USER_ID Secret の名前"
  default     = "class-change-batch-user-id"
}

variable "user_password_secret_name" {
  type        = string
  description = "外部プロジェクト上の USER_PASSWORD Secret の名前"
  default     = "class-change-batch-user-password"
}
