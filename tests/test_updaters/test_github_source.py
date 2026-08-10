from pathlib import Path

import pytest

from update_tf_modules.updaters.github_source import update_github_module


@pytest.fixture
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from update_tf_modules.updaters import github_source
    monkeypatch.setattr(github_source, "ROOT", tmp_path)
    return tmp_path

@pytest.mark.parametrize(
    "original,source_prefix,new_ref,expected,expected_count",
    [
        (
            'source = "git::https://github.com/org/repo.git?ref=oldref"\n',
            'git::https://github.com/org/repo.git?ref=',
            'newref',
            'source = "git::https://github.com/org/repo.git?ref=newref"\n',
            1,
        ),
        (
            # No match
            'source = "git::https://github.com/org/repo.git?ref=main"\n',
            'git::https://github.com/org/other.git?ref=',
            'newref',
            'source = "git::https://github.com/org/repo.git?ref=main"\n',
            0,
        ),
        (
            # Multiple matches
            (
                'source = "git::https://github.com/org/repo.git?ref=old1"\n'
                'source = "git::https://github.com/org/repo.git?ref=old2"\n'
            ),
            'git::https://github.com/org/repo.git?ref=',
            'newref',
            (
                'source = "git::https://github.com/org/repo.git?ref=newref"\n'
                'source = "git::https://github.com/org/repo.git?ref=newref"\n'
            ),
            2,
        ), # Already latest ref
                (
            'source = "git::https://github.com/org/repo.git?ref=newref"\n',
            'git::https://github.com/org/repo.git?ref=',
            'newref',
            'source = "git::https://github.com/org/repo.git?ref=newref"\n',
            0,
        ),
    ]
)
def test_update_github_module(tmp_root: Path, original: str, source_prefix: str, new_ref: str, expected: str, expected_count: int):
    file = tmp_root / "main.tf"
    file.write_text(original, encoding="utf-8")
    count = update_github_module(file, source_prefix, new_ref)
    assert count == expected_count
    assert file.read_text(encoding="utf-8") == expected