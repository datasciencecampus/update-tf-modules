from pathlib import Path

import pytest

from update_tf_modules.targets import resolve_targets
from update_tf_modules.models import BaseModule

@pytest.fixture
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Patch ROOT to temporary directory
    from update_tf_modules import targets
    monkeypatch.setattr(targets, "ROOT", tmp_path)
    return tmp_path

@pytest.fixture
def base_module():
    def _factory(**kwargs):
        return BaseModule(name="mod", **kwargs)
    return _factory

def test_resolve_targets_files(tmp_root: Path, base_module: BaseModule):
    path_files = [tmp_root / "file1.tf", tmp_root / "file2.tf"]
    for f in path_files:
        f.write_text("test")
    str_files = [str(p) for p in path_files]
    result = resolve_targets(base_module(files=str_files))
    assert set(result) == set(path_files)

def test_resolve_targets_file(tmp_root: Path, base_module: BaseModule):
    file = tmp_root / "file1.tf"
    file.write_text("test")
    result = resolve_targets(base_module(file=str(file)))
    assert result == [file]

def test_resolve_targets_glob(tmp_root: Path, base_module: BaseModule):
    files = [tmp_root / f"file{i}.tf" for i in range(3)]
    for f in files:
        f.write_text("test")
    result = resolve_targets(base_module(glob="*.tf"))
    assert set(result) == set(sorted(files))
