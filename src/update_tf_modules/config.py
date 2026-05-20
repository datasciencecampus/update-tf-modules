import os
from pathlib import Path

# Resolve paths relative to the checked-out repository.
ROOT = Path(
	os.getenv("UPDATE_TF_MODULES_ROOT")
	or os.getenv("GITHUB_WORKSPACE")
	or Path.cwd()
).resolve()
DEFAULT_MANIFEST_PATH = ROOT / ".github" / "update-modules-manifest.yml"
TERRAFORM_ROOT = ROOT / "terraform"
GITHUB_API = "https://api.github.com"
TERRAFORM_REGISTRY_API = "https://registry.terraform.io/v1/modules"
