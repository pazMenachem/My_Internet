import json
import pytest
from unittest import mock
from typing import Dict, Any

from src.Application import Application
from src.utils import (
    STR_CODE, STR_CONTENT, STR_OPERATION, STR_DOMAINS,
    Codes, DEFAULT_CONFIG
)

@pytest.fixture
def mock_config_manager() -> mock.Mock:
    """Fixture to provide a mock configuration manager."""
    config_manager = mock.Mock()
    config_manager.get_config.return_value = DEFAULT_CONFIG.copy()
    return config_manager

@pytest.fixture
def application(mock_config_manager: mock.Mock) -> Application:
    """Fixture to create an Application instance with mocked components."""
    with mock.patch('src.Application.Viewer') as mock_viewer, \
         mock.patch('src.Application.Communicator') as mock_comm, \
         mock.patch('src.Application.setup_logger'):
        app = Application()
        app._logger = mock.Mock()
        app._config_manager = mock_config_manager
        return app

def test_init(application: Application) -> None:
    """Test the initialization of Application."""
    assert hasattr(application, '_logger')
    assert hasattr(application, '_communicator')
    assert hasattr(application, '_config_manager')

def test_handle_request_ad_block(application: Application) -> None:
    """Test handling ad block request."""
    test_request = {
        STR_CODE: Codes.CODE_AD_BLOCK,
        STR_CONTENT: "on",
    }
    
    application._communicator.send_message = mock.Mock()
    application._handle_request(json.dumps(test_request))
    
    application._communicator.send_message.assert_called_once()
    sent_data = application._communicator.send_message.call_args[0][0]
    assert sent_data == test_request

def test_handle_request_domain_list_update(application: Application) -> None:
    """Test handling domain list update request."""
    test_domains = ["domain1.com", "domain2.com"]
    test_request = {
        STR_CODE: Codes.CODE_SUCCESS,
        STR_DOMAINS: test_domains,
        STR_OPERATION: Codes.CODE_DOMAIN_LIST_UPDATE
    }
    
    application._handle_request(json.dumps(test_request), to_server=False)
    application._view.update_domain_list_response.assert_called_once_with(test_domains)

def test_cleanup(application: Application) -> None:
    """Test cleanup process."""
    application._cleanup()
    application._communicator.close.assert_called_once()

def test_handle_request_invalid_json(application: Application) -> None:
    """Test handling invalid JSON in request."""
    invalid_json = "{"
    
    with pytest.raises(json.JSONDecodeError):
        application._handle_request(invalid_json)
    
    application._logger.error.assert_called()
    