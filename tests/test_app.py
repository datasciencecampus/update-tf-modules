import yaml
from pathlib import Path
import pytest

from update_tf_modules.app import main

@pytest.fixture
def manifest_data(tmp_path: Path) -> tuple[Path, list[Path], Path, list[Path]]:
    # Create a directory structure for glob
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()
    target1 = tf_dir / "target1.tf"
    target2 = tf_dir / "target2.tf"
    target1.write_text(
        'module "foo" {\n'
        '  source = "git::https://github.com/owner/repo.git?ref=old"\n'
        '}\n'
    )
    target2.write_text(
        'module "bar" {\n'
        '  source = "git::https://github.com/owner/repo.git?ref=old"\n'
        '}\n'
    )

    # Create a single file for 'file'
    single_file = tmp_path / "single.tf"
    single_file.write_text(
        'module "baz" {\n'
        '  source = "git::https://github.com/owner/repo.git?ref=old"\n'
        '}\n'
    )

    # Create multiple files for 'files'
    multi1 = tmp_path / "multi1.tf"
    multi2 = tmp_path / "multi2.tf"
    multi1.write_text(
        'module "multi1" {\n'
        '  source = "terraform-aws-modules/vpc/aws"\n'
        '}\n'
    )
    multi2.write_text(
        'module "multi2" {\n'
        '  source = "terraform-aws-modules/vpc/aws"\n'
        '}\n'
    )

    manifest: dict[str, list[dict[str, object]]] = {
        "modules": [
            {
                "name": "test_github_mod_glob",
                "type": "github",
                "repo": "owner/repo",
                "lookup": "release",
                "pin": "tag",
                "glob": "terraform/*.tf",
                "source_prefix": "git::https://github.com/owner/repo.git?ref="
            },
            {
                "name": "test_github_mod_file",
                "type": "github",
                "repo": "owner/repo",
                "lookup": "release",
                "pin": "tag",
                "file": "single.tf",
                "source_prefix": "git::https://github.com/owner/repo.git?ref="
            },
            {
                "name": "test_registry_mod_files",
                "type": "registry",
                "source": "terraform-aws-modules/vpc/aws",
                "files": ["multi1.tf", "multi2.tf"]
            }
        ]
    }
    manifest_path = tmp_path / "manifest.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)
    return manifest_path, [target1, target2], single_file, [multi1, multi2]

def test_app_integration(
    monkeypatch: pytest.MonkeyPatch,
    manifest_data: tuple[Path, list[Path], Path, list[Path]]
) -> None:
    manifest_path, glob_targets, single_file, multi_files = manifest_data

    tmp_root = manifest_path.parent
    from update_tf_modules import discovery, targets
    from update_tf_modules.updaters import github_source, registry_source
    monkeypatch.setattr(targets, "ROOT", tmp_root)
    monkeypatch.setattr(discovery, "TERRAFORM_ROOT", tmp_root / "terraform")
    monkeypatch.setattr(github_source, "ROOT", tmp_root)
    monkeypatch.setattr(registry_source, "ROOT", tmp_root)

    # Mock API calls
    monkeypatch.setattr(
        "update_tf_modules.app.get_latest_github_tag",
        lambda s, r, l: "v2.0.0"
    )
    monkeypatch.setattr(
        "update_tf_modules.app.get_commit_hash_for_tag",
        lambda s, r, t: "abc123"
    )
    monkeypatch.setattr(
        "update_tf_modules.app.get_latest_registry_version",
        lambda s, src: "3.0.0"
    )

    # Run the main workflow
    main(manifest_path=manifest_path)

    # Assert the target files were updated
    for t in glob_targets:
        assert "v2.0.0" in t.read_text() or "abc123" in t.read_text()
    assert "v2.0.0" in single_file.read_text() or "abc123" in single_file.read_text()
    for t in multi_files:
        assert "3.0.0" in t.read_text()


def test_app_lifecycle_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    manifest_data: tuple[Path, list[Path], Path, list[Path]],
) -> None:
    manifest_path, _, _, _ = manifest_data
    tmp_root = manifest_path.parent

    from update_tf_modules import discovery, targets
    from update_tf_modules.updaters import github_source, registry_source
    monkeypatch.setattr(targets, "ROOT", tmp_root)
    monkeypatch.setattr(discovery, "TERRAFORM_ROOT", tmp_root / "terraform")
    monkeypatch.setattr(github_source, "ROOT", tmp_root)
    monkeypatch.setattr(registry_source, "ROOT", tmp_root)

    monkeypatch.setattr("update_tf_modules.app.get_latest_github_tag", lambda s, r, l: "v2.0.0")
    monkeypatch.setattr("update_tf_modules.app.get_commit_hash_for_tag", lambda s, r, t: "abc123")
    monkeypatch.setattr("update_tf_modules.app.get_latest_registry_version", lambda s, src: "3.0.0")

    main(manifest_path=manifest_path)

    out = capsys.readouterr().out
    assert "[INFO] Manifest loaded:" in out
    assert "3 module(s)" in out
    assert "[INFO] Running discovery check for unmanaged modules..." in out
    assert "[INFO] Processing 3 module(s)..." in out
    assert "[INFO] Completed module update run." in out