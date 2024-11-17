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
        self.logger.info("Server initialized")

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

    async def handle_kernel_requests(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle kernel requests using asyncio for better performance."""
        addr = writer.get_extra_info('peername')
        self.logger.info(f"Kernel module connected from {addr}")
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                request_data = json.loads(data.decode())
                domain = request_data.get(STR_DOMAIN, '').strip()
                
                if not domain:
                    continue

                ad_block_enabled = self.db_manager.get_setting(STR_AD_BLOCK) == STR_TOGGLE_ON
                adult_block_enabled = self.db_manager.get_setting(STR_ADULT_BLOCK) == STR_TOGGLE_ON

                block_reason = None
                should_block = False
                
                if self.db_manager.is_domain_blocked(domain):
                    should_block = True
                    block_reason = "custom_blocklist"
                    self.logger.info(f"Domain {domain} blocked (custom blocklist)")
                
                elif ad_block_enabled and request_data.get('is_ad', False):
                    should_block = True
                    block_reason = "ads"
                    self.logger.info(f"Domain {domain} blocked (ads)")
                
                elif adult_block_enabled and 'adult' in request_data.get('categories', []):
                    should_block = True
                    block_reason = "adult_content"
                    self.logger.info(f"Domain {domain} blocked (adult content)")

                response = {
                    'block': should_block,
                    'reason': block_reason or 'allowed',
                    'domain': domain
                }
                
                self.logger.debug(f"Domain check result: {domain} -> {'blocked' if should_block else 'allowed'} ({block_reason or 'no reason'})")
                
                writer.write(json.dumps(response).encode() + b'\n')
                await writer.drain()

        except Exception as e:
            self.logger.error(f"Kernel error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"Kernel connection closed for {addr}")

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
        """Get initial settings and domain list for client initialization."""
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
