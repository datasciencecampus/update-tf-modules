import pytest
from pytest_mock import MockerFixture
import requests

@pytest.fixture
def mock_session(mocker: MockerFixture) -> requests.Session:
    session = requests.Session()
    mocker.patch.object(session, "get")
    return session