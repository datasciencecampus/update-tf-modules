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
        targets = [ROOT / Path(file_name) for file_name in module.files]
    elif module.file is not None:
        targets = [ROOT / Path(module.file)]
    elif module.glob is not None:
        targets = sorted(ROOT.glob(module.glob))
    else:
        raise ValueError(
            f"Module '{module.name}' has no target selector configured; expected one of glob/file/files."
        )

    return targets
