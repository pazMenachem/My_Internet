import socket
from typing import Optional, Callable
import json

PORT = 65432
HOST = '127.0.0.1'
RECEIVE_BUFFER_SIZE = 1024

class Communicator:
    def __init__(self, message_callback: Callable[[str], None]) -> None:
        """
        Initialize the communicator.
        
        Args:
            message_callback: Callback function to handle received messages.
        """
        self._host = HOST
        self._port = PORT
        self._socket: Optional[socket.socket] = None
        self._message_callback = message_callback

    def connect(self) -> None:
        """
        Establish connection to the server.
        
        Raises:
            socket.error: If connection cannot be established.
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))

    def send_message(self, message: str) -> None:
        """
        Send a json message to the server.
        
        Args:
            message_json: The message to send to the server.
            
        Raises:
            RuntimeError: If socket connection is not established.
        """
        if not self._socket:
            raise RuntimeError("Socket not set up. Call connect method first.")

        self._socket.send(message.encode('utf-8'))

    def receive_message(self) -> None:
        """Continuously receive and process messages from the socket connection.

        This method runs in a loop to receive messages from the socket. Each received
        message is decoded from UTF-8 and passed to the message callback function.

        Raises:
            RuntimeError: If socket connection is not established.
            socket.error: If there's an error receiving data from the socket.
            UnicodeDecodeError: If received data cannot be decoded as UTF-8.
        """
        if not self._socket:
            raise RuntimeError("Socket not set up. Call connect method first.")

        while message_bytes := self._socket.recv(RECEIVE_BUFFER_SIZE):
            if not message_bytes:
                break
            self._message_callback(message_bytes.decode('utf-8'))

    def close(self) -> None:
        """Close the socket connection and clean up resources."""
        if self._socket:
            self._socket.close()
        self._socket = None
