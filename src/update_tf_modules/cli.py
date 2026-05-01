import argparse
from pathlib import Path
from typing import Sequence

from .app import main as run_update
from .config import DEFAULT_MANIFEST_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="update-tf-modules",
        description="Update Terraform module versions from a manifest."
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to the module update manifest."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run_update(manifest_path=args.manifest_path)
        return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"[ERROR] {e}")
        return 2
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}")
        return 1
    
if __name__ == "__main__":
    raise SystemExit(main())