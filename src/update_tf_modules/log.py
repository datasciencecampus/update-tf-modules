"""Temporary thin output wrapper for structured run progress messages."""


def info(message: str) -> None:
    """Emit an informational progress line."""
    print(f"[INFO] {message}")


def warn(message: str) -> None:
    """Emit a non-blocking warning line."""
    print(f"[WARN] {message}")


def skip(message: str) -> None:
    """Emit a skip notice for a module bypassed intentionally."""
    print(f"[SKIP] {message}")


def error(message: str) -> None:
    """Emit an error line for a failure that halted processing of one module."""
    print(f"[ERROR] {message}")
