from pathlib import Path

import requests

from .clients.github_api import (
    build_github_session,
    get_commit_hash_for_tag,
    get_latest_github_tag,
)
from .clients.registry_api import build_registry_session, get_latest_registry_version
from .config import DEFAULT_MANIFEST_PATH
from .discovery import warn_on_unmanaged_modules
from . import log
from .manifest import load_manifest
from .models import GitHubModule, RegistryModule
from .targets import resolve_targets
from .updaters.github_source import update_github_module
from .updaters.registry_source import update_registry_module

def main(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
    """Run the module update workflow for all manifest entries.

    Args:
        manifest_path: Path to the YAML manifest describing managed modules.
    """
    modules = load_manifest(manifest_path)
    log.info(f"Manifest loaded: {manifest_path} ({len(modules)} module(s))")

    log.info("Running discovery check for unmanaged modules...")
    warn_on_unmanaged_modules(modules)

    github_session = build_github_session()
    registry_session = build_registry_session()
    total_updates = 0

    log.info(f"Processing {len(modules)} module(s)...")
    for module in modules:
        if isinstance(module, GitHubModule):
            total_updates += process_github_module(github_session, module)
        else:
            total_updates += process_registry_module(registry_session, module)

    log.info(f"Completed module update run. Replacements made: {total_updates}")


def process_github_module(
    github_session: requests.Session,
    module: GitHubModule,
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
    lookup = module.lookup
    pin = module.pin

    tag = get_latest_github_tag(github_session, module.repo, lookup)
    if not tag:
        print(
            f"[SKIP] Could not update module '{module.name}' because no GitHub tag or release could be resolved."
        )
        return 0

    if pin == "sha":
        resolved_ref = get_commit_hash_for_tag(github_session, module.repo, tag)
        if not resolved_ref:
            print(
                f"[SKIP] Could not update module '{module.name}' because the commit SHA for tag '{tag}' could not be resolved."
            )
            return 0
    elif pin == "tag":
        resolved_ref = tag
    else:
        raise ValueError(
            f"Module '{module.name}' has unsupported pin strategy '{pin}'. Use 'sha' or 'tag'."
        )

    updated = 0
    for target in resolve_targets(module):
        updated += update_github_module(target, module.source_prefix, resolved_ref)

    return updated


def process_registry_module(
    registry_session: requests.Session,
    module: RegistryModule,
) -> int:
    """Resolve and apply updates for a Terraform Registry module definition.

    Args:
        registry_session: Terraform Registry session.
        module: Manifest entry describing the registry module.

    Returns:
        Number of version insertions or updates across target files.
    """
    version = get_latest_registry_version(registry_session, module.source)
    if not version:
        print(
            f"[SKIP] Could not update registry module '{module.name}' because no version could be resolved."
        )
        return 0

    updated = 0
    for target in resolve_targets(module):
        updated += update_registry_module(target, module.source, version)

    return updated