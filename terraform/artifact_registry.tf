resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = local.service_name
  format        = "DOCKER"
  description   = "class change batch job images"

  depends_on = [google_project_service.required_apis]
}
