resource "google_secret_manager_secret" "user_id" {
  secret_id = "${local.service_name}-user-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_iam_member" "job_user_id_accessor" {
  secret_id = google_secret_manager_secret.user_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.job.email}"
}

resource "google_secret_manager_secret" "user_password" {
  secret_id = "${local.service_name}-user-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_iam_member" "job_user_password_accessor" {
  secret_id = google_secret_manager_secret.user_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.job.email}"
}
