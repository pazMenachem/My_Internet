import socket
from typing import Optional

PORT = 65432
HOST = '127.0.0.1'

class Communicator:
    def __init__(self) -> None:
        self._host: str = HOST
        self._port: int = PORT
        self._socket: Optional[socket.socket] = None

        # self.setup()

    def setup(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))

    def send_message(self, message: str) -> None:
        if not self._socket:
            raise RuntimeError("Socket not set up. Call setup method first.")

        message_bytes = message.encode('utf-8')
        self._socket.send(message_bytes)

    def receive_message(self) -> str:
        if not self._socket:
            raise RuntimeError("Socket not set up. Call setup method first.")

        message_bytes = self._socket.recv(1024)
        return message_bytes.decode('utf-8')

    def close(self) -> None:
        if self._socket:
            self._socket.close()
        self._socket = None
