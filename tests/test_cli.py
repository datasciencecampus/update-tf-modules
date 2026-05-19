from pathlib import Path

import pytest

from update_tf_modules import cli
from update_tf_modules.config import DEFAULT_MANIFEST_PATH


def test_build_parser_uses_default_manifest_path() -> None:
    parser = cli.build_parser()

    args = parser.parse_args([])

    assert args.manifest_path == DEFAULT_MANIFEST_PATH


def test_main_passes_manifest_path_and_returns_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Path] = {}

    def fake_run_update(manifest_path: Path) -> None:
        captured["manifest_path"] = manifest_path

    monkeypatch.setattr(cli, "run_update", fake_run_update)

    exit_code = cli.main(["--manifest-path", "custom.yml"])

    assert exit_code == 0
    assert captured["manifest_path"] == Path("custom.yml")


def test_main_returns_two_for_expected_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_update(manifest_path: Path) -> None:
        raise FileNotFoundError("missing manifest")

    monkeypatch.setattr(cli, "run_update", fake_run_update)

    exit_code = cli.main([])

    assert exit_code == 2
    assert "[ERROR] missing manifest" in capsys.readouterr().out


def test_main_returns_one_for_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_update(manifest_path: Path) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "run_update", fake_run_update)

    exit_code = cli.main([])

    assert exit_code == 1
    assert "[ERROR] Unexpected failure: boom" in capsys.readouterr().out
