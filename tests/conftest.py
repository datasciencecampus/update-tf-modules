import pytest
import requests

@pytest.fixture
def mock_session(mocker):
    session = requests.Session()
    mocker.patch.object(session, "get")
    return session