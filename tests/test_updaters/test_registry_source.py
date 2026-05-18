from pathlib import Path

import pytest

from update_tf_modules.updaters.registry_source import update_registry_module

@pytest.fixture
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from update_tf_modules.updaters import registry_source
    monkeypatch.setattr(registry_source, "ROOT", tmp_path)
    return tmp_path

def test_updates_existing_version(tmp_root: Path):
    content = '''
module "testmod" {
  source = "myregistry/module"
  version = "1.0.0"
}
'''
    file = tmp_root / "file.tf"
    file.write_text(content)
    count = update_registry_module(file, "myregistry/module", "2.0.0")
    assert count == 1
    assert 'version = "2.0.0"' in file.read_text()

def test_inserts_version_if_missing(tmp_root: Path):
    content = '''
module "testmod" {
  source = "myregistry/module"
}
'''
    file = tmp_root / "file.tf"
    file.write_text(content)
    count = update_registry_module(file, "myregistry/module", "2.0.0")
    assert count == 1
    assert 'version = "2.0.0"' in file.read_text()
    text = file.read_text() 
    assert text.index('version = "2.0.0"') > text.index('source = "myregistry/module"')

def test_does_not_update_non_matching_source(tmp_root: Path):
    content = '''
module "testmod" {
  source = "other/module"
}
'''
    file = tmp_root / "file.tf"
    file.write_text(content)
    count = update_registry_module(file, "myregistry/module", "2.0.0")
    assert count == 0
    assert 'version' not in file.read_text()

def test_multiple_modules_some_matching(tmp_root: Path):
    content = '''
module "matchingmod1" {
  source = "myregistry/module"
}
module "nomatchmod" {
  source = "other/module"
  version = "0.1.0"
}
module "matchingmod2" {
  source = "myregistry/module"
  version = "1.2.3"
}
'''
    file = tmp_root / "file.tf"
    file.write_text(content)
    count = update_registry_module(file, "myregistry/module", "2.0.0")
    assert count == 2
    text = file.read_text()
    assert text.count('version = "2.0.0"') == 2
    assert 'version = "0.1.0"' in text  # Unchanged

def test_preserves_unrelated_lines(tmp_root: Path):
    content = '''
# Some comment
module "mymod" {
  source = "myregistry/module"
}
output "someoutput" {
  value = "test"
}
'''
    file = tmp_root / "file.tf"
    file.write_text(content)
    update_registry_module(file, "myregistry/module", "2.0.0")
    text = file.read_text()
    assert "# Some comment" in text
    assert 'output "someoutput"' in text
    assert 'version = "2.0.0"' in text
