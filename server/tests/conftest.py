import pytest
from unittest import mock
from typing import Generator
from My_Internet.server.src.db_manager import DatabaseManager
from My_Internet.server.src.handlers import RequestFactory

@pytest.fixture(scope="function")
def mock_db_manager() -> mock.Mock:
    """Fixture to provide a mock database manager."""
    mock_db = mock.Mock(spec=DatabaseManager)
    
    # Setup default returns for common methods
    mock_db.is_domain_blocked.return_value = False
    mock_db.is_easylist_blocked.return_value = False
    
    return mock_db

@pytest.fixture
def mock_requests() -> Generator[mock.Mock, None, None]:
    """Fixture to mock requests library."""
    with mock.patch('My_Internet.server.src.handlers.requests') as mock_req:
        # Create a mock response
        mock_response = mock.Mock()
        mock_response.text = "test.com\n!comment\nexample.com"
        mock_req.get.return_value = mock_response
        
        # Reset the mock to clear any previous calls
        mock_req.reset_mock()
        yield mock_req

@pytest.fixture(scope="function")
def request_factory(mock_db_manager: mock.Mock) -> RequestFactory:
    """Fixture to create a RequestFactory instance."""
    return RequestFactory(mock_db_manager)

@pytest.fixture(scope="session")
def sample_domains() -> list[str]:
    """Fixture to provide test domains."""
    return [
        "example.com",
        "test.com",
        "sample.org"
    ]

@pytest.fixture(scope="session")
def sample_requests() -> dict:
    """Fixture to provide sample request data."""
    return {
        "adult_block": {
            "type": "adult_content_block",
            "action": "enable"
        },
        "domain_block": {
            "type": "domain_block",
            "action": "block",
            "domain": "example.com"
        },
        "ad_block": {
            "type": "ad_block",
            "domain": "test.com"
        }
    }