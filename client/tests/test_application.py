import logging
from unittest import mock
from typing import Optional, Callable
import json

import pytest

from src.Application import Application
from src.View import Viewer
from src.Communicator import Communicator
from src.utils import (
    STR_CODE, STR_CONTENT,
    Codes, DEFAULT_CONFIG
)


@pytest.fixture
def mock_config_manager() -> mock.Mock:
    """Fixture to provide a mock configuration manager."""
    config_manager = mock.Mock()
    config_manager.get_config.return_value = DEFAULT_CONFIG
    return config_manager


@pytest.fixture
def application(mock_config_manager: mock.Mock) -> Application:
    """Fixture to create an Application instance."""
    with mock.patch('src.Application.Viewer') as mock_viewer, \
         mock.patch('src.Application.Communicator') as mock_comm, \
         mock.patch('src.Application.setup_logger') as mock_logger:
        app = Application()
        app._logger = mock.Mock()
        app._config_manager = mock_config_manager
        return app


def test_init(application: Application) -> None:
    """Test the initialization of Application."""
    assert hasattr(application, '_logger')
    assert hasattr(application, '_view')
    assert hasattr(application, '_communicator')
    assert hasattr(application, '_request_lock')
    assert hasattr(application, '_config_manager')


@mock.patch('src.Application.threading.Thread')
def test_start_communication(
    mock_thread: mock.Mock,
    application: Application
) -> None:
    """Test the communication startup."""
    application._start_communication()
    
    application._communicator.connect.assert_called_once()
    mock_thread.assert_called_once_with(
        target=application._communicator.receive_message,
        daemon=True
    )
    mock_thread.return_value.start.assert_called_once()


def test_start_gui(application: Application) -> None:
    """Test the GUI startup."""
    application._start_gui()
    application._view.run.assert_called_once()


def test_handle_request_ad_block(application: Application) -> None:
    """Test handling ad block request."""
    test_request = {
        STR_CODE: Codes.CODE_AD_BLOCK,
        STR_CONTENT: "test"
    }
    
    application._communicator.send_message = mock.Mock()
    
    application._handle_request(json.dumps(test_request))
    
    actual_arg = application._communicator.send_message.call_args[0][0]
    
    assert json.loads(json.loads(actual_arg)) == test_request


def test_handle_request_domain_list_update(application: Application) -> None:
    """Test handling domain list update request."""
    test_content = ["domain1.com", "domain2.com"]
    test_request = json.dumps({
        STR_CODE: Codes.CODE_DOMAIN_LIST_UPDATE,
        STR_CONTENT: test_content
    })
    
    application._handle_request(test_request)
    application._view.update_domain_list_response.assert_called_once_with(test_content)


def test_cleanup(application: Application) -> None:
    """Test cleanup process."""
    application._cleanup()
    
    application._communicator.close.assert_called_once()
    application._view.root.destroy.assert_called_once()


def test_run_success(application: Application) -> None:
    """Test successful application run."""
    with mock.patch.object(application, '_start_communication'), \
         mock.patch.object(application, '_start_gui'), \
         mock.patch.object(application, '_cleanup'):
        
        application.run()
        
        application._start_communication.assert_called_once()
        application._start_gui.assert_called_once()
        application._cleanup.assert_called_once()


def test_run_exception(application: Application) -> None:
    """Test application run with exception."""
    error_msg = "Test error"
    
    with mock.patch.object(application, '_start_communication') as mock_start_comm, \
         mock.patch.object(application, '_cleanup') as mock_cleanup:
        
        mock_start_comm.side_effect = Exception(error_msg)
        
        with pytest.raises(Exception) as exc_info:
            application.run()
        
        assert str(exc_info.value) == error_msg
        application._logger.error.assert_called_with(
            f"Error during execution: {error_msg}",
            exc_info=True
        )
        mock_cleanup.assert_called_once()


def test_handle_request_json_error(application: Application) -> None:
    """Test handling of invalid JSON in request."""
    invalid_json = "{"
    
    with pytest.raises(json.JSONDecodeError):
        application._handle_request(invalid_json)
    
    application._logger.error.assert_called()
    