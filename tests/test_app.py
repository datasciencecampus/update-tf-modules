import yaml
from pathlib import Path
import pytest
from pytest_mock import MockerFixture

from update_tf_modules import app
from update_tf_modules.app import main, process_github_module, process_registry_module
from update_tf_modules.models import GitHubModule, RegistryModule

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


# ---------------------------------------------------------------------------
# process_github_module – per-module output
# ---------------------------------------------------------------------------

@pytest.fixture
def github_module() -> GitHubModule:
    return GitHubModule(
        name="my-mod",
        type="github",
        repo="org/repo",
        source_prefix="git::https://github.com/org/repo.git?ref=",
        lookup="release",
        pin="tag",
        glob="*.tf",
    )


@pytest.fixture
def registry_module() -> RegistryModule:
    return RegistryModule(
        name="my-reg-mod",
        type="registry",
        source="ns/mod/aws",
        glob="*.tf",
    )


def test_process_github_module_logs_start_and_resolution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    github_module: GitHubModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: "v1.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [])

    process_github_module(mocker.MagicMock(), github_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-mod' (github): querying repo=org/repo" in out
    assert "[INFO] Module 'my-mod' (github): resolved tag v1.0.0" in out


def test_process_github_module_logs_updated_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    github_module: GitHubModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: "v1.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [mocker.MagicMock()])
    monkeypatch.setattr(app, "update_github_module", lambda f, sp, ref: 2)

    result = process_github_module(mocker.MagicMock(), github_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-mod' outcome: updated (2 replacement(s))" in out
    assert result == 2


def test_process_github_module_logs_unchanged_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    github_module: GitHubModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: "v1.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [mocker.MagicMock()])
    monkeypatch.setattr(app, "update_github_module", lambda f, sp, ref: 0)

    result = process_github_module(mocker.MagicMock(), github_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-mod' outcome: unchanged" in out
    assert result == 0


def test_process_github_module_skips_when_no_tag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    github_module: GitHubModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: None)

    result = process_github_module(mocker.MagicMock(), github_module)

    out = capsys.readouterr().out
    assert "[SKIP] Module 'my-mod': no GitHub tag or release could be resolved." in out
    assert result == 0


def test_process_github_module_skips_when_no_sha(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    module = GitHubModule(
        name="sha-mod",
        type="github",
        repo="org/repo",
        source_prefix="git::https://github.com/org/repo.git?ref=",
        pin="sha",
        glob="*.tf",
    )
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: "v1.0.0")
    monkeypatch.setattr(app, "get_commit_hash_for_tag", lambda s, r, t: None)

    result = process_github_module(mocker.MagicMock(), module)

    out = capsys.readouterr().out
    assert "[SKIP] Module 'sha-mod': commit SHA for tag 'v1.0.0' could not be resolved." in out
    assert result == 0


def test_process_github_module_sha_pin_logs_resolution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    module = GitHubModule(
        name="sha-mod",
        type="github",
        repo="org/repo",
        source_prefix="git::https://github.com/org/repo.git?ref=",
        pin="sha",
        glob="*.tf",
    )
    monkeypatch.setattr(app, "get_latest_github_tag", lambda s, r, l: "v1.0.0")
    monkeypatch.setattr(app, "get_commit_hash_for_tag", lambda s, r, t: "abc123")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [])

    process_github_module(mocker.MagicMock(), module)

    out = capsys.readouterr().out
    assert "resolved tag v1.0.0 -> SHA abc123" in out


# ---------------------------------------------------------------------------
# process_registry_module – per-module output
# ---------------------------------------------------------------------------


def test_process_registry_module_logs_start_and_resolution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    registry_module: RegistryModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_registry_version", lambda s, src: "2.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [])

    process_registry_module(mocker.MagicMock(), registry_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-reg-mod' (registry): querying source=ns/mod/aws" in out
    assert "[INFO] Module 'my-reg-mod' (registry): resolved version 2.0.0" in out


def test_process_registry_module_logs_updated_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    registry_module: RegistryModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_registry_version", lambda s, src: "2.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [mocker.MagicMock()])
    monkeypatch.setattr(app, "update_registry_module", lambda f, src, ver: 1)

    result = process_registry_module(mocker.MagicMock(), registry_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-reg-mod' outcome: updated (1 replacement(s))" in out
    assert result == 1


def test_process_registry_module_logs_unchanged_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    registry_module: RegistryModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_registry_version", lambda s, src: "2.0.0")
    monkeypatch.setattr(app, "resolve_targets", lambda m: [mocker.MagicMock()])
    monkeypatch.setattr(app, "update_registry_module", lambda f, src, ver: 0)

    result = process_registry_module(mocker.MagicMock(), registry_module)

    out = capsys.readouterr().out
    assert "[INFO] Module 'my-reg-mod' outcome: unchanged" in out
    assert result == 0


def test_process_registry_module_skips_when_no_version(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
    registry_module: RegistryModule,
) -> None:
    monkeypatch.setattr(app, "get_latest_registry_version", lambda s, src: None)

    result = process_registry_module(mocker.MagicMock(), registry_module)

    out = capsys.readouterr().out
    assert "[SKIP] Module 'my-reg-mod': no registry version could be resolved." in out
    assert result == 0