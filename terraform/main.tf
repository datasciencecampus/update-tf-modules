terraform {
  required_version = ">= 1.5.0"
}

module "state_bootstrap" {
  source = "git::https://github.com/datasciencecampus/terraform-gcs-remote-state-bootstrap.git?ref=v1.1.1"
}

module "network" {
  source  = "terraform-google-modules/network/google"
  version = "18.1.0"
}
