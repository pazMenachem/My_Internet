import socket

PORT = 5000
ADDRESS = 'localhost'
HOST = ADDRESS

class Communicator:
    def __init__(self):
        self._host = ADDRESS
        self._port = PORT
        self._socket = None

        # self.setup()
        
    def setup(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))
            
    def send_message(self, message):
        if not self._socket:
            raise RuntimeError("Socket not set up. Call setup method first.")
        
        message_bytes = message.encode('utf-8')
        self._socket.send(message_bytes)
        
    def receive_message(self):
        if not self._socket:
            raise RuntimeError("Socket not set up. Call setup method first.")
            
        message_bytes = self._socket.recv(1024)
        return message_bytes.decode('utf-8')
    
    def close(self):
        if self._socket:
            self._socket.close()
        self._socket = None
