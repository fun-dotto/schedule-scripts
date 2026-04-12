resource "google_secret_manager_secret" "user_id" {
  secret_id = "${local.service_name}-user-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "user_password" {
  secret_id = "${local.service_name}-user-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}
