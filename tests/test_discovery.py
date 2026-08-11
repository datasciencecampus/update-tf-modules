import pathlib

from _pytest.monkeypatch import MonkeyPatch
import pytest

from update_tf_modules import discovery
from update_tf_modules.models import GitHubModule, RegistryModule
from update_tf_modules.discovery import (
    normalize_discovered_source,
    warn_on_unmanaged_modules,
    discover_module_sources,
    managed_source_keys,
)

@pytest.mark.parametrize("input_str,expected", [
    ("git::https://github.com/org/repo.git?ref=main", "git::https://github.com/org/repo.git?ref="),
    ("git::https://github.com/org/repo.git?ref=main&key=value", "git::https://github.com/org/repo.git?ref="),
    ("registry.terraform.io/org/module/aws", "registry.terraform.io/org/module/aws"),
    ("git::https://github.com/org/repo.git", "git::https://github.com/org/repo.git"),
])
def test_normalize_discovered_source(input_str: str, expected: str):
    assert normalize_discovered_source(input_str) == expected


def test_discover_module_sources(tmp_path: pathlib.Path, monkeypatch: MonkeyPatch):
    tf_content = '''
    module "mod1" {
      source = "git::https://github.com/org/repo.git?ref=main"
    }
    module "mod2" {
      source = "registry.terraform.io/org/module/aws"
    }
    '''
    tf_file = tmp_path / "main.tf"
    tf_file.write_text(tf_content)
    monkeypatch.setattr(discovery, "TERRAFORM_ROOT", tmp_path)
    result = discover_module_sources()
    assert "git::https://github.com/org/repo.git?ref=" in result
    assert "registry.terraform.io/org/module/aws" in result


def test_managed_source_keys():
    github_mod = GitHubModule(
        name="mod1",
        glob="*.tf",
        repo="org/repo",
        source_prefix="git::https://github.com/org/repo.git?ref=",
        type="github"
    )
    registry_mod = RegistryModule(
        name="mod2",
        glob="*.tf",
        source="registry.terraform.io/org/module/aws",
        type="registry"
    )
    result = managed_source_keys([github_mod, registry_mod])
    assert "git::https://github.com/org/repo.git?ref=" in result
    assert "registry.terraform.io/org/module/aws" in result

def test_warn_on_unmanaged_modules(monkeypatch, caplog):
    monkeypatch.setattr(discovery, "discover_module_sources", lambda: {"source1", "source2"})
    monkeypatch.setattr(discovery, "managed_source_keys", lambda _: {"source1"})
    warn_on_unmanaged_modules([])
    assert "Terraform modules were found in the repo but are not represented in the manifest:" in caplog.text
    assert "  - source2" in caplog.text