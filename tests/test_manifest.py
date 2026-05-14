import pytest 
import pathlib

from update_tf_modules.manifest import load_manifest
from update_tf_modules.models import GitHubModule, RegistryModule

def test_load_manifest_valid(tmp_path: pathlib.Path):
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        """
modules:
  - name: test_module1
    type: github
    repo: repo_name1
    glob: some_regex1
    source_prefix: some_prefix
  - name: test_module2
    type: registry
    repo: repo_name2
    glob: some_regex2
    source: some_source
"""
    )
    modules = load_manifest(manifest)
    assert isinstance(modules, list)
    assert all(isinstance(module, (GitHubModule, RegistryModule)) for module in modules)


def test_manifest_raises_not_a_mapping(tmp_path: pathlib.Path):
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        """
- modules:
  test_module1:
    type: github
    repo: repo_name1
    glob: some_regex1
    source_prefix: some_prefix
  test_module2:
    type: registry
    repo: repo_name2
    glob: some_regex2
    source: some_source
"""
    ) 
    with pytest.raises(ValueError, match="Manifest must be a mapping"):
        load_manifest(manifest)

@pytest.mark.parametrize("manifest_content, expected_error",
    [
        ("""
modules:
  test_module1:
    type: github
    repo: repo_name1
    glob: some_regex1
    source_prefix: some_prefix
  test_module2:
    type: registry
    repo: repo_name2
    glob: some_regex2
    source: some_source
""", "Manifest must contain a non-empty 'modules' list."),
("""
modules:
""", "Manifest must contain a non-empty 'modules' list.")
])
def test_manifest_raises_non_empty_modules_list(tmp_path: pathlib.Path, manifest_content: str, expected_error: str):
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(manifest_content)
    with pytest.raises(ValueError, match=expected_error):
        load_manifest(manifest)


def test_manifest_raises_each_module_not_mapping(tmp_path: pathlib.Path):
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        """
modules:
  - test_module1
  - name: test_module2
    type: registry
    repo: repo_name2
    glob: some_regex2
    source: some_source
"""
    )
    with pytest.raises(ValueError, match="Each manifest module must be a mapping"):
        load_manifest(manifest)
