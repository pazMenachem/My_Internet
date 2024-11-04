import socket
from unittest import mock
from typing import Optional, Callable

import pytest

from src.Communicator import Communicator, HOST, PORT, RECEIVE_BUFFER_SIZE


@pytest.fixture
def mock_callback() -> Callable[[str], None]:
    """Fixture to provide a mock callback function."""
    return mock.Mock()


@pytest.fixture
def communicator(mock_callback: Callable[[str], None]) -> Communicator:
    """Fixture to create a Communicator instance."""
    return Communicator(message_callback=mock_callback)


def test_init(communicator: Communicator, mock_callback: Callable[[str], None]) -> None:
    """Test the initialization of Communicator."""
    assert communicator._host == HOST
    assert communicator._port == PORT
    assert communicator._socket is None
    assert communicator._message_callback == mock_callback


@mock.patch('socket.socket')
def test_connect(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test the connect method initializes and connects the socket."""
    mock_socket_instance = mock_socket_class.return_value
    communicator.connect()
    
    mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    mock_socket_instance.connect.assert_called_once_with((HOST, PORT))
    assert communicator._socket is mock_socket_instance


@mock.patch('socket.socket')
def test_send_message_without_setup(
    mock_socket_class: mock.Mock,
    communicator: Communicator
) -> None:
    """Test sending a message without setting up the socket raises RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        communicator.send_message("Hello")
    assert str(exc_info.value) == "Socket not set up. Call connect method first."


@mock.patch('socket.socket')
def test_send_message(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test sending a message successfully."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    message: str = "Hello, World!"
    communicator.send_message(message)

    mock_socket_instance.send.assert_called_once_with(message.encode('utf-8'))


@mock.patch('socket.socket')
def test_receive_message_without_setup(
    mock_socket_class: mock.Mock,
    communicator: Communicator
) -> None:
    """Test receiving a message without setting up the socket raises RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        communicator.receive_message()
    assert str(exc_info.value) == "Socket not set up. Call connect method first."


@mock.patch('socket.socket')
def test_receive_message(
    mock_socket_class: mock.Mock,
    communicator: Communicator,
    mock_callback: Callable[[str], None]
) -> None:
    """Test receiving a message successfully."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    # Setup mock to return a message once and then empty string to break the loop
    mock_socket_instance.recv.side_effect = [b'Hello, Client!', b'']
    
    communicator.receive_message()

    mock_socket_instance.recv.assert_called_with(RECEIVE_BUFFER_SIZE)
    mock_callback.assert_called_once_with('Hello, Client!')


@mock.patch('socket.socket')
def test_close_socket(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test closing the socket."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    communicator.close()

    mock_socket_instance.close.assert_called_once()
    assert communicator._socket is None


@mock.patch('socket.socket')
def test_receive_message_decode_error(
    mock_socket_class: mock.Mock,
    communicator: Communicator,
    mock_callback: Callable[[str], None]
) -> None:
    """Test handling of decode errors in receive_message."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    # Setup mock to return invalid UTF-8 bytes
    mock_socket_instance.recv.side_effect = [bytes([0xFF, 0xFE, 0xFD]), b'']
    
    with pytest.raises(UnicodeDecodeError):
        communicator.receive_message()

    mock_callback.assert_not_called()
