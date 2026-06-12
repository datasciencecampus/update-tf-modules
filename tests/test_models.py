import pytest
from pydantic import ValidationError

from update_tf_modules.models import BaseModule, GitHubModule, RegistryModule

@pytest.fixture
def base_github_fields() -> dict[str, str]:
    return {
        "name": "mod",
        "type": "github",
        "repo": "repo",
        "source_prefix": "prefix",
        "glob": "*.tf"
    }

@pytest.fixture
def base_registry_fields() -> dict[str, str]:
    return {
        "name": "mod",
        "type": "registry",
        "source": "reg-source",
        "glob": "*.tf"
    }

@pytest.mark.parametrize("fields", [
    {"glob": "*.tf"},
    {"file": "main.tf"},
    {"files": ["main.tf", "vars.tf"]},
])
def tests_base_module_accepts_one_selector(fields: dict[str, str | list[str]]):
    data: dict[str, str | list[str]] = {"name": "mod", **fields}
    module = BaseModule(**data)
    assert module.name == "mod"

@pytest.mark.parametrize("fields", [
    {},
    {"glob": "*.tf", "file": "main.tf"},
    {"glob": "*.tf", "files": ["main.tf"]},
    {"file": "main.tf", "files": ["main.tf"]},
    {"glob": "*.tf", "file": "main.tf", "files": ["main.tf"]},
])
def test_base_module_rejects_invalid_selectors(fields):
    data = {"name": "mod", **fields}
    with pytest.raises(ValueError, match="must define exactly one of 'glob', 'file' or 'files'"):
        BaseModule(**data)


def test_base_module_rejects_empty_files():
    data = {"name": "mod", "files": []}
    with pytest.raises(ValueError, match="has 'files' but it is empty."):
        BaseModule(**data)

@pytest.mark.parametrize("fields", [
    {"glob": "*.tf"},
    {"file": "main.tf"},
    {"files": ["main.tf", "vars.tf"]},
])
def tests_github_module_accepts_one_selector(base_github_fields: dict[str, str], fields: dict[str, str | list[str]]):
    data: dict[str, str | list[str]] = {**base_github_fields, **fields}
    for key in ("glob", "file", "files"):
        if key not in fields and key in data:
            del data[key]
    module = GitHubModule(**data) # type: ignore
    assert module.name == "mod"

def test_github_module_requires_fields(base_github_fields: dict[str, str]):
    data = dict(base_github_fields)
    del data["repo"]
    with pytest.raises(ValidationError):
        GitHubModule(**data)

def test_registry_module_requires_fields(base_registry_fields: dict[str, str]):
    data = dict(base_registry_fields)
    del data["source"]
    with pytest.raises(ValidationError):
        RegistryModule(**data)