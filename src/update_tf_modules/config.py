import os
from pathlib import Path

REPO_ROOT_ENV = "UPDATE_TF_MODULES_REPO_ROOT"
TERRAFORM_ROOT_ENV = "UPDATE_TF_MODULES_TARGET_TERRAFORM_ROOT"

# Repository root: where manifests and Terraform files are resolved from.
ROOT = Path(
	os.getenv(REPO_ROOT_ENV)
	or os.getenv("GITHUB_WORKSPACE")
	or Path.cwd()
).resolve()
DEFAULT_MANIFEST_PATH = ROOT / ".github" / "update-modules-manifest.yml"

# Terraform root: sub-path (or absolute path) where module discovery scans .tf files.
_terraform_root = Path(
	os.getenv(TERRAFORM_ROOT_ENV)
	or "terraform"
)
TERRAFORM_ROOT = (
	_terraform_root if _terraform_root.is_absolute() else ROOT / _terraform_root
).resolve()

# API endpoints
GITHUB_API = "https://api.github.com"
TERRAFORM_REGISTRY_API = "https://registry.terraform.io/v1/modules"
