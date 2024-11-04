import os
import logging
from unittest import mock
from datetime import datetime
from typing import Optional, Callable

import pytest

from src.Application import Application
from src.View import Viewer
from src.Communicator import Communicator


@pytest.fixture
def mock_callback() -> Callable[[str], None]:
    """Fixture to provide a mock callback function."""
    return mock.Mock()


@pytest.fixture
def application(mock_callback: Callable[[str], None]) -> Application:
    """Fixture to create an Application instance."""
    with mock.patch('src.Application.Viewer') as mock_viewer, \
         mock.patch('src.Application.Communicator') as mock_comm, \
         mock.patch('src.Application.setup_logger') as mock_logger:
        app = Application()
        app._logger = mock.Mock()
        return app


def test_init(application: Application) -> None:
    """Test the initialization of Application."""
    assert hasattr(application, '_logger')
    assert hasattr(application, '_view')
    assert hasattr(application, '_communicator')


@mock.patch('src.Application.threading.Thread')
def test_start_communication(mock_thread: mock.Mock, application: Application) -> None:
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


def test_handle_request(application: Application) -> None:
    """Test request handling."""
    test_request = '{"type": "test", "content": "message"}'
    
    # Currently just testing logging as implementation is pending
    application._handle_request(test_request)
    application._logger.debug.assert_called_once_with(f"Processing request: {test_request}")


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
    