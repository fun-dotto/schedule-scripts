resource "google_service_account" "job" {
  account_id   = "${local.service_name}-job"
  display_name = "Irregularities Batch Cloud Run Job"

  depends_on = [google_project_service.required_apis]
}

resource "google_project_iam_member" "job_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.job.email}"
}

resource "google_project_iam_member" "job_sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.job.email}"
}

resource "google_project_iam_member" "job_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.job.email}"
}

resource "google_sql_user" "job_iam_user" {
  name     = trimsuffix(google_service_account.job.email, ".gserviceaccount.com")
  instance = local.cloud_sql_instance_name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"

  depends_on = [google_project_service.required_apis]
}
