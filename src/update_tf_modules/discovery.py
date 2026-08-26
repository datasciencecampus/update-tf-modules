import re
import logging

from .config import TERRAFORM_ROOT
from .models import GitHubModule, Module


logger = logging.getLogger(__name__)

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


def managed_source_keys(modules: list[Module]) -> set[str]:
    """Build the set of module sources managed by the manifest.

    Args:
        modules: Manifest module definitions.

    Returns:
        A set of source identifiers used for managed/unmanaged comparison.
    """
    keys: set[str] = set()
    for module in modules:
        if isinstance(module, GitHubModule):
            keys.add(module.source_prefix)
        else:
            keys.add(module.source)
    return keys


def warn_on_unmanaged_modules(modules: list[Module]) -> None:
    """Print warnings for Terraform module sources missing from the manifest.

    Args:
        modules: Manifest module definitions.
    """
    discovered = discover_module_sources()
    managed = managed_source_keys(modules)
    unmanaged = sorted(discovered - managed)

    if unmanaged:
        logger.warning(
            "Terraform modules were found in the repo but are not represented in the manifest:"
        )
        for source in unmanaged:
            logger.warning(f"  - {source}")
