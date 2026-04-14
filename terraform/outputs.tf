output "job_service_account_email" {
  value       = google_service_account.job.email
  description = "Cloud Run Job 実行 SA（Cloud SQL IAM ユーザーとして登録済み）"
}

output "scheduler_service_account_email" {
  value       = google_service_account.scheduler.email
  description = "Cloud Scheduler 用 SA"
}

output "artifact_registry_repository" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${local.service_name}"
  description = "Docker イメージの push 先リポジトリ"
}

output "docker_image" {
  value       = local.image
  description = "Cloud Run Job が参照するイメージ URI"
}

output "secret_user_id_name" {
  value       = google_secret_manager_secret.user_id.secret_id
  description = "USER_ID のシークレット名（値は gcloud で別途登録）"
}

output "secret_user_password_name" {
  value       = google_secret_manager_secret.user_password.secret_id
  description = "USER_PASSWORD のシークレット名（値は gcloud で別途登録）"
}

output "cloud_run_job_name" {
  value       = google_cloud_run_v2_job.job.name
  description = "Cloud Run Job 名（手動実行: gcloud run jobs execute）"
}
