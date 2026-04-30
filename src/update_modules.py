"""Update Terraform module versions across the repository.

This script reads a module update manifest and updates Terraform module
references in target files. It supports two source types:

- GitHub module sources pinned by tag or resolved commit SHA.
- Terraform Registry module sources pinned by version.

The script validates manifest entries, warns about
Terraform module sources that are not managed by the manifest, fetches the
latest versions from remote APIs, and rewrites matching module references in
configured files.
"""

from pathlib import Path
import os
import re
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / ".github" / "module-update-manifest.yml"
TERRAFORM_ROOT = ROOT / "terraform"
GITHUB_API = "https://api.github.com"
TERRAFORM_REGISTRY_API = "https://registry.terraform.io/v1/modules"


def main(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
    """Run the module update workflow for all manifest entries.

    Args:
        manifest_path: Path to the YAML manifest describing managed modules.
    """
    modules = load_manifest(manifest_path)
    validate_manifest_modules(modules)
    warn_on_unmanaged_modules(modules)

    github_session = build_github_session()
    registry_session = build_registry_session()
    total_updates = 0

    for module in modules:
        if module["type"] == "github":
            total_updates += process_github_module(github_session, module)
        elif module["type"] == "registry":
            total_updates += process_registry_module(registry_session, module)

    print(f"Completed module update run. Replacements made: {total_updates}")


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


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load and validate the top-level module list from a manifest file.

    Args:
        manifest_path: Path to the YAML manifest file.

    Returns:
        A non-empty list of module definition dictionaries.

    Raises:
        ValueError: If the manifest does not contain a non-empty modules list.
    """
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}

    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ValueError("Manifest must contain a non-empty 'modules' list.")

    return modules


def resolve_targets(module: dict[str, Any]) -> list[Path]:
    """Resolve one or more target files for a module manifest entry.

    Supports one of the manifest keys: file, files or glob.

    Args:
        module: A single module definition from the manifest.

    Returns:
        A list of existing absolute target paths.

    Raises:
        ValueError: If no manifest key is provided.
        FileNotFoundError: If resolved targets do not exist or no targets match.
    """
    if "files" in module:
        targets = [ROOT / Path(file_name) for file_name in module["files"]]
    elif "file" in module:
        targets = [ROOT / Path(module["file"])]
    elif "glob" in module:
        targets = sorted(ROOT.glob(module["glob"]))
    else:
        raise ValueError(f"Module '{module['name']}' must define one of: file, files, glob.")

    missing = [str(path.relative_to(ROOT)) for path in targets if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Module '{module['name']}' targets files that do not exist: {', '.join(missing)}"
        )

    if not targets:
        raise FileNotFoundError(
            f"Module '{module['name']}' did not resolve any target files."
        )

    return targets


def semver_key(version: str) -> tuple[tuple[int, Any], ...]:
    """Build a sortable key for semantic-like version strings.

    Args:
        version: A version string, optionally prefixed with "v".

    Returns:
        A tuple key that allows mixed numeric and non-numeric comparison.
    """
    parts = re.split(r"[.+-]", version.lstrip("v"))
    key: list[tuple[int, Any]] = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part))
    return tuple(key)


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
        print(f"[ERROR] Failed to fetch latest GitHub version for '{repo}': {error}")
        return None
    except Exception as error:
        print(f"[ERROR] Unexpected error fetching GitHub version for '{repo}': {error}")
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
        print(
            f"[ERROR] Failed to fetch commit hash for tag '{tag}' in repo '{repo}': {error}"
        )
        return None
    except Exception as error:
        print(
            f"[ERROR] Unexpected error fetching commit hash for tag '{tag}' in repo '{repo}': {error}"
        )
        return None


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
        print(
            f"[ERROR] Failed to fetch latest version for registry module '{source}': {error}"
        )
        return None
    except Exception as error:
        print(
            f"[ERROR] Unexpected error fetching version for registry module '{source}': {error}"
        )
        return None


def update_github_module(
    file_path: Path,
    source_prefix: str,
    new_ref: str,
) -> int:
    """Update GitHub module ref values in a Terraform file.

    Matches source lines that begin with source_prefix and replaces the
    trailing ref segment.

    Args:
        file_path: Terraform file to update.
        source_prefix: Source prefix ending with ?ref=.
        new_ref: New ref value to set.

    Returns:
        Number of matching source entries updated.
    """
    regex = rf'(^\s*source\s*=\s*"{re.escape(source_prefix)})([^"]+)(")'
    content = file_path.read_text(encoding="utf-8")
    new_content, count = re.subn(
        regex, 
        lambda match: f"{match.group(1)}{new_ref}{match.group(3)}", 
        content, 
        flags=re.MULTILINE,
        )

    if count > 0 and new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Updated GitHub module in {file_path.relative_to(ROOT)} to {new_ref}")

    return count


def update_registry_module(
    file_path: Path,
    source: str,
    new_version: str,
) -> int:
    """Update or insert version constraints for a registry module source.

    The function scans module blocks, finds those with a matching source value,
    and either updates an existing version attribute or inserts one before the
    module block closes.

    Args:
        file_path: Terraform file to update.
        source: Exact registry source string to match.
        new_version: Version value to write.

    Returns:
        Count of module blocks where version was inserted or updated.
    """
    lines = file_path.read_text(encoding="utf-8").splitlines()

    module_start_pattern = re.compile(r'^\s*module\s+"[^"]+"\s*\{\s*$')
    source_pattern = re.compile(rf'^\s*source\s*=\s*"{re.escape(source)}"\s*$')
    version_pattern = re.compile(r'^(?P<indent>\s*)version\s*=\s*"[^"]+"\s*$')

    updated_lines: list[str] = []
    in_module = False
    brace_depth = 0
    matching_source = False
    version_updated = False
    inserted_or_updated = 0
    source_indent = "  "

    for line in lines:
        if not in_module and module_start_pattern.match(line):
            in_module = True
            brace_depth = line.count("{") - line.count("}")
            matching_source = False
            version_updated = False
            updated_lines.append(line)
            continue

        if in_module:
            if source_pattern.match(line):
                matching_source = True
                indent_match = re.match(r"^(\s*)", line)
                source_indent = indent_match.group(1) if indent_match else ""
                updated_lines.append(line)
                brace_depth += line.count("{") - line.count("}")
                continue

            version_match = version_pattern.match(line)
            if matching_source and version_match:
                indent = version_match.group("indent")
                updated_lines.append(f'{indent}version = "{new_version}"')
                version_updated = True
                inserted_or_updated += 1
                brace_depth += line.count("{") - line.count("}")
                continue

            next_depth = brace_depth + line.count("{") - line.count("}")
            if matching_source and next_depth == 0 and line.strip() == "}":
                if not version_updated:
                    updated_lines.append(f'{source_indent}version = "{new_version}"')
                    inserted_or_updated += 1
                updated_lines.append(line)
                in_module = False
                brace_depth = 0
                matching_source = False
                version_updated = False
                continue

            updated_lines.append(line)
            brace_depth = next_depth
            if brace_depth <= 0:
                in_module = False
                matching_source = False
                version_updated = False
            continue

        updated_lines.append(line)

    new_content = "\n".join(updated_lines) + "\n"
    old_content = file_path.read_text(encoding="utf-8")
    if new_content != old_content:
        file_path.write_text(new_content, encoding="utf-8")
        print(
            f"Updated registry module '{source}' in {file_path.relative_to(ROOT)} to {new_version}"
        )

    return inserted_or_updated


def normalize_discovered_source(source: str) -> str:
    """Normalize discovered module sources for manifest key comparison.

    Args:
        source: Raw source string discovered in Terraform configuration.

    Returns:
        A normalized source string. Git sources with ?ref= are reduced to their
        stable prefix ending in ?ref=.
    """
    if source.startswith("git::") and "?ref=" in source:
        return source.split("?ref=", 1)[0] + "?ref="
    return source


def discover_module_sources() -> set[str]:
    """Collect module source strings used in Terraform files.

    Returns:
        A set of normalized source strings discovered in module blocks.
    """
    discovered: set[str] = set()
    module_start_pattern = re.compile(r'^\s*module\s+"[^"]+"\s*\{\s*$')
    source_pattern = re.compile(r'^\s*source\s*=\s*"([^"]+)"\s*$')

    for file_path in TERRAFORM_ROOT.glob("**/*.tf"):
        lines = file_path.read_text(encoding="utf-8").splitlines()
        in_module = False
        brace_depth = 0

        for line in lines:
            if not in_module and module_start_pattern.match(line):
                in_module = True
                brace_depth = line.count("{") - line.count("}")
                continue

            if in_module:
                source_match = source_pattern.match(line)
                if source_match:
                    discovered.add(normalize_discovered_source(source_match.group(1)))

                brace_depth += line.count("{") - line.count("}")
                if brace_depth <= 0:
                    in_module = False
                    brace_depth = 0

    return discovered


def managed_source_keys(modules: list[dict[str, Any]]) -> set[str]:
    """Build the set of module sources managed by the manifest.

    Args:
        modules: Manifest module definitions.

    Returns:
        A set of source identifiers used for managed/unmanaged comparison.
    """
    keys: set[str] = set()
    for module in modules:
        if module["type"] == "github":
            keys.add(module["source_prefix"])
        elif module["type"] == "registry":
            keys.add(module["source"])
    return keys


def warn_on_unmanaged_modules(modules: list[dict[str, Any]]) -> None:
    """Print warnings for Terraform module sources missing from the manifest.

    Args:
        modules: Manifest module definitions.
    """
    discovered = discover_module_sources()
    managed = managed_source_keys(modules)
    unmanaged = sorted(discovered - managed)

    if unmanaged:
        print("[WARN] Terraform modules were found in the repo but are not represented in the manifest:")
        for source in unmanaged:
            print(f"  - {source}")


def process_github_module(
    github_session: requests.Session,
    module: dict[str, Any],
) -> int:
    """Resolve and apply updates for a GitHub-backed module definition.

    Args:
        github_session: GitHub API session.
        module: Manifest entry describing the GitHub module.

    Returns:
        Number of source replacements made across all target files.

    Raises:
        ValueError: If an unsupported pin strategy is configured.
    """
    lookup = module.get("lookup", "release")
    pin = module.get("pin", "sha")

    tag = get_latest_github_tag(github_session, module["repo"], lookup)
    if not tag:
        print(
            f"[SKIP] Could not update module '{module['name']}' because no GitHub tag or release could be resolved."
        )
        return 0

    if pin == "sha":
        resolved_ref = get_commit_hash_for_tag(github_session, module["repo"], tag)
        if not resolved_ref:
            print(
                f"[SKIP] Could not update module '{module['name']}' because the commit SHA for tag '{tag}' could not be resolved."
            )
            return 0
    elif pin == "tag":
        resolved_ref = tag
    else:
        raise ValueError(
            f"Module '{module['name']}' has unsupported pin strategy '{pin}'. Use 'sha' or 'tag'."
        )

    updated = 0
    for target in resolve_targets(module):
        updated += update_github_module(target, module["source_prefix"], resolved_ref)

    return updated


def process_registry_module(
    registry_session: requests.Session,
    module: dict[str, Any],
) -> int:
    """Resolve and apply updates for a Terraform Registry module definition.

    Args:
        registry_session: Terraform Registry session.
        module: Manifest entry describing the registry module.

    Returns:
        Number of version insertions or updates across target files.
    """
    version = get_latest_registry_version(registry_session, module["source"])
    if not version:
        print(
            f"[SKIP] Could not update registry module '{module['name']}' because no version could be resolved."
        )
        return 0

    updated = 0
    for target in resolve_targets(module):
        updated += update_registry_module(target, module["source"], version)

    return updated


def validate_manifest_modules(modules: list[dict[str, Any]]) -> None:
    """Validate required fields and target files for manifest module entries.

    Args:
        modules: Manifest module definitions to validate.

    Raises:
        ValueError: If entries are missing required fields or use unsupported types.
        FileNotFoundError: If any declared target paths are invalid.
    """
    for module in modules:
        if "name" not in module or "type" not in module:
            raise ValueError("Each manifest entry must define at least 'name' and 'type'.")

        if module["type"] == "github":
            required = {"repo", "source_prefix"}
        elif module["type"] == "registry":
            required = {"source"}
        else:
            raise ValueError(
                f"Module '{module['name']}' has unsupported type '{module['type']}'."
            )

        missing = [field for field in required if field not in module]
        if missing:
            raise ValueError(
                f"Module '{module['name']}' is missing required fields: {', '.join(missing)}"
            )

        resolve_targets(module)


if __name__ == "__main__":
    main()