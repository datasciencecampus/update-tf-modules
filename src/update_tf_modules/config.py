from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / ".github" / "module-update-manifest.yml"
TERRAFORM_ROOT = ROOT / "terraform"
GITHUB_API = "https://api.github.com"
TERRAFORM_REGISTRY_API = "https://registry.terraform.io/v1/modules"
