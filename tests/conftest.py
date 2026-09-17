import pytest
from instagram_service import config

FAKE_TOKEN = "fake-token-for-tests"


@pytest.fixture
def base_url():
    """The Graph API base URL, so tests don't hardcode the version string."""
    return config.GRAPH_API_BASE_URL


@pytest.fixture
def token():
    return FAKE_TOKEN
