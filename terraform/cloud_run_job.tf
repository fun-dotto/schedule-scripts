resource "google_cloud_run_v2_job" "job" {
  name     = local.service_name
  location = var.region

  template {
    template {
      service_account = google_service_account.job.email
      timeout         = "900s"
      max_retries     = 1

      containers {
        image = local.image

        env {
          name  = "INSTANCE_CONNECTION_NAME"
          value = var.instance_connection_name
        }

        env {
          name  = "DB_NAME"
          value = var.db_name
        }

        env {
          name  = "DB_IAM_USER"
          value = trimsuffix(google_service_account.job.email, ".gserviceaccount.com")
        }

        env {
          name = "USER_ID"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.user_id.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "USER_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.user_password.secret_id
              version = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      # CI/CD からイメージタグを更新する運用に備え、template 全体の変更を Terraform では無視
      template,
    ]
  }

  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.repo,
    google_project_iam_member.job_sql_client,
    google_project_iam_member.job_sql_instance_user,
    google_project_iam_member.job_secret_accessor,
  ]
}
