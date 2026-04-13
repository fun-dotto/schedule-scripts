resource "google_service_account" "scheduler" {
  account_id   = "${local.service_name}-scheduler"
  display_name = "Class Change Batch Cloud Scheduler"

  depends_on = [google_project_service.required_apis]
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  project  = google_cloud_run_v2_job.job.project
  location = google_cloud_run_v2_job.job.location
  name     = google_cloud_run_v2_job.job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "trigger" {
  name        = "${local.service_name}-trigger"
  description = "Trigger class change batch Cloud Run Job daily at 17:00 JST"
  schedule    = var.schedule
  time_zone   = "Asia/Tokyo"
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${google_cloud_run_v2_job.job.location}/jobs/${google_cloud_run_v2_job.job.name}:run"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode("{}")

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_v2_job_iam_member.scheduler_invoker,
  ]
}
