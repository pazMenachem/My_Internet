from typing import Dict, Any, Optional
import socket
import threading
import json
import asyncio
from .utils import (
    CLIENT_PORT, DEFAULT_ADDRESS, KERNEL_PORT,
    STR_AD_BLOCK, STR_ADULT_BLOCK, STR_CODE, STR_DOMAINS, STR_CONTENT,
    STR_TOGGLE_ON, STR_TOGGLE_OFF, STR_DOMAIN, STR_OPERATION, STR_SETTINGS,
    Codes, invalid_json_response
)
from .db_manager import DatabaseManager
from .handlers import RequestFactory
from .logger import setup_logger

class Server:
    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize server with database manager."""
        self.db_manager = db_manager
        self.request_factory = RequestFactory(self.db_manager)
        self.running = True
        self.logger = setup_logger(__name__)
        self.kernel_writer: Optional[asyncio.StreamWriter] = None
        self.logger.info("Server initialized")

    async def notify_kernel(self, notification: Dict[str, Any]) -> None:
        """Send notification to kernel if connected."""
        if self.kernel_writer:
            try:
                self.kernel_writer.write(json.dumps(notification).encode() + b'\n')
                await self.kernel_writer.drain()
                self.logger.debug(f"Kernel notified: {notification}")
            except Exception as e:
                self.logger.error(f"Failed to notify kernel: {e}")

    async def handle_kernel_requests(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle kernel connection and send initial settings."""
        addr = writer.get_extra_info('peername')
        self.logger.info(f"Kernel module connected from {addr}")
        self.kernel_writer = writer
        
        try:
            initial_settings = self._get_initial_settings()
            await self.notify_kernel(initial_settings)

            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"Kernel connection error: {e}")
        finally:
            self.kernel_writer = None
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"Kernel connection closed for {addr}")

    def handle_client_thread(self) -> None:
        """Handle client connections using traditional socket."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind((DEFAULT_ADDRESS, CLIENT_PORT))
        client_socket.listen(1)  
        client_socket.settimeout(1.0)  
        self.logger.info(f"Client server running on {DEFAULT_ADDRESS}:{CLIENT_PORT}")

        try:
            while self.running:
                try:
                    conn, addr = client_socket.accept()
                    self.logger.info(f"Client connected from {addr}")
                    
                    conn.settimeout(1.0)
                    
                    try:
                        # Send initial settings
                        initial_settings = self._get_initial_settings()
                        conn.send(json.dumps(initial_settings).encode() + b'\n')
                        self.logger.debug(f"Sent initial settings: {initial_settings}")

                        while True:
                            try:
                                data = conn.recv(1024)
                                if not data:
                                    break

                                try:
                                    request_data = json.loads(data.decode())
                                    self.logger.debug(f"Received request: {request_data}")
                                    response = self.request_factory.handle_request(request_data)
                                    
                                    conn.send(json.dumps(response).encode() + b'\n')
                                    self.logger.debug(f"Sent response: {response}")

                                    if response.get(STR_CODE) == Codes.CODE_SUCCESS:
                                        asyncio.run(self.notify_kernel(response))

                                except json.JSONDecodeError:
                                    self.logger.error("Invalid JSON format received")
                                    conn.send(json.dumps(invalid_json_response()).encode() + b'\n')

                            except socket.timeout:
                                if not self.running:
                                    break
                                continue
                    finally:
                        conn.close()

                except socket.timeout:
                    if not self.running:
                        break
                    continue
                except Exception as e:
                    self.logger.error(f"Client error: {e}")

        finally:
            client_socket.close()

    async def start_server(self) -> None:
        """Run both client and kernel handlers."""
        client_thread: Optional[threading.Thread] = None
        kernel_server: Optional[asyncio.Server] = None
        
        try:
            client_thread = threading.Thread(target=self.handle_client_thread)
            client_thread.start()
            self.logger.info("Client handler thread started")

            kernel_server = await asyncio.start_server(
                self.handle_kernel_requests,
                DEFAULT_ADDRESS,
                KERNEL_PORT
            )
            self.logger.info(f"Kernel server running on {DEFAULT_ADDRESS}:{KERNEL_PORT}")
            
            async with kernel_server:
                await kernel_server.serve_forever()

        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self.running = False
            # Clean up resources
            if kernel_server:
                kernel_server.close()
                await kernel_server.wait_closed()
            if client_thread and client_thread.is_alive():
                client_thread.join(timeout=1.0)

    def _get_initial_settings(self) -> Dict[str, Any]:
        """Get initial settings and domain list for initialization."""
        try:
            request_data = {STR_CODE: Codes.CODE_INIT_SETTINGS}
            return self.request_factory.handle_request(request_data)
        except Exception as e:
            self.logger.error(f"Error getting initial settings: {e}")
            return invalid_json_response()

def initialize_server(db_file: str) -> None:
    """Initialize and run the server."""
    db_manager = DatabaseManager(db_file)
    server = Server(db_manager)
    asyncio.run(server.start_server())
