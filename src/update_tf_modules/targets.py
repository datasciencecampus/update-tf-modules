from pathlib import Path
from typing import Any

from src.update_tf_modules.config import ROOT

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
