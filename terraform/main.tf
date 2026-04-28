terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "swift2023groupc-tfstate"
    prefix = "class-change-batch"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  service_name = "class-change-batch"
  image        = "${var.region}-docker.pkg.dev/${var.project_id}/${local.service_name}/${local.service_name}:${var.image_tag}"

  cloud_sql_instance_name = split(":", var.instance_connection_name)[2]

  batch_jobs_repo_name = "batch-jobs"
  batch_jobs_image     = "${var.region}-docker.pkg.dev/${var.project_id}/${local.batch_jobs_repo_name}/${local.batch_jobs_repo_name}:${var.batch_jobs_image_tag}"
  batch_jobs_sa_id     = "batch-jobs-job"

  batch_jobs = {
    "build-class-change-notifications" = {
      schedule = var.build_class_change_notifications_schedule
      command  = ["/bin/build-class-change-notifications"]
    }
    "dispatch-notifications" = {
      schedule = var.dispatch_notifications_schedule
      command  = ["/bin/dispatch-notifications"]
    }
  }
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "iam.googleapis.com",
    "fcm.googleapis.com",
    "firebase.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}
