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