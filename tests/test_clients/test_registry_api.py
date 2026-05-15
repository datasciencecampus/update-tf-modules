import pytest
from pytest_mock import MockerFixture
import requests

from update_tf_modules.clients.registry_api import (
    build_registry_session,
    get_latest_registry_version,
    semver_key,
)

def test_build_registry_session_sets_headers():
    session = build_registry_session()
    assert session.headers["User-Agent"] == "terraform-template-module-updater"


def test_get_latest_registry_version_success(mocker: MockerFixture, mock_session: requests.Session):
    mock_response = mocker.Mock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "modules": [
            {"versions": [{"version": "1.0.0"}, {"version": "2.0.0"}]}
        ]
    }
    mock_session.get.return_value = mock_response
    result = get_latest_registry_version(mock_session, "made/up/repo")
    assert result == "2.0.0"

def test_get_latest_registry_version_no_versions(mocker: MockerFixture, mock_session: requests.Session):
    mock_response = mocker.Mock()
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "modules": [
            {"versions": []}
        ]
    }
    mock_session.get.return_value = mock_response
    result = get_latest_registry_version(mock_session, "made/up/repo")
    assert result is None

def test_get_latest_registry_version_raises_http_error(mock_session: requests.Session):
    mock_session.get.side_effect = requests.HTTPError("fail")
    result = get_latest_registry_version(mock_session, "made/up/repo")
    assert result is None


@pytest.mark.parametrize(
        "version1,version2,expected", [
    ("v1.2.3", "v1.2.10", True),
    ("v1.2.3", "v1.10.3", True),
    ("v1.2.3", "v10.2.3", True),
    ("v1.2.3", "v1.2.3", False),
    ("v1.2.3", "v1.2.3-alpha", True)
])
def test_semver_key(version1: str, version2: str, expected: bool):
    assert (semver_key(version1) < semver_key(version2)) == expected
