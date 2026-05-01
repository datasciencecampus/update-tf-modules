from pathlib import Path
from typing import Any, cast

import yaml

from .models import Module, parse_modules

def load_manifest(manifest_path: Path) -> list[Module]:
    """Load and validate the top-level module list from a manifest file.

    Args:
        manifest_path: Path to the YAML manifest file.

    Returns:
        A non-empty list of module definition dictionaries.

    Raises:
        ValueError: If the manifest does not contain a non-empty modules list or if any module is not a mapping.
    """
    with manifest_path.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("Manifest must be a mapping")

    raw_modules = data.get("modules")
    if not isinstance(raw_modules, list) or not raw_modules:
        raise ValueError("Manifest must contain a non-empty 'modules' list.")

    if not all(isinstance(module, dict) for module in raw_modules):
        raise ValueError("Each manifest module must be a mapping")

    return parse_modules(cast(list[dict[str, object]], raw_modules))
        
