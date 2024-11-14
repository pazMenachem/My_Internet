import socket
import pytest
from unittest import mock
from typing import Callable
import json

from src.Communicator import Communicator
from src.utils import (
    DEFAULT_CONFIG, ERR_SOCKET_NOT_SETUP,
    STR_NETWORK, STR_HOST, STR_PORT, STR_RECEIVE_BUFFER_SIZE
)

@pytest.fixture
def mock_config_manager() -> mock.Mock:
    """Fixture to provide a mock configuration manager."""
    config_manager = mock.Mock()
    config_manager.get_config.return_value = DEFAULT_CONFIG
    return config_manager

@pytest.fixture
def mock_callback() -> Callable[[str], None]:
    """Fixture to provide a mock callback function."""
    return mock.Mock()

@pytest.fixture
def communicator(
    mock_config_manager: mock.Mock,
    mock_callback: Callable[[str], None]
) -> Communicator:
    """Fixture to create a Communicator instance."""
    return Communicator(
        config_manager=mock_config_manager,
        message_callback=mock_callback
    )

def test_init(communicator: Communicator, mock_callback: Callable[[str], None]) -> None:
    """Test initialization of Communicator."""
    config = DEFAULT_CONFIG[STR_NETWORK]
    assert communicator._host == config[STR_HOST]
    assert communicator._port == int(config[STR_PORT])
    assert communicator._receive_buffer_size == int(config[STR_RECEIVE_BUFFER_SIZE])
    assert communicator._socket is None
    assert communicator._message_callback == mock_callback

@mock.patch('socket.socket')
def test_connect(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test socket connection."""
    mock_socket_instance = mock_socket_class.return_value
    communicator.connect()
    
    mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    mock_socket_instance.connect.assert_called_once_with(
        (communicator._host, communicator._port)
    )
    assert communicator._socket is mock_socket_instance

@mock.patch('socket.socket')
def test_send_message_without_setup(
    mock_socket_class: mock.Mock,
    communicator: Communicator
) -> None:
    """Test sending message without socket setup."""
    with pytest.raises(RuntimeError) as exc_info:
        communicator.send_message("test message")
    assert str(exc_info.value) == ERR_SOCKET_NOT_SETUP

@mock.patch('socket.socket')
def test_send_message(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test sending message successfully."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance
    
    message = {"test": "message"}
    communicator.send_message(message)
    
    mock_socket_instance.send.assert_called_once_with(json.dumps(message).encode('utf-8'))

@mock.patch('socket.socket')
def test_close_socket(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test closing socket connection."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance
    
    communicator.close()
    
    mock_socket_instance.close.assert_called_once()
    assert communicator._socket is None
