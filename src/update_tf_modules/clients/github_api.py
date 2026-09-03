import os
import logging

import requests

from ..config import GITHUB_API


logger = logging.getLogger(__name__)


def build_github_session() -> requests.Session:
    """Create an HTTP session configured for GitHub API requests.

    Returns:
        A requests session with default GitHub headers and optional
        authentication from GITHUB_TOKEN or GH_TOKEN.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "User-Agent": "terraform-template-module-updater",
        }
    )
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def get_latest_github_tag(
    session: requests.Session, repo: str, lookup: str = "release"
) -> str | None:
    """Get the latest GitHub version reference for a repository.

    If lookup is "release", this first tries the latest release endpoint and
    falls back to tags when no release exists.

    Args:
        session: GitHub API session.
        repo: Repository in owner/name format (e.g. "datasciencecampus/terraform-template").
        lookup: Lookup strategy, either "release" or "tag".

    Returns:
        The latest tag name, or None when it cannot be resolved.
    """
    try:
        if lookup == "release":
            response = session.get(
                f"{GITHUB_API}/repos/{repo}/releases/latest",
                timeout=15,
            )
            if response.status_code == 404:
                lookup = "tag"
            else:
                response.raise_for_status()
                return response.json().get("tag_name")

        if lookup == "tag":
            response = session.get(
                f"{GITHUB_API}/repos/{repo}/tags",
                params={"per_page": 1},
                timeout=15,
            )
            response.raise_for_status()
            tags = response.json()
            if tags:
                return tags[0].get("name")
            return None

        raise ValueError(f"Unsupported GitHub lookup strategy: {lookup}")
    except requests.HTTPError as error:
        logger.error(f"Failed to fetch latest GitHub version for '{repo}': {error}")
        return None
    except Exception as error:
        logger.exception(f"Unexpected error fetching GitHub version for '{repo}': {error}")
        return None

def get_commit_hash_for_tag(
    session: requests.Session, repo: str, tag: str
) -> str | None:
    """Resolve the commit SHA from a tag.

    Handles both lightweight and annotated tags.

    Args:
        session: GitHub API session.
        repo: Repository in owner/name format (e.g. "datasciencecampus/terraform-template").
        tag: Tag name to resolve.

    Returns:
        The resolved commit SHA, or None when it cannot be resolved.
    """
    url = f"{GITHUB_API}/repos/{repo}/git/refs/tags/{tag}"
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        obj = response.json().get("object", {})
        if obj.get("type") == "tag":
            tag_response = session.get(obj["url"], timeout=15)
            tag_response.raise_for_status()
            return tag_response.json().get("object", {}).get("sha")
        return obj.get("sha")
    except requests.HTTPError as error:
        logger.error(f"Failed to fetch commit hash for tag '{tag}' in repo '{repo}': {error}")
        return None
    except Exception as error:
        logger.exception(
            f"Unexpected error fetching commit hash for tag '{tag}' in repo '{repo}': {error}"
        )
        return None
