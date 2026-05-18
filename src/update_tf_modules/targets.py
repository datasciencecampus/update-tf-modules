from pathlib import Path

from .config import ROOT
from .models import BaseModule

def resolve_targets(module: BaseModule) -> list[Path]:
    """Resolve one or more target files for a module manifest entry.

    Supports one of the manifest keys: file, files or glob.

    Args:
        module: A single module definition from the manifest.

    Returns:
        A list of existing absolute target paths.

    """
    if module.files is not None:
        return [ROOT / Path(file_name) for file_name in module.files]
    elif module.file is not None:
        return [ROOT / Path(module.file)]
    return sorted(ROOT.glob(module.glob))
