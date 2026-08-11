from pathlib import Path
import re

from ..config import ROOT

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
                updated_lines.append((new_line := f'{indent}version = "{new_version}"'))
                version_updated = True
                if new_line != line:
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