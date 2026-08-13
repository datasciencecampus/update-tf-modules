import logging
import re

import requests

from ..config import TERRAFORM_REGISTRY_API

logger = logging.getLogger(__name__)

def build_registry_session() -> requests.Session:
    """Create an HTTP session configured for Terraform Registry requests.

    Returns:
        A requests session with a User-Agent header.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "terraform-template-module-updater",
        }
    )
    return session


def get_latest_registry_version(
    session: requests.Session, source: str
) -> str | None:
    """Fetch the highest available version for a Terraform Registry module.

    Args:
        session: Terraform Registry session.
        source: Module source in namespace/name/provider form.

    Returns:
        The latest discovered version, or None when unavailable.
    """
    try:
        response = session.get(
            f"{TERRAFORM_REGISTRY_API}/{source}/versions",
            timeout=15,
        )
        response.raise_for_status()
        versions = response.json()["modules"][0]["versions"]
        version_numbers = [entry["version"] for entry in versions if "version" in entry]
        if not version_numbers:
            return None
        return max(version_numbers, key=semver_key)
    except requests.HTTPError as error:
        logger.error("Failed to fetch latest version for registry module '%s': %s", source, error)
        return None
    except Exception as error:
        logger.error("Unexpected error fetching version for registry module '%s': %s", source, error)
        return None
    

def semver_key(version: str) -> tuple[tuple[int, int | str], ...]:
    """Build a sortable key for semantic-like version strings.

    Args:
        version: A version string, optionally prefixed with "v".

    Returns:
        A tuple key that allows mixed numeric and non-numeric comparison.
    """
    parts = re.split(r"[.+-]", version.lstrip("v"))
    key: list[tuple[int, int | str]] = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part))
    return tuple(key)

