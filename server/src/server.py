import asyncio
import json
from typing import Dict, Any
from .config import HOST, CLIENT_PORT, KERNEL_PORT
from .db_manager import DatabaseManager
from .handlers import RequestFactory
from .response_codes import Codes, RESPONSE_MESSAGES

class Server:
    def __init__(self, db_file: str):
        """Initialize server with database and request factory."""
        self.db_manager = DatabaseManager(db_file)
        self.request_factory = RequestFactory(self.db_manager)
        self.client_writer = None  # Store the single client connection

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle the client connection."""
        # Store the client writer for potential updates
        self.client_writer = writer
        print(f"Client connected from {writer.get_extra_info('peername')}")

        try:
            # Send initial domain list to client
            await self._send_domain_list()

            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    request_data = json.loads(data.decode('utf-8'))
                    print(f"Received from client: {request_data}")

                    # Process request
                    response = self.request_factory.handle_request(request_data)
                    print(f"Sending response: {response}")

                    # Send response
                    writer.write(json.dumps(response).encode('utf-8') + b'\n')
                    await writer.drain()

                    # If domain list was modified, send update
                    if request_data.get('code') in [Codes.CODE_ADD_DOMAIN, Codes.CODE_REMOVE_DOMAIN]:
                        await self._send_domain_list()

                except json.JSONDecodeError:
                    print("Invalid JSON received")
                    error_response = {
                        'code': request_data.get('code', ''),
                        'message': RESPONSE_MESSAGES['invalid_request']
                    }
                    writer.write(json.dumps(error_response).encode('utf-8') + b'\n')
                    await writer.drain()

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.client_writer = None
            writer.close()
            await writer.wait_closed()
            print("Client disconnected")

    async def handle_kernel(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle kernel module connections."""
        print(f"Kernel module connected from {writer.get_extra_info('peername')}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    request_data = json.loads(data.decode('utf-8'))
                    print(f"Received from kernel: {request_data}")

                    # Process kernel request
                    response = self.handle_kernel_request(request_data)
                    print(f"Sending to kernel: {response}")

                    writer.write(json.dumps(response).encode('utf-8') + b'\n')
                    await writer.drain()

                except json.JSONDecodeError:
                    print("Invalid JSON received from kernel")

        except Exception as e:
            print(f"Error handling kernel module: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print("Kernel module disconnected")

    def handle_kernel_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process kernel module requests."""
        domain = request_data.get('domain')
        if not domain:
            return {'block': False}

        # Check if domain should be blocked
        should_block = (
            # Check manually blocked domains
            self.db_manager.is_domain_blocked(domain) or
            # Check ad blocking
            (
                self.db_manager.get_setting('ad_block') == 'on' and
                self.db_manager.is_easylist_blocked(domain)
            ) or
            # Check adult content blocking
            (
                self.db_manager.get_setting('adult_block') == 'on' and
                'adult' in request_data.get('categories', [])
            )
        )

        return {'block': should_block}

    async def _send_domain_list(self) -> None:
        """Send updated domain list to client."""
        if self.client_writer:
            domains = self.db_manager.get_blocked_domains()
            update_message = {
                'code': Codes.CODE_DOMAIN_LIST_UPDATE,
                'content': domains
            }
            try:
                self.client_writer.write(json.dumps(update_message).encode('utf-8') + b'\n')
                await self.client_writer.drain()
            except Exception as e:
                print(f"Error sending domain list update: {e}")

async def start_server(db_manager: DatabaseManager) -> None:
    """Start the server with both client and kernel handlers."""
    server = Server(db_manager.db_file)

    client_server = await asyncio.start_server(
        server.handle_client,
        HOST,
        CLIENT_PORT
    )

    kernel_server = await asyncio.start_server(
        server.handle_kernel,
        HOST,
        KERNEL_PORT
    )

    async with client_server, kernel_server:
        print(f"Client server running on {HOST}:{CLIENT_PORT}")
        print(f"Kernel server running on {HOST}:{KERNEL_PORT}")
        
        await asyncio.gather(
            client_server.serve_forever(),
            kernel_server.serve_forever()
        )

def run(db_file: str) -> None:
    """Initialize and run the server."""
    try:
        asyncio.run(start_server(DatabaseManager(db_file)))
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {str(e)}")