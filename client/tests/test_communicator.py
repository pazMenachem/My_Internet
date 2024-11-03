import socket
from unittest import mock
from typing import Optional

import pytest

from src.Communicator import Communicator, HOST, PORT


@pytest.fixture
def communicator() -> Communicator:
    """Fixture to create a Communicator instance."""
    return Communicator()


@mock.patch('socket.socket')
def test_setup(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test the setup method initializes and connects the socket."""
    mock_socket_instance = mock_socket_class.return_value
    communicator.setup()
    mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    mock_socket_instance.connect.assert_called_once_with((HOST, PORT))
    assert communicator._socket is mock_socket_instance


@mock.patch('socket.socket')
def test_send_message_without_setup(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test sending a message without setting up the socket raises RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        communicator.send_message("Hello")
    assert str(exc_info.value) == "Socket not set up. Call setup method first."


@mock.patch('socket.socket')
def test_send_message(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test sending a message successfully."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    message: str = "Hello, World!"
    communicator.send_message(message)

    mock_socket_instance.send.assert_called_once_with(message.encode('utf-8'))


@mock.patch('socket.socket')
def test_receive_message_without_setup(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test receiving a message without setting up the socket raises RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        communicator.receive_message()
    assert str(exc_info.value) == "Socket not set up. Call setup method first."


@mock.patch('socket.socket')
def test_receive_message(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test receiving a message successfully."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    mock_socket_instance.recv.return_value = b'Hello, Client!'
    message: str = communicator.receive_message()

    mock_socket_instance.recv.assert_called_once_with(1024)
    assert message == 'Hello, Client!'


@mock.patch('socket.socket')
def test_close_socket(mock_socket_class: mock.Mock, communicator: Communicator) -> None:
    """Test closing the socket."""
    mock_socket_instance = mock_socket_class.return_value
    communicator._socket = mock_socket_instance

    communicator.close()

    mock_socket_instance.close.assert_called_once()
    assert communicator._socket is None 