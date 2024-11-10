import socket
import threading
import json
import asyncio
from typing import Dict, Any
from .config import HOST, CLIENT_PORT, KERNEL_PORT
from .db_manager import DatabaseManager
from .handlers import RequestFactory

class Server:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.request_factory = RequestFactory(self.db_manager)
        self.running = True

    def handle_client_thread(self) -> None:
        """Handle client connections using traditional socket."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind((HOST, CLIENT_PORT))
        client_socket.listen(1)  # Only one client needed
        print(f"Client server running on {HOST}:{CLIENT_PORT}")

        while self.running:
            try:
                conn, addr = client_socket.accept()
                print(f"Client connected from {addr}")
                
                # Send initial domain list
                domains = self.db_manager.get_blocked_domains()
                conn.send(json.dumps({
                    'type': 'domain_list',
                    'domains': domains
                }).encode() + b'\n')

                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    try:
                        request_data = json.loads(data.decode())
                        response = self.request_factory.handle_request(request_data)
                        conn.send(json.dumps(response).encode() + b'\n')
                    except json.JSONDecodeError:
                        conn.send(json.dumps({
                            'status': 'error',
                            'message': 'Invalid JSON format'
                        }).encode() + b'\n')
                    except Exception as e:
                        conn.send(json.dumps({
                            'status': 'error',
                            'message': str(e)
                        }).encode() + b'\n')

            except Exception as e:
                print(f"Client error: {e}")
            finally:
                if 'conn' in locals():
                    conn.close()

    async def handle_kernel_requests(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle kernel requests using asyncio for better performance."""
        addr = writer.get_extra_info('peername')
        print(f"Kernel module connected from {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                request_data = json.loads(data.decode())
                domain = request_data.get('domain')

                # Fast domain check
                should_block = (
                    self.db_manager.is_domain_blocked(domain) or
                    (self.db_manager.get_setting('ad_block') == 'on' and
                     self.db_manager.is_easylist_blocked(domain)) or
                    (self.db_manager.get_setting('adult_block') == 'on' and
                     'adult' in request_data.get('categories', []))
                )

                writer.write(json.dumps({'block': should_block}).encode() + b'\n')
                await writer.drain()

        except Exception as e:
            print(f"Kernel error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def start_server(self) -> None:
        """Run both client and kernel handlers."""
        try:
            # Start client handler in a separate thread
            client_thread = threading.Thread(target=self.handle_client_thread)
            client_thread.start()

            # Run kernel handler with asyncio
            async def start_kernel_server() -> None:
                kernel_server = await asyncio.start_server(
                    self.handle_kernel_requests,
                    HOST,
                    KERNEL_PORT
                )
                print(f"Kernel server running on {HOST}:{KERNEL_PORT}")
                await kernel_server.serve_forever()

            # Run the asyncio event loop for kernel handler
            asyncio.run(start_kernel_server())

        except KeyboardInterrupt:
            self.running = False
            print("\nServer stopping...")
        except Exception as e:
            print(f"Server error: {e}")

def initialize_server(db_file: str) -> None:
    """Initialize and run the server."""
    db_manager = DatabaseManager(db_file)
    server = Server(db_manager)
    server.start_server()