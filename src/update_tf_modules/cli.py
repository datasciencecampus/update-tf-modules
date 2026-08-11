import argparse
import logging
import os
from pathlib import Path
from typing import Sequence

from .app import main as run_update
from .config import DEFAULT_MANIFEST_PATH


def configure_logging() -> None:
    """Configure process-wide logging for CLI runs."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


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
    configure_logging()
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