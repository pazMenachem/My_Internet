import os
import logging
from unittest import mock
from datetime import datetime
from typing import Optional

import pytest

from src.Controller import Controller
from src.View import Viewer
from src.Communicator import Communicator, HOST, PORT


@pytest.fixture
def controller() -> Controller:
    """Fixture to create a Controller instance."""
    with mock.patch('src.Controller.Viewer'), \
         mock.patch('src.Controller.Communicator'), \
         mock.patch('src.Controller.logging'):
        yield Controller()


@mock.patch('src.Controller.os.path.exists')
@mock.patch('src.Controller.os.makedirs')
@mock.patch('src.Controller.logging.getLogger')
@mock.patch('src.Controller.logging.basicConfig')
@mock.patch('src.Controller.datetime')
def test_logger_setup(
    mock_datetime: mock.Mock,
    mock_basicConfig: mock.Mock,
    mock_getLogger: mock.Mock,
    mock_makedirs: mock.Mock,
    mock_exists: mock.Mock,
    controller: Controller
) -> None:
    """Test the logger setup in Controller."""
    mock_exists.return_value = False
    mock_datetime.now.return_value = datetime(2023, 10, 1, 12, 0, 0)
    mock_logger = mock.Mock()
    mock_logger.info = mock.Mock()
    mock_getLogger.return_value = mock_logger

    controller._logger_setup()

    mock_exists.assert_called_once_with("client_logs")
    mock_makedirs.assert_called_once_with("client_logs")
    mock_datetime.now.assert_called_once()
    expected_log_file = os.path.join("client_logs", "Client_20231001_120000.log")
    mock_basicConfig.assert_called_once_with(
        level=mock.ANY,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            mock.ANY,
            mock.ANY,
        ],
    )
    mock_getLogger.assert_called_once_with('src.Controller')
    mock_logger.info.assert_any_call("Logger setup complete")


@mock.patch('src.Controller.Viewer')
@mock.patch('src.Controller.logging.Logger.info')
@mock.patch('src.Controller.logging.Logger.error')
def test_run_success(
    mock_error: mock.Mock,
    mock_info: mock.Mock,
    mock_viewer: mock.Mock,
    controller: Controller
) -> None:
    """Test the run method executes successfully."""
    controller._view = mock_viewer.return_value
    controller._logger = mock.Mock(spec=logging.Logger)
    
    controller.run()
    
    controller._logger.info.assert_called_with("Starting application")
    controller._view.run.assert_called_once()
    mock_error.assert_not_called()


@mock.patch('src.Controller.logging.Logger.info')
@mock.patch('src.Controller.logging.Logger.error')
def test_run_exception(
    mock_error: mock.Mock,
    mock_info: mock.Mock,
    controller: Controller
) -> None:
    """Test the run method handles exceptions properly."""
    # Setup the mock viewer instance
    mock_viewer = mock.Mock()
    mock_viewer.run.side_effect = Exception("Test Exception")
    
    controller._view = mock_viewer
    
    mock_logger = mock.Mock(spec=logging.Logger)
    controller._logger = mock_logger
    
    with pytest.raises(Exception) as exc_info:
        controller.run()
    
    assert str(exc_info.value) == "Test Exception"
    mock_logger.info.assert_called_with("Starting application")
    mock_logger.error.assert_called_with(
        "Error during execution: Test Exception",
        exc_info=True
    )
    mock_viewer.run.assert_called_once()
