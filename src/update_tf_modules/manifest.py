def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load and validate the top-level module list from a manifest file.

    Args:
        manifest_path: Path to the YAML manifest file.

    Returns:
        A non-empty list of module definition dictionaries.

    Raises:
        ValueError: If the manifest does not contain a non-empty modules list.
    """
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}

    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ValueError("Manifest must contain a non-empty 'modules' list.")

    return modules


def validate_manifest_modules(modules: list[dict[str, Any]]) -> None:
    """Validate required fields and target files for manifest module entries.

    Args:
        modules: Manifest module definitions to validate.

    Raises:
        ValueError: If entries are missing required fields or use unsupported types.
        FileNotFoundError: If any declared target paths are invalid.
    """
    for module in modules:
        if "name" not in module or "type" not in module:
            raise ValueError("Each manifest entry must define at least 'name' and 'type'.")

        if module["type"] == "github":
            required = {"repo", "source_prefix"}
        elif module["type"] == "registry":
            required = {"source"}
        else:
            raise ValueError(
                f"Module '{module['name']}' has unsupported type '{module['type']}'."
            )

        missing = [field for field in required if field not in module]
        if missing:
            raise ValueError(
                f"Module '{module['name']}' is missing required fields: {', '.join(missing)}"
            )

        resolve_targets(module)

