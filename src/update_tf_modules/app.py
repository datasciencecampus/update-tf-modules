from dataclasses import dataclass
import logging
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
from .manifest import load_manifest
from .models import GitHubModule, RegistryModule
from .targets import resolve_targets
from .updaters.github_source import update_github_module
from .updaters.registry_source import update_registry_module


logger = logging.getLogger(__name__)


@dataclass
class ModuleOutcome:
    outcome: str # "updated" | "unchanged" | "skipped"
    replacements: int = 0

def main(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
    """Run the module update workflow for all manifest entries.

    Args:
        manifest_path: Path to the YAML manifest describing managed modules.
    """
    modules = load_manifest(manifest_path)
    logger.info(f"Manifest loaded: {manifest_path} ({len(modules)} module(s))")

    logger.info("Running discovery check for unmanaged modules...")
    warn_on_unmanaged_modules(modules)

    github_session = build_github_session()
    registry_session = build_registry_session()

    outcomes: list[ModuleOutcome] = []
    logger.info(f"Processing {(n_modules := len(modules))} module(s)...")
    for module in modules:
        if isinstance(module, GitHubModule):
            outcomes.append(process_github_module(github_session, module))
        else:
            outcomes.append(process_registry_module(registry_session, module))

    total_replacements = sum(o.replacements for o in outcomes)
    n_updated = sum(1 for o in outcomes if o.outcome == "updated")
    n_unchanged = sum(1 for o in outcomes if o.outcome == "unchanged")
    n_skipped = sum(1 for o in outcomes if o.outcome == "skipped")

    logger.info(
        f"Run summary: modules={n_modules}, updated={n_updated}, "
        f"unchanged={n_unchanged}, skipped={n_skipped} "
        f"replacements={total_replacements}"
        )


def process_github_module(
    github_session: requests.Session,
    module: GitHubModule,
) -> ModuleOutcome:
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

    logger.info(f"Module '{module.name}' (github): querying repo={module.repo} lookup={lookup}")
    tag = get_latest_github_tag(github_session, module.repo, lookup)
    if not tag:
        logger.info(
            f"Module '{module.name}' outcome: skipped - no GitHub tag or release could be resolved"
        )
        return ModuleOutcome(outcome="skipped")

    if pin == "sha":
        logger.info(f"Module '{module.name}' (github): resolving SHA for tag {tag}")
        resolved_ref = get_commit_hash_for_tag(github_session, module.repo, tag)
        if not resolved_ref:
            logger.info(
                f"Module '{module.name}' outcome: skipped - commit SHA for tag '{tag}' could not be resolved"
            )
            return ModuleOutcome(outcome="skipped")
        logger.info(f"Module '{module.name}' (github): resolved tag {tag} -> SHA {resolved_ref}")
    elif pin == "tag":
        resolved_ref = tag
        logger.info(f"Module '{module.name}' (github): resolved tag {resolved_ref}")
    else:
        raise ValueError(
            f"Module '{module.name}' has unsupported pin strategy '{pin}'. Use 'sha' or 'tag'."
        )

    updated = 0
    targets = resolve_targets(module)
    if not targets: 
        logger.warning(
            f"Module '{module.name}' outcome: unchanged - no target files resolved "
            f"(check glob/file/files selector in manifest)"
        )
        return ModuleOutcome(outcome="unchanged")
    
    for target in targets:
        updated += update_github_module(target, module.source_prefix, resolved_ref)

    if updated > 0:
        logger.info(f"Module '{module.name}' outcome: updated ({updated} replacement(s))")
        return ModuleOutcome(outcome="updated", replacements=updated)
    else:
        logger.info(
            f"Module '{module.name}' outcome: unchanged - ref is already {resolved_ref} "
            f"or source_prefix does not match any entries in target file(s)"
            )
        return ModuleOutcome(outcome="unchanged")


def process_registry_module(
    registry_session: requests.Session,
    module: RegistryModule,
) -> ModuleOutcome:
    """Resolve and apply updates for a Terraform Registry module definition.

    Args:
        registry_session: Terraform Registry session.
        module: Manifest entry describing the registry module.

    Returns:
        Number of version insertions or updates across target files.
    """
    logger.info(f"Module '{module.name}' (registry): querying source={module.source}")
    version = get_latest_registry_version(registry_session, module.source)
    if not version:
        logger.info(
            f"Module '{module.name}' outcome: skipped - no registry version could be resolved"
        )
        return ModuleOutcome(outcome="skipped")

    logger.info(f"Module '{module.name}' (registry): resolved version {version}")
    updated = 0
    targets = resolve_targets(module)
    if not targets:
        logger.warning(
            f"Module '{module.name}' outcome: unchanged - no target files resolved "
            f"(check glob/file/files selector in manifest)"
        )
        return ModuleOutcome(outcome="unchanged")
    for target in targets:
        updated += update_registry_module(target, module.source, version)

    if updated > 0:
        logger.info(f"Module '{module.name}' outcome: updated ({updated} replacement(s))")
        return ModuleOutcome(outcome="updated", replacements=updated)
    else:
        logger.info(
            f"Module '{module.name}' outcome: unchanged - version is already {version} "
            f"or source does not match any entries in target file(s)"
                 )
        return ModuleOutcome(outcome="unchanged")