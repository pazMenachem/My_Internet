import socket
from typing import Optional, Callable
import json
from .Logger import setup_logger

class Communicator:
    def __init__(self, config_manager, message_callback: Callable[[str], None]) -> None:
        """
        Initialize the communicator.
        
        Args:
            config_manager: Configuration manager instance
            message_callback: Callback function to handle received messages.
        """
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing Communicator")
        self.config = config_manager.get_config()
        self._message_callback = message_callback
        
        self._host = self.config["network"]["host"]
        self._port = self.config["network"]["port"]
        self._receive_buffer_size = self.config["network"]["receive_buffer_size"]
        self._socket: Optional[socket.socket] = None

    def connect(self) -> None:
        """
        Establish connection to the server.
        
        Raises:
            socket.error: If connection cannot be established.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._host, self._port))
            self.logger.info(f"Connected to server at {self._host}:{self._port}")
        except socket.error as e:
            self.logger.error(f"Failed to connect to server: {str(e)}")
            raise

    def send_message(self, message: str) -> None:
        """
        Send a json message to the server.
        
        Args:
            message_json: The message to send to the server.
            
        Raises:
            RuntimeError: If socket connection is not established.
        """
        if not self._socket:
            self.logger.error("Attempted to send message without connection")
            raise RuntimeError("Socket not set up. Call connect method first.")

        try:
            self._socket.send(message.encode('utf-8'))
            self.logger.info(f"Message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise

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
            self.logger.error("Attempted to receive message without connection")
            raise RuntimeError("Socket not set up. Call connect method first.")

        self.logger.info("Starting message receive loop")
        try:
            while message_bytes := self._socket.recv(self._receive_buffer_size):
                if not message_bytes:
                    self.logger.warning("Received empty message, breaking receive loop")
                    break
                message = message_bytes.decode('utf-8')
                self.logger.info(f"Received message: {message}")
                self._message_callback(message)
        except Exception as e:
            self.logger.error(f"Error receiving message: {str(e)}")
            raise

    def close(self) -> None:
        """Close the socket connection and clean up resources."""
        if self._socket:
            try:
                self._socket.close()
                self.logger.info("Socket connection closed")
            except Exception as e:
                self.logger.error(f"Error closing socket: {str(e)}")
            finally:
                self._socket = None
