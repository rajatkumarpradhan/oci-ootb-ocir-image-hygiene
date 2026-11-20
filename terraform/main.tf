# TEMPLATE ONLY - NOT plan/apply validated against a live tenancy.
# Built-in resource: OCI Container Registry repository.
# Convention shown: private repo, and pipelines push immutable version tags
# alongside (never instead of) a moving 'latest'.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

variable "compartment_id" {
  type        = string
  description = "OCID of the compartment"
}

resource "oci_artifacts_container_repository" "frontend" {
  compartment_id = var.compartment_id
  display_name   = "webshop/frontend"
  is_public      = false
  is_immutable   = false # set true only if every pushed tag must be immutable
}
