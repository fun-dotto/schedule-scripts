resource "google_service_account" "job" {
  account_id   = "${local.service_name}-job"
  display_name = "Class Change Batch Cloud Run Job"

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

resource "google_sql_user" "job_iam_user" {
  name     = trimsuffix(google_service_account.job.email, ".gserviceaccount.com")
  instance = local.cloud_sql_instance_name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"

  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "batch_jobs_job" {
  account_id   = local.batch_jobs_sa_id
  display_name = "Batch Jobs (Go) Cloud Run Job"

  depends_on = [google_project_service.required_apis]
}

resource "google_project_iam_member" "batch_jobs_job_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.batch_jobs_job.email}"
}

resource "google_project_iam_member" "batch_jobs_job_sql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.batch_jobs_job.email}"
}

resource "google_sql_user" "batch_jobs_job_iam_user" {
  name     = trimsuffix(google_service_account.batch_jobs_job.email, ".gserviceaccount.com")
  instance = local.cloud_sql_instance_name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"

  depends_on = [google_project_service.required_apis]
}

# dispatch-notifications が FCM HTTP v1 API でプッシュ通知を送るための最小権限。
# Firebase 系の predefined role はいずれも広すぎる（auth / firestore / storage 等まで触れる）ため、
# cloudmessaging.messages.create だけを持つカスタムロールに絞っている。
resource "google_project_iam_custom_role" "fcm_sender" {
  role_id     = "fcmSender"
  title       = "FCM Sender"
  description = "Send FCM messages via the HTTP v1 API"
  permissions = [
    "cloudmessaging.messages.create",
  ]
}

resource "google_project_iam_member" "batch_jobs_job_fcm_sender" {
  project = var.project_id
  role    = google_project_iam_custom_role.fcm_sender.name
  member  = "serviceAccount:${google_service_account.batch_jobs_job.email}"
}
