import pytest
from pytest_mock import MockerFixture
import requests

from update_tf_modules.clients import github_api

def test_build_github_session_sets_headers(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GITHUB_TOKEN", "abc123")
    session = github_api.build_github_session()
    assert session.headers["User-Agent"] == "terraform-template-module-updater"
    assert session.headers["Authorization"] == "Bearer abc123"


def test_build_github_session_no_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    session = github_api.build_github_session()
    assert "Authorization" not in session.headers


def test_get_latest_github_tag_release_success(mocker: MockerFixture, mock_session: requests.Session):
    mock_response = mocker.Mock(status_code=200)
    mock_response.json.return_value = {"tag_name": "v1.2.3"}
    mock_session.get.return_value = mock_response
    result = github_api.get_latest_github_tag(mock_session, "made/up/repo")
    assert result == "v1.2.3"

def test_get_latest_github_tag_release_404_fallback_to_tag(mocker: MockerFixture, mock_session: requests.Session):
    # First call returns 404, second returns tags
    release_resp = mocker.Mock(status_code=404)
    tag_resp = mocker.Mock(status_code=200)
    tag_resp.json.return_value = [{"name": "v2.0.0"}]
    mock_session.get.side_effect = [release_resp, tag_resp]
    result = github_api.get_latest_github_tag(mock_session, "made/up/repo")
    assert result == "v2.0.0"

def test_get_latest_github_tag_tag_empty(mocker: MockerFixture, mock_session: requests.Session):
    tag_resp = mocker.Mock(status_code=200)
    tag_resp.json.return_value = []
    mock_session.get.return_value = tag_resp
    result = github_api.get_latest_github_tag(mock_session, "made/up/repo", lookup="tag")
    assert result is None

def test_get_latest_github_tag_http_error(mock_session: requests.Session):
    mock_session.get.side_effect = requests.HTTPError("fail")
    result = github_api.get_latest_github_tag(mock_session, "made/up/repo")
    assert result is None

def test_get_commit_hash_for_tag_lightweight(mocker: MockerFixture, mock_session: requests.Session):
    resp = mocker.Mock()
    resp.raise_for_status = lambda: None
    resp.json.return_value = {"object": {"type": "commit", "sha": "abc123"}}
    mock_session.get.return_value = resp
    result = github_api.get_commit_hash_for_tag(mock_session, "made/up/repo", "v1.0.0")
    assert result == "abc123"

def test_get_commit_hash_for_tag_annotated(mocker: MockerFixture, mock_session: requests.Session):
    # First call returns type=tag, second returns the commit object
    resp1 = mocker.Mock()
    resp1.raise_for_status = lambda: None
    resp1.json.return_value = {"object": {"type": "tag", "url": "http://tag-url"}}
    resp2 = mocker.Mock()
    resp2.raise_for_status = lambda: None
    resp2.json.return_value = {"object": {"sha": "def456"}}
    mock_session.get.side_effect = [resp1, resp2]
    result = github_api.get_commit_hash_for_tag(mock_session, "made/up/repo", "v1.0.0")
    assert result == "def456"


def test_get_commit_hash_for_tag_http_error(mock_session: requests.Session):
    mock_session.get.side_effect = requests.HTTPError("fail")
    result = github_api.get_commit_hash_for_tag(mock_session, "made/up/repo", "v1.0.0")
    assert result is None
