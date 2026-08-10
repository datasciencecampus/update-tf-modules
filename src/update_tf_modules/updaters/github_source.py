from pathlib import Path
import re

from ..config import ROOT

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
        source_prefix: Source prefix ending with '?ref='.
        new_ref: New ref value to set.

    Returns:
        Number of matching source entries updated.
    """
    regex = rf'(^\s*source\s*=\s*"{re.escape(source_prefix)})([^"]+)(")'
    content = file_path.read_text(encoding="utf-8")
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        current_ref = match.group(2)
        if current_ref == new_ref:
            return match.group(0)

        replacements += 1
        return f"{match.group(1)}{new_ref}{match.group(3)}"

    new_content = re.sub(regex, replace, content, flags=re.MULTILINE)

    if replacements > 0:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Updated GitHub module in {file_path.relative_to(ROOT)} to {new_ref}")

    return replacements