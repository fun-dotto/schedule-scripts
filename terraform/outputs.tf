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

output "secret_user_id_reference" {
  value       = "projects/${var.secret_project_id}/secrets/${var.user_id_secret_name}"
  description = "USER_ID が参照している外部プロジェクトの Secret フルパス"
}

output "secret_user_password_reference" {
  value       = "projects/${var.secret_project_id}/secrets/${var.user_password_secret_name}"
  description = "USER_PASSWORD が参照している外部プロジェクトの Secret フルパス"
}

output "cloud_run_job_name" {
  value       = google_cloud_run_v2_job.job.name
  description = "Cloud Run Job 名（手動実行: gcloud run jobs execute）"
}

output "batch_jobs_artifact_registry_repository" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${local.batch_jobs_repo_name}"
  description = "Batch jobs (Go) の Docker イメージ push 先リポジトリ"
}

output "batch_jobs_docker_image" {
  value       = local.batch_jobs_image
  description = "Batch jobs (Go) の Cloud Run Job が参照するイメージ URI"
}

output "batch_jobs_job_service_account_email" {
  value       = google_service_account.batch_jobs_job.email
  description = "Batch jobs (Go) Cloud Run Job 実行 SA"
}

output "batch_jobs_cloud_run_job_names" {
  value       = [for j in google_cloud_run_v2_job.batch_jobs : j.name]
  description = "Batch jobs (Go) Cloud Run Job 名一覧"
}
