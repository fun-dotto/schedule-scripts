resource "google_service_account" "scheduler" {
  account_id   = "${local.service_name}-scheduler"
  display_name = "Class Change Batch Cloud Scheduler"

  depends_on = [google_project_service.required_apis]
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_service_account_iam_member" "scheduler_token_creator" {
  service_account_id = google_service_account.scheduler.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"

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
  description = "Trigger class change batch Cloud Run Job"
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

resource "google_cloud_run_v2_job_iam_member" "batch_jobs_scheduler_invoker" {
  for_each = google_cloud_run_v2_job.batch_jobs

  project  = each.value.project
  location = each.value.location
  name     = each.value.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "batch_jobs_triggers" {
  for_each = local.batch_jobs

  name        = "${each.key}-trigger"
  description = "Trigger ${each.key} Cloud Run Job"
  schedule    = each.value.schedule
  time_zone   = "Asia/Tokyo"
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${each.key}:run"
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
    google_cloud_run_v2_job_iam_member.batch_jobs_scheduler_invoker,
  ]
}
